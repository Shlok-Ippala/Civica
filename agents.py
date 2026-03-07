AGENTS = [
    # === TORONTO (5 agents, weight 0.18) — 48% renter rate ===
    {"id": 1, "city": "Toronto", "province": "ON", "age_bracket": "18-24", "income_bracket": "very_low", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "student", "immigration_status": "born_here", "population_weight": 0.18},
    {"id": 2, "city": "Toronto", "province": "ON", "age_bracket": "25-34", "income_bracket": "high", "tenure": "renter", "debt_load": "high", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.18},
    {"id": 3, "city": "Toronto", "province": "ON", "age_bracket": "35-49", "income_bracket": "very_high", "tenure": "owner", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "established_immigrant", "population_weight": 0.18},
    {"id": 4, "city": "Toronto", "province": "ON", "age_bracket": "50-64", "income_bracket": "high", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "self_employed", "immigration_status": "born_here", "population_weight": 0.18},
    {"id": 5, "city": "Toronto", "province": "ON", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "medium", "family_size": "small_family", "employment_type": "gig", "immigration_status": "recent_immigrant", "population_weight": 0.18},

    # === MONTREAL (5 agents, weight 0.16) — 63% renter rate ===
    {"id": 6, "city": "Montreal", "province": "QC", "age_bracket": "18-24", "income_bracket": "very_low", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "student", "immigration_status": "born_here", "population_weight": 0.16},
    {"id": 7, "city": "Montreal", "province": "QC", "age_bracket": "25-34", "income_bracket": "medium", "tenure": "renter", "debt_load": "medium", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.16},
    {"id": 8, "city": "Montreal", "province": "QC", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "renter", "debt_load": "high", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "recent_immigrant", "population_weight": 0.16},
    {"id": 9, "city": "Montreal", "province": "QC", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.16},
    {"id": 10, "city": "Montreal", "province": "QC", "age_bracket": "65+", "income_bracket": "low", "tenure": "owner", "debt_load": "none", "family_size": "couple", "employment_type": "retired", "immigration_status": "born_here", "population_weight": 0.16},

    # === VANCOUVER (4 agents, weight 0.13) — 54% renter rate ===
    {"id": 11, "city": "Vancouver", "province": "BC", "age_bracket": "25-34", "income_bracket": "high", "tenure": "renter", "debt_load": "high", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.13},
    {"id": 12, "city": "Vancouver", "province": "BC", "age_bracket": "35-49", "income_bracket": "very_high", "tenure": "owner", "debt_load": "high", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "established_immigrant", "population_weight": 0.13},
    {"id": 13, "city": "Vancouver", "province": "BC", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "renter", "debt_load": "medium", "family_size": "single", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.13},
    {"id": 14, "city": "Vancouver", "province": "BC", "age_bracket": "65+", "income_bracket": "low", "tenure": "owner", "debt_load": "none", "family_size": "couple", "employment_type": "retired", "immigration_status": "established_immigrant", "population_weight": 0.13},

    # === CALGARY (3 agents, weight 0.10) — 31% renter rate ===
    {"id": 15, "city": "Calgary", "province": "AB", "age_bracket": "25-34", "income_bracket": "high", "tenure": "renter", "debt_load": "medium", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.10},
    {"id": 16, "city": "Calgary", "province": "AB", "age_bracket": "35-49", "income_bracket": "very_high", "tenure": "owner", "debt_load": "medium", "family_size": "large_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.10},
    {"id": 17, "city": "Calgary", "province": "AB", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "self_employed", "immigration_status": "established_immigrant", "population_weight": 0.10},

    # === EDMONTON (3 agents, weight 0.09) ===
    {"id": 18, "city": "Edmonton", "province": "AB", "age_bracket": "25-34", "income_bracket": "medium", "tenure": "renter", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "recent_immigrant", "population_weight": 0.09},
    {"id": 19, "city": "Edmonton", "province": "AB", "age_bracket": "35-49", "income_bracket": "high", "tenure": "owner", "debt_load": "medium", "family_size": "large_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.09},
    {"id": 20, "city": "Edmonton", "province": "AB", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.09},

    # === OTTAWA (2 agents, weight 0.07) ===
    {"id": 21, "city": "Ottawa", "province": "ON", "age_bracket": "35-49", "income_bracket": "high", "tenure": "owner", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.07},
    {"id": 22, "city": "Ottawa", "province": "ON", "age_bracket": "25-34", "income_bracket": "medium", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.07},

    # === WINNIPEG (2 agents, weight 0.05) ===
    {"id": 23, "city": "Winnipeg", "province": "MB", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "owner", "debt_load": "medium", "family_size": "large_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.05},
    {"id": 24, "city": "Winnipeg", "province": "MB", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "refugee", "population_weight": 0.05},

    # === HAMILTON (2 agents, weight 0.04) ===
    {"id": 25, "city": "Hamilton", "province": "ON", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.04},
    {"id": 26, "city": "Hamilton", "province": "ON", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "gig", "immigration_status": "born_here", "population_weight": 0.04},

    # === KITCHENER-WATERLOO (2 agents, weight 0.04) ===
    {"id": 27, "city": "Kitchener-Waterloo", "province": "ON", "age_bracket": "25-34", "income_bracket": "high", "tenure": "owner", "debt_load": "high", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.04},
    {"id": 28, "city": "Kitchener-Waterloo", "province": "ON", "age_bracket": "18-24", "income_bracket": "very_low", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "student", "immigration_status": "recent_immigrant", "population_weight": 0.04},

    # === HALIFAX (2 agents, weight 0.03) ===
    {"id": 29, "city": "Halifax", "province": "NS", "age_bracket": "65+", "income_bracket": "low", "tenure": "owner", "debt_load": "none", "family_size": "couple", "employment_type": "retired", "immigration_status": "born_here", "population_weight": 0.03},
    {"id": 30, "city": "Halifax", "province": "NS", "age_bracket": "25-34", "income_bracket": "medium", "tenure": "renter", "debt_load": "high", "family_size": "single", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.03},

    # === VICTORIA (2 agents, weight 0.03) ===
    {"id": 31, "city": "Victoria", "province": "BC", "age_bracket": "65+", "income_bracket": "medium", "tenure": "owner", "debt_load": "none", "family_size": "single", "employment_type": "retired", "immigration_status": "born_here", "population_weight": 0.03},
    {"id": 32, "city": "Victoria", "province": "BC", "age_bracket": "35-49", "income_bracket": "high", "tenure": "owner", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.03},

    # === SASKATOON (2 agents, weight 0.02) ===
    {"id": 33, "city": "Saskatoon", "province": "SK", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "owner", "debt_load": "medium", "family_size": "large_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.02},
    {"id": 34, "city": "Saskatoon", "province": "SK", "age_bracket": "18-24", "income_bracket": "very_low", "tenure": "renter", "debt_load": "none", "family_size": "single", "employment_type": "student", "immigration_status": "born_here", "population_weight": 0.02},

    # === REGINA (2 agents, weight 0.02) ===
    {"id": 35, "city": "Regina", "province": "SK", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "established_immigrant", "population_weight": 0.02},
    {"id": 36, "city": "Regina", "province": "SK", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "medium", "family_size": "couple", "employment_type": "salaried", "immigration_status": "recent_immigrant", "population_weight": 0.02},

    # === KELOWNA (2 agents, weight 0.02) ===
    {"id": 37, "city": "Kelowna", "province": "BC", "age_bracket": "65+", "income_bracket": "medium", "tenure": "owner", "debt_load": "none", "family_size": "couple", "employment_type": "retired", "immigration_status": "born_here", "population_weight": 0.02},
    {"id": 38, "city": "Kelowna", "province": "BC", "age_bracket": "35-49", "income_bracket": "high", "tenure": "owner", "debt_load": "medium", "family_size": "small_family", "employment_type": "self_employed", "immigration_status": "born_here", "population_weight": 0.02},

    # === SUDBURY (2 agents, weight 0.02) ===
    {"id": 39, "city": "Sudbury", "province": "ON", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.02},
    {"id": 40, "city": "Sudbury", "province": "ON", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "medium", "family_size": "single", "employment_type": "unemployed", "immigration_status": "born_here", "population_weight": 0.02},

    # === NORTHERN ONTARIO RURAL (2 agents, weight 0.02) ===
    {"id": 41, "city": "Northern Ontario Rural", "province": "ON", "age_bracket": "50-64", "income_bracket": "low", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "self_employed", "immigration_status": "born_here", "population_weight": 0.02},
    {"id": 42, "city": "Northern Ontario Rural", "province": "ON", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "owner", "debt_load": "medium", "family_size": "large_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.02},

    # === NORTHERN BC RURAL (2 agents, weight 0.02) ===
    {"id": 43, "city": "Northern BC Rural", "province": "BC", "age_bracket": "35-49", "income_bracket": "medium", "tenure": "owner", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.02},
    {"id": 44, "city": "Northern BC Rural", "province": "BC", "age_bracket": "65+", "income_bracket": "low", "tenure": "owner", "debt_load": "none", "family_size": "single", "employment_type": "retired", "immigration_status": "born_here", "population_weight": 0.02},

    # === PEI RURAL (2 agents, weight 0.01) ===
    {"id": 45, "city": "PEI Rural", "province": "PE", "age_bracket": "50-64", "income_bracket": "low", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "self_employed", "immigration_status": "born_here", "population_weight": 0.01},
    {"id": 46, "city": "PEI Rural", "province": "PE", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "medium", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.01},

    # === INDIGENOUS RESERVE NORTHERN ONTARIO (2 agents, weight 0.01) ===
    {"id": 47, "city": "Reserve Northern Ontario", "province": "ON", "age_bracket": "35-49", "income_bracket": "very_low", "tenure": "renter", "debt_load": "none", "family_size": "large_family", "employment_type": "unemployed", "immigration_status": "born_here", "population_weight": 0.01},
    {"id": 48, "city": "Reserve Northern Ontario", "province": "ON", "age_bracket": "18-24", "income_bracket": "very_low", "tenure": "renter", "debt_load": "none", "family_size": "single", "employment_type": "unemployed", "immigration_status": "born_here", "population_weight": 0.01},

    # === NUNAVUT/NWT REMOTE (2 agents, weight 0.01) ===
    {"id": 49, "city": "Nunavut Remote", "province": "NU", "age_bracket": "25-34", "income_bracket": "low", "tenure": "renter", "debt_load": "none", "family_size": "small_family", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.01},
    {"id": 50, "city": "Nunavut Remote", "province": "NU", "age_bracket": "50-64", "income_bracket": "medium", "tenure": "owner", "debt_load": "low", "family_size": "couple", "employment_type": "salaried", "immigration_status": "born_here", "population_weight": 0.01},
]


def get_demographic_breakdowns(agents):
    """Pre-compute all demographic groupings once at startup"""
    return {
        "renters": [a for a in agents if a["tenure"] == "renter"],
        "owners": [a for a in agents if a["tenure"] == "owner"],
        "age_18_34": [a for a in agents if a["age_bracket"] in ["18-24", "25-34"]],
        "age_65_plus": [a for a in agents if a["age_bracket"] == "65+"],
        "low_income": [a for a in agents if a["income_bracket"] in ["very_low", "low"]],
        "high_income": [a for a in agents if a["income_bracket"] in ["high", "very_high"]],
        "recent_immigrants": [a for a in agents if a["immigration_status"] in ["recent_immigrant", "refugee"]],
        "rural": [a for a in agents if any(x in a["city"] for x in ["Northern", "Rural", "Nunavut", "PEI", "Reserve"])],
    }
