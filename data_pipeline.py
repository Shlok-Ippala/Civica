"""
Fetches real Canadian housing and demographic data from StatsCan APIs.
Caches results to data/city_profiles.json.

Data sources (all free, no auth):
- Table 34-10-0127-01: CMHC vacancy rates by CMA
- Table 34-10-0133-01: CMHC average rents by CMA
- Table 34-10-0156-01: CMHC housing starts by CMA
- Table 14-10-0380-01: LFS unemployment rate by CMA
- Table 17-10-0135-01: Population estimates by CMA
- Table 11-10-0239-01: Income by age group by CMA

Usage:
    python data_pipeline.py             # fetch and cache (or load from cache)
    python data_pipeline.py --refresh   # force re-fetch from API
"""

import json
import os
import sys
import io
import zipfile
import requests
import pandas as pd
import stats_can as sc

os.makedirs("data", exist_ok=True)

CACHE_PATH = "data/city_profiles.json"

# Maps our city names -> StatsCan GEO strings per table type
# Different tables use slightly different GEO formats
GEO_MAP_STANDARD = {
    "Toronto": "Toronto, Ontario",
    "Vancouver": "Vancouver, British Columbia",
    "Montreal": "Montréal, Quebec",
    "Calgary": "Calgary, Alberta",
    "Edmonton": "Edmonton, Alberta",
    "Ottawa": "Ottawa-Gatineau, Ontario part, Ontario",
    "Winnipeg": "Winnipeg, Manitoba",
    "Hamilton": "Hamilton, Ontario",
    "Kitchener": "Kitchener-Cambridge-Waterloo, Ontario",
    "Halifax": "Halifax, Nova Scotia",
    "Victoria": "Victoria, British Columbia",
    "Saskatoon": "Saskatoon, Saskatchewan",
    "Regina": "Regina, Saskatchewan",
    "Kelowna": "Kelowna, British Columbia",
    "Sudbury": "Greater Sudbury, Ontario",
}

# For vacancy/rents, Ottawa uses a different format
GEO_MAP_CMHC = {
    **GEO_MAP_STANDARD,
    "Ottawa": "Ottawa-Gatineau, Ontario/Quebec",
}

# For population table, GEO uses "(CMA)" format
GEO_MAP_POP = {
    "Toronto": "Toronto (CMA), Ontario",
    "Vancouver": "Vancouver (CMA), British Columbia",
    "Montreal": "Montréal (CMA), Quebec",
    "Calgary": "Calgary (CMA), Alberta",
    "Edmonton": "Edmonton (CMA), Alberta",
    "Ottawa": "Ottawa - Gatineau (CMA), Ontario part, Ontario",
    "Winnipeg": "Winnipeg (CMA), Manitoba",
    "Hamilton": "Hamilton (CMA), Ontario",
    "Kitchener": "Kitchener - Cambridge - Waterloo (CMA), Ontario",
    "Halifax": "Halifax (CMA), Nova Scotia",
    "Victoria": "Victoria (CMA), British Columbia",
    "Saskatoon": "Saskatoon (CMA), Saskatchewan",
    "Regina": "Regina (CMA), Saskatchewan",
    "Kelowna": "Kelowna (CMA), British Columbia",
    "Sudbury": "Greater Sudbury (CMA), Ontario",
}

# Cities without CMA data — use hardcoded fallbacks
FALLBACK_PROFILES = {
    "Northern Ontario": {
        "avg_rent_1br": 900, "avg_rent_2br": 1100, "vacancy_rate": 5.5,
        "median_household_income": 58000, "unemployment_rate": 7.5,
        "population": 146000, "population_growth_rate": -0.3,
        "housing_starts_annual": 400, "source": "estimated",
        "income_by_age": {"18-24": 12000, "25-34": 38000, "35-49": 48000, "50-64": 45000, "65+": 30000},
    },
    "Northern BC": {
        "avg_rent_1br": 1100, "avg_rent_2br": 1400, "vacancy_rate": 4.8,
        "median_household_income": 72000, "unemployment_rate": 6.0,
        "population": 85000, "population_growth_rate": 0.2,
        "housing_starts_annual": 600, "source": "estimated",
        "income_by_age": {"18-24": 14000, "25-34": 45000, "35-49": 55000, "50-64": 52000, "65+": 32000},
    },
    "PEI": {
        "avg_rent_1br": 1300, "avg_rent_2br": 1600, "vacancy_rate": 0.8,
        "median_household_income": 62000, "unemployment_rate": 8.2,
        "population": 170000, "population_growth_rate": 3.5,
        "housing_starts_annual": 800, "source": "estimated",
        "income_by_age": {"18-24": 11000, "25-34": 36000, "35-49": 46000, "50-64": 42000, "65+": 28000},
    },
    "Indigenous Reserve Northern Ontario": {
        "avg_rent_1br": 600, "avg_rent_2br": 800, "vacancy_rate": 0.2,
        "median_household_income": 32000, "unemployment_rate": 18.0,
        "population": 25000, "population_growth_rate": 1.8,
        "housing_starts_annual": 80, "source": "estimated",
        "income_by_age": {"18-24": 6000, "25-34": 22000, "35-49": 28000, "50-64": 26000, "65+": 20000},
    },
    "Nunavut": {
        "avg_rent_1br": 2200, "avg_rent_2br": 2800, "vacancy_rate": 0.1,
        "median_household_income": 48000, "unemployment_rate": 14.0,
        "population": 40000, "population_growth_rate": 1.2,
        "housing_starts_annual": 120, "source": "estimated",
        "income_by_age": {"18-24": 10000, "25-34": 35000, "35-49": 45000, "50-64": 42000, "65+": 28000},
    },
}

# StatsCan age groups -> our age brackets
AGE_MAP = {
    "18-24": "15 to 24 years",
    "25-34": "25 to 34 years",
    "35-49": "35 to 44 years",  # closest match
    "50-64": "55 to 64 years",  # closest match
    "65+": "65 years and over",
}


def _download_csv(table_id_compact):
    """Download a StatsCan table as CSV (for tables that fail with stats_can library)."""
    url = f"https://www150.statcan.gc.ca/n1/tbl/csv/{table_id_compact}-eng.zip"
    print(f"  Downloading {table_id_compact} from StatsCan...", flush=True)
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    csv_name = [n for n in z.namelist() if n.endswith(".csv") and not n.startswith("metadata")][0]
    return pd.read_csv(z.open(csv_name), low_memory=False)


def _download_zip_table(table_id):
    """Download a StatsCan table using stats_can library."""
    print(f"  Downloading {table_id} via stats_can...", flush=True)
    return sc.zip_table_to_dataframe(table_id)


def _latest_value(df, geo_str, filters=None):
    """Get the latest VALUE for a GEO string with optional column filters."""
    mask = df["GEO"] == geo_str
    if filters:
        for col, val in filters.items():
            mask = mask & (df[col] == val)
    subset = df[mask].dropna(subset=["VALUE"])
    if subset.empty:
        return None
    latest = subset.sort_values("REF_DATE", ascending=False).iloc[0]
    return float(latest["VALUE"])


def _growth_rate(df, geo_str, filters=None):
    """Calculate year-over-year growth rate from latest two periods."""
    mask = df["GEO"] == geo_str
    if filters:
        for col, val in filters.items():
            mask = mask & (df[col] == val)
    subset = df[mask].dropna(subset=["VALUE"]).sort_values("REF_DATE", ascending=False)
    if len(subset) < 2:
        return None
    latest = float(subset.iloc[0]["VALUE"])
    previous = float(subset.iloc[1]["VALUE"])
    if previous == 0:
        return None
    return round((latest - previous) / previous * 100, 2)


def fetch_from_statscan():
    """Fetch all data from StatsCan APIs and return city profiles dict."""
    print("Fetching data from Statistics Canada...", flush=True)
    profiles = {}

    # 1. Vacancy rates (stats_can library works)
    try:
        vacancy_df = _download_zip_table("34-10-0127-01")
    except Exception as e:
        print(f"  [WARN] Vacancy table failed: {e}")
        vacancy_df = None

    # 2. Average rents (stats_can library works)
    try:
        rents_df = _download_zip_table("34-10-0133-01")
    except Exception as e:
        print(f"  [WARN] Rents table failed: {e}")
        rents_df = None

    # 3. Housing starts (direct CSV — large table times out with library)
    try:
        starts_df = _download_csv("34100156")
    except Exception as e:
        print(f"  [WARN] Housing starts table failed: {e}")
        starts_df = None

    # 4. Unemployment (direct CSV — library metadata validation fails)
    try:
        unemp_df = _download_csv("14100380")
    except Exception as e:
        print(f"  [WARN] Unemployment table failed: {e}")
        unemp_df = None

    # 5. Population (direct CSV — library metadata validation fails)
    try:
        pop_df = _download_csv("17100135")
    except Exception as e:
        print(f"  [WARN] Population table failed: {e}")
        pop_df = None

    # 6. Income by age (stats_can library works)
    try:
        income_df = _download_zip_table("11-10-0239-01")
    except Exception as e:
        print(f"  [WARN] Income table failed: {e}")
        income_df = None

    # Build profiles for CMA cities
    for city, geo_cmhc in GEO_MAP_CMHC.items():
        geo_std = GEO_MAP_STANDARD[city]
        geo_pop = GEO_MAP_POP[city]

        profile = {"source": "statscan_api"}

        # Vacancy rate
        if vacancy_df is not None:
            profile["vacancy_rate"] = _latest_value(vacancy_df, geo_cmhc)

        # Rents (apartment structures of six units and over)
        if rents_df is not None:
            rent_filters = {"Type of structure": "Apartment structures of six units and over"}
            profile["avg_rent_1br"] = _latest_value(
                rents_df, geo_cmhc, {**rent_filters, "Type of unit": "One bedroom units"}
            )
            profile["avg_rent_2br"] = _latest_value(
                rents_df, geo_cmhc, {**rent_filters, "Type of unit": "Two bedroom units"}
            )

        # Housing starts (seasonally adjusted annual rate, total units, latest month * 1000)
        if starts_df is not None:
            geo_starts = geo_std
            # Ottawa uses different format in this table
            if city == "Ottawa":
                geo_starts = "Ottawa-Gatineau, Ontario part, Ontario"
            val = _latest_value(starts_df, geo_starts, {"Type of unit": "Total units"})
            if val is not None:
                # Values are in thousands (SAAR), multiply by 1000 for actual annual rate
                profile["housing_starts_annual"] = round(val * 1000)

        # Unemployment rate
        if unemp_df is not None:
            profile["unemployment_rate"] = _latest_value(unemp_df, geo_std, {
                "Labour force characteristics": "Unemployment rate",
                "Statistics": "Estimate",
                "Data type": "Seasonally adjusted",
            })

        # Population
        if pop_df is not None:
            profile["population"] = _latest_value(pop_df, geo_pop, {
                "Sex": "Both sexes",
                "Age group": "All ages",
            })
            profile["population_growth_rate"] = _growth_rate(pop_df, geo_pop, {
                "Sex": "Both sexes",
                "Age group": "All ages",
            })

        # Income by age
        if income_df is not None:
            income_by_age = {}
            for our_age, statscan_age in AGE_MAP.items():
                val = _latest_value(income_df, geo_std, {
                    "Age group": statscan_age,
                    "Sex": "Both sexes",
                    "Income source": "Total income",
                    "Statistics": "Median income (excluding zeros)",
                })
                if val is not None:
                    income_by_age[our_age] = val
            if income_by_age:
                profile["income_by_age"] = income_by_age

            # Overall median household income (15+)
            profile["median_household_income"] = _latest_value(income_df, geo_std, {
                "Age group": "15 years and over",
                "Sex": "Both sexes",
                "Income source": "Total income",
                "Statistics": "Median income (excluding zeros)",
            })

        # Computed fields
        rent = profile.get("avg_rent_1br")
        income = profile.get("median_household_income")
        if rent and income and income > 0:
            profile["shelter_cost_to_income_ratio"] = round((rent * 12) / income, 3)

        profiles[city] = profile

    # Add fallback cities (no CMA data)
    for city, fallback in FALLBACK_PROFILES.items():
        profiles[city] = fallback

    return profiles


def load_city_profiles(force_refresh=False):
    """Load city profiles from cache, or fetch from API if not cached."""
    if not force_refresh and os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            profiles = json.load(f)
        print(f"Loaded {len(profiles)} city profiles from cache")
        return profiles

    profiles = fetch_from_statscan()

    with open(CACHE_PATH, "w") as f:
        json.dump(profiles, f, indent=2)
    print(f"Saved {len(profiles)} city profiles to {CACHE_PATH}")

    return profiles


if __name__ == "__main__":
    force = "--refresh" in sys.argv
    profiles = load_city_profiles(force_refresh=force)
    print(f"\nLoaded {len(profiles)} city profiles")
    for city, data in profiles.items():
        rent = data.get("avg_rent_1br", "?")
        vacancy = data.get("vacancy_rate", "?")
        unemp = data.get("unemployment_rate", "?")
        pop = data.get("population", "?")
        src = data.get("source", "?")
        print(f"  {city}: rent=${rent}, vacancy={vacancy}%, unemp={unemp}%, pop={pop} [{src}]")
