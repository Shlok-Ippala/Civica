import asyncio
import json
import os
import time

from backboard import BackboardClient
from dotenv import load_dotenv
from agents import AGENTS, get_demographic_breakdowns
from data_pipeline import load_city_profiles
from policy_classifier import classify_policy
from confidence_scorer import calculate_confidence
from forward_validator import seal_simulation

load_dotenv()

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")
SPECIALIST_PROVIDER = "openai"
SPECIALIST_MODEL = "gpt-4o"
VALIDATOR_PROVIDER = "anthropic"
VALIDATOR_MODEL = "claude-3-haiku-20240307"
COORDINATOR_PROVIDER = "openai"
COORDINATOR_MODEL = "gpt-4o"
DEMOGRAPHIC_GROUPS = get_demographic_breakdowns(AGENTS)
CITY_PROFILES = load_city_profiles()

# Map agent city names to data_pipeline city names
CITY_NAME_MAP = {
    "Kitchener-Waterloo": "Kitchener",
    "Northern Ontario Rural": "Northern Ontario",
    "Northern BC Rural": "Northern BC",
    "PEI Rural": "PEI",
    "Reserve Northern Ontario": "Indigenous Reserve Northern Ontario",
    "Nunavut Remote": "Nunavut",
}

RISK_CATEGORIES = [
    "affordability", "geographic", "timeline", "displacement",
    "fiscal", "employment", "infrastructure", "equity", "none",
]

SPECIALISTS = [
    {
        "id": "labor_economist",
        "title": "Labor Economist",
        "focus": "Labor market impacts: job creation, labor shortages, wage effects, employment shifts, skills gaps, construction workforce capacity",
        "categories": ["employment", "timeline"],
    },
    {
        "id": "urban_planner",
        "title": "Urban Planner",
        "focus": "Infrastructure and urban systems: transit capacity, utilities, schools, healthcare facilities, road networks, service delivery in new developments",
        "categories": ["infrastructure", "geographic"],
    },
    {
        "id": "fiscal_analyst",
        "title": "Fiscal Policy Analyst",
        "focus": "Government finances and taxation: municipal tax base changes, property tax impacts, government spending requirements, debt implications, cost-benefit of public investment",
        "categories": ["fiscal"],
    },
    {
        "id": "housing_economist",
        "title": "Housing Market Economist",
        "focus": "Housing supply and demand dynamics: price effects of new supply, rental market shifts, vacancy rate changes, speculative behavior, market absorption rates",
        "categories": ["affordability"],
    },
    {
        "id": "social_equity_researcher",
        "title": "Social Equity Researcher",
        "focus": "Distributional impacts: who benefits vs who bears costs, gentrification, displacement of vulnerable communities, access barriers, income inequality effects",
        "categories": ["equity", "displacement"],
    },
    {
        "id": "regional_development_analyst",
        "title": "Regional Development Analyst",
        "focus": "Geographic distribution: urban vs rural impacts, regional disparities, resource allocation across provinces, northern/remote community effects, Indigenous community impacts",
        "categories": ["geographic", "equity"],
    },
    {
        "id": "construction_industry_analyst",
        "title": "Construction Industry Analyst",
        "focus": "Construction sector capacity: material supply chains, contractor availability, building quality risks from rapid scaling, regulatory bottlenecks, zoning and permitting",
        "categories": ["timeline", "infrastructure"],
    },
    {
        "id": "demographic_economist",
        "title": "Demographic Economist",
        "focus": "Population and migration effects: immigration pull factors, internal migration patterns, aging population impacts, household formation trends, demand projections by age cohort",
        "categories": ["displacement", "affordability"],
    },
]

os.makedirs("cache", exist_ok=True)


def log(msg):
    print(msg, flush=True)


# --- City data helpers ---

def build_city_context(agent):
    city_key = CITY_NAME_MAP.get(agent["city"], agent["city"])
    city_data = CITY_PROFILES.get(city_key, {})

    parts = []
    if city_data.get("avg_rent_1br"):
        parts.append(f"avg_rent_1br: ${city_data['avg_rent_1br']:.0f}")
    if city_data.get("avg_rent_2br"):
        parts.append(f"avg_rent_2br: ${city_data['avg_rent_2br']:.0f}")
    if city_data.get("vacancy_rate") is not None:
        parts.append(f"vacancy: {city_data['vacancy_rate']}%")
    if city_data.get("median_household_income"):
        parts.append(f"median_income: ${city_data['median_household_income']:.0f}")
    if city_data.get("shelter_cost_to_income_ratio"):
        parts.append(f"shelter_cost_ratio: {city_data['shelter_cost_to_income_ratio']}")
    if city_data.get("unemployment_rate") is not None:
        parts.append(f"unemployment: {city_data['unemployment_rate']}%")
    if city_data.get("population"):
        parts.append(f"pop: {city_data['population']:.0f}")
    if city_data.get("population_growth_rate") is not None:
        parts.append(f"pop_growth: {city_data['population_growth_rate']}%")
    if city_data.get("housing_starts_annual"):
        parts.append(f"housing_starts: {city_data['housing_starts_annual']}")
    city_line = ", ".join(parts) if parts else "city data unavailable"

    age_income_line = ""
    income_by_age = city_data.get("income_by_age", {})
    if agent["age_bracket"] in income_by_age:
        age_income_line = f"\nDemographic income: median for {agent['age_bracket']} in {agent['city']}: ${income_by_age[agent['age_bracket']]:.0f}"

    return city_line, age_income_line


def build_all_cities_summary():
    """Build a summary of all city data for specialists."""
    lines = []
    for city_key, data in CITY_PROFILES.items():
        parts = []
        if data.get("avg_rent_1br"):
            parts.append(f"rent_1br=${data['avg_rent_1br']:.0f}")
        if data.get("vacancy_rate") is not None:
            parts.append(f"vacancy={data['vacancy_rate']}%")
        if data.get("unemployment_rate") is not None:
            parts.append(f"unemp={data['unemployment_rate']}%")
        if data.get("population"):
            parts.append(f"pop={data['population']:.0f}")
        if data.get("housing_starts_annual"):
            parts.append(f"starts={data['housing_starts_annual']}")
        if data.get("median_household_income"):
            parts.append(f"income=${data['median_household_income']:.0f}")
        if parts:
            lines.append(f"  {city_key}: {', '.join(parts)}")
    return "\n".join(lines)


# --- Round 1: Domain specialist analysis (expensive model) ---

async def call_specialist(client, thread_id, specialist, policy_text, policy_classification, cities_summary):
    prompt = f"""You are a {specialist['title']} analyzing a Canadian government policy.

Your domain: {specialist['focus']}

Policy: {policy_text}
Policy classification: {json.dumps(policy_classification)}

Real city data from Statistics Canada:
{cities_summary}

Analyze this policy ONLY through your domain expertise. Identify 2-4 specific risks that this policy CREATES or WORSENS. Do NOT flag pre-existing problems the policy fails to solve — only flag things that get WORSE because of this policy.

For each risk, ground it in the real city data above. Reference specific numbers. Explain the economic mechanism — the causal chain from policy action to negative outcome.

Return only valid JSON:
{{
    "specialist": "{specialist['id']}",
    "risks": [
        {{
            "risk": "one sentence describing the specific risk",
            "mechanism": "2-3 sentences: the causal chain from policy to risk, referencing real data",
            "severity": 1|2|3,
            "category": "one of: {"|".join(c for c in RISK_CATEGORIES if c != 'none')}",
            "most_exposed": "which demographic groups bear this risk and why",
            "cities_most_affected": ["list", "of", "cities"]
        }}
    ]
}}
Where severity means: 1=minor concern, 2=significant risk, 3=severe risk"""

    fallback = {
        "specialist": specialist["id"],
        "risks": [],
    }

    try:
        response = await client.add_message(
            thread_id=thread_id,
            content=prompt,
            llm_provider=SPECIALIST_PROVIDER,
            model_name=SPECIALIST_MODEL,
            stream=False,
        )
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        # Validate each risk
        valid_risks = []
        for r in parsed.get("risks", []):
            if "risk" in r and "severity" in r and "category" in r:
                r["severity"] = r["severity"] if isinstance(r["severity"], int) and 1 <= r["severity"] <= 3 else 2
                r["category"] = r["category"] if r["category"] in RISK_CATEGORIES else "none"
                valid_risks.append(r)
        return {"specialist": specialist["id"], "risks": valid_risks}
    except Exception as e:
        log(f"  [WARN] Specialist {specialist['id']} failed: {e}")
        return fallback


async def run_specialists(client, asst_id, policy_text, policy_classification):
    """Run all domain specialists in parallel."""
    cities_summary = build_all_cities_summary()

    threads = await asyncio.gather(
        *[client.create_thread(asst_id) for _ in SPECIALISTS]
    )

    results = await asyncio.gather(
        *[
            call_specialist(client, t.thread_id, s, policy_text, policy_classification, cities_summary)
            for t, s in zip(threads, SPECIALISTS)
        ],
        return_exceptions=True,
    )

    return [r for r in results if not isinstance(r, Exception)]


# --- Round 2: Demographic validation (cheap model) ---

def build_validation_context(specialist_results):
    """Build a summary of top specialist findings for validators.

    Takes the highest-severity risk from each specialist, plus any severity-3
    risks, deduped by category. Caps at ~10 risks to keep the prompt short.
    """
    # Collect all risks with source
    all_risks = []
    for sr in specialist_results:
        for r in sr.get("risks", []):
            all_risks.append({
                "source": sr["specialist"],
                "risk": r["risk"],
                "mechanism": r.get("mechanism", ""),
                "severity": r["severity"],
                "category": r["category"],
                "most_exposed": r.get("most_exposed", ""),
                "cities_most_affected": r.get("cities_most_affected", []),
            })

    # Take highest-severity risk per specialist
    top_per_specialist = {}
    for r in all_risks:
        src = r["source"]
        if src not in top_per_specialist or r["severity"] > top_per_specialist[src]["severity"]:
            top_per_specialist[src] = r

    # Start with top per specialist, then add any remaining severity-3 risks
    selected = list(top_per_specialist.values())
    selected_keys = {(r["source"], r["risk"]) for r in selected}
    for r in all_risks:
        if r["severity"] == 3 and (r["source"], r["risk"]) not in selected_keys:
            selected.append(r)
            selected_keys.add((r["source"], r["risk"]))

    # Cap at 10 and sort by severity descending
    selected = sorted(selected, key=lambda r: -r["severity"])[:10]

    lines = []
    for i, r in enumerate(selected, 1):
        lines.append(f"Risk {i} [{r['category']}] (severity {r['severity']}/3):")
        lines.append(f"  {r['risk']}")
        lines.append(f"  Mechanism: {r['mechanism']}")
        lines.append("")

    return "\n".join(lines), selected


async def call_validator(client, thread_id, agent, policy_text, validation_context):
    city_line, age_income_line = build_city_context(agent)

    prompt = f"""You are validating specialist risk assessments against a specific demographic profile. Domain experts identified the following risks for a Canadian policy. Your job: determine which risks ACTUALLY AFFECT someone matching your demographic profile, given your real city data.

Demographic profile: {agent['age_bracket']} {agent['tenure']} in {agent['city']}, {agent['income_bracket']} income, {agent['family_size']}, {agent['employment_type']}, {agent['immigration_status']}, {agent['debt_load']} debt
Real city data: {city_line}{age_income_line}
Policy: {policy_text}

Specialist-identified risks:
{validation_context}

For each risk, assess: does this risk ACTUALLY AFFECT someone with your specific profile and city data? Consider your income, tenure, location, employment type, and family situation.

Return only valid JSON:
{{
    "validations": [
        {{
            "risk_index": 1,
            "applies": true|false,
            "severity_for_me": 0|1|2|3,
            "reason": "one sentence — why this does or doesn't apply to your specific situation"
        }}
    ],
    "missed_risk": null or {{"risk": "one sentence", "category": "{"|".join(c for c in RISK_CATEGORIES if c != 'none')}", "severity": 1|2|3}}
}}
severity_for_me: 0=doesn't apply, 1=minor, 2=significant, 3=severe
missed_risk: a risk the specialists missed that specifically affects your demographic. null if none."""

    fallback = {
        "agent_id": agent["id"],
        "city": agent["city"],
        "tenure": agent["tenure"],
        "age_bracket": agent["age_bracket"],
        "income_bracket": agent["income_bracket"],
        "immigration_status": agent["immigration_status"],
        "family_size": agent["family_size"],
        "employment_type": agent["employment_type"],
        "population_weight": agent["population_weight"],
        "validations": [],
        "missed_risk": None,
    }

    for attempt in range(2):
        try:
            response = await client.add_message(
                thread_id=thread_id,
                content=prompt,
                llm_provider=VALIDATOR_PROVIDER,
                model_name=VALIDATOR_MODEL,
                stream=False,
            )
            raw = response.content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            return {
                "agent_id": agent["id"],
                "city": agent["city"],
                "tenure": agent["tenure"],
                "age_bracket": agent["age_bracket"],
                "income_bracket": agent["income_bracket"],
                "immigration_status": agent["immigration_status"],
                "family_size": agent["family_size"],
                "employment_type": agent["employment_type"],
                "population_weight": agent["population_weight"],
                "validations": parsed.get("validations", []),
                "missed_risk": parsed.get("missed_risk"),
            }
        except Exception:
            if attempt == 0:
                continue
            return fallback

    return fallback


async def run_validators(client, asst_id, agents, policy_text, validation_context):
    """Run all demographic validators in batches."""
    batch_size = 4
    results = []

    threads = await asyncio.gather(
        *[client.create_thread(asst_id) for _ in agents]
    )

    for i in range(0, len(agents), batch_size):
        batch_agents = agents[i : i + batch_size]
        batch_threads = threads[i : i + batch_size]
        batch_results = await asyncio.gather(
            *[
                call_validator(client, t.thread_id, a, policy_text, validation_context)
                for t, a in zip(batch_threads, batch_agents)
            ],
            return_exceptions=True,
        )
        results += [r for r in batch_results if not isinstance(r, Exception)]

    return results


# --- Coordinator: Risk synthesis ---

def build_coordinator_prompt(policy_text, specialist_results, validator_results, specialist_risks):
    """Build coordinator prompt from specialist findings + demographic validation."""

    # For each specialist risk, count how many validators confirmed it
    risk_validations = []
    for i, risk in enumerate(specialist_risks):
        confirmed_by = []
        severities = []
        for v in validator_results:
            for val in v.get("validations", []):
                if val.get("risk_index") == i + 1 and val.get("applies"):
                    confirmed_by.append({
                        "agent_id": v["agent_id"],
                        "city": v["city"],
                        "tenure": v["tenure"],
                        "age_bracket": v["age_bracket"],
                        "income_bracket": v["income_bracket"],
                        "reason": val.get("reason", ""),
                    })
                    severities.append(val.get("severity_for_me", 0))

        risk_validations.append({
            "risk": risk["risk"],
            "mechanism": risk.get("mechanism", ""),
            "source_specialist": risk.get("source", ""),
            "original_severity": risk["severity"],
            "category": risk["category"],
            "most_exposed": risk.get("most_exposed", ""),
            "cities_most_affected": risk.get("cities_most_affected", []),
            "validators_confirmed": len(confirmed_by),
            "validators_total": len(validator_results),
            "avg_severity_confirmed": round(sum(severities) / max(len(severities), 1), 1),
            "confirmed_demographics": confirmed_by[:10],
        })

    # Collect missed risks from validators
    missed_risks = []
    for v in validator_results:
        if v.get("missed_risk"):
            missed_risks.append({
                "from_agent": v["agent_id"],
                "city": v["city"],
                "demographic": f"{v['age_bracket']} {v['tenure']} {v['income_bracket']}",
                **v["missed_risk"],
            })

    return f"""You are a senior policy risk analyst producing the final risk report for a Canadian policy.

Policy: {policy_text}

PROCESS: 8 domain specialists identified risks. Then 50 demographic personas validated each risk against their real city data. Below are the results.

Specialist risks with demographic validation:
{json.dumps(risk_validations, indent=2)}

Additional risks flagged by demographic validators (missed by specialists):
{json.dumps(missed_risks, indent=2) if missed_risks else "None"}

Produce the final risk report. Rank risks by:
1. Validation breadth — how many diverse demographic groups confirmed the risk
2. Average severity among those who confirmed it
3. Whether the risk was confirmed across multiple cities and tenure types (renters AND owners)

CRITICAL: Only include risks the policy CREATES or WORSENS, not pre-existing problems.

For each risk, provide a REASONING CHAIN: (1) what economic mechanism this policy triggers, (2) specific data points that support it, (3) which demographics confirmed it and why they're vulnerable, (4) confidence level based on validation breadth.

Return exactly this JSON:
{{
    "risks": [
        {{
            "rank": 1,
            "title": "short risk title",
            "severity": "HIGH|MEDIUM|LOW",
            "reasoning": "3-5 sentence reasoning chain grounded in specialist analysis and demographic validation",
            "affected_groups": "who bears this risk",
            "confirmed_by": 0,
            "out_of": {len(validator_results)},
            "cities": ["list", "of", "affected", "cities"],
            "cascade_effect": "how this risk compounds with others, or null"
        }}
    ],
    "blind_spots": "one sentence — what demographics or perspectives are underrepresented",
    "overall_risk_level": "HIGH|MEDIUM|LOW",
    "key_insight": "one sentence — the single most important non-obvious finding"
}}"""


async def run_coordinator(client, asst_id, policy_text, specialist_results, validator_results, specialist_risks):
    prompt = build_coordinator_prompt(policy_text, specialist_results, validator_results, specialist_risks)
    try:
        thread = await client.create_thread(asst_id)
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=prompt,
            llm_provider=COORDINATOR_PROVIDER,
            model_name=COORDINATOR_MODEL,
            stream=False,
        )
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        log(f"  [WARN] Coordinator failed: {e}")
        return {
            "risks": [],
            "blind_spots": "coordinator unavailable",
            "overall_risk_level": "UNKNOWN",
            "key_insight": "coordinator unavailable",
        }


# --- Main simulation loop ---

async def run_simulation(policy_text):
    client = BackboardClient(api_key=BACKBOARD_API_KEY)

    log(f"\nCivica Risk Analysis: '{policy_text}'")
    log(f"Specialists: {len(SPECIALISTS)} ({SPECIALIST_PROVIDER}/{SPECIALIST_MODEL})")
    log(f"Validators: {len(AGENTS)} ({VALIDATOR_PROVIDER}/{VALIDATOR_MODEL})")
    log(f"Coordinator: {COORDINATOR_PROVIDER}/{COORDINATOR_MODEL}")
    log(f"Renters: {len(DEMOGRAPHIC_GROUPS['renters'])} | Owners: {len(DEMOGRAPHIC_GROUPS['owners'])}")
    log(f"Rural/remote: {len(DEMOGRAPHIC_GROUPS['rural'])} | Recent immigrants: {len(DEMOGRAPHIC_GROUPS['recent_immigrants'])}\n")
    start = time.time()

    # Create assistant
    assistant = await client.create_assistant(
        name="Civica Risk Analyst",
        system_prompt="You are a policy risk analyst. Always return valid JSON only.",
    )
    asst_id = assistant.assistant_id
    log(f"Created Backboard assistant: {asst_id}")

    # Classify policy
    log("Classifying policy...")
    policy_classification = await classify_policy(client, asst_id, policy_text)
    log(f"Policy classified: {policy_classification['type']} | affects: {policy_classification['primary_affected']}")

    # ROUND 1: Domain specialist analysis
    log(f"\nRound 1: {len(SPECIALISTS)} domain specialists analyzing policy...")
    r1_start = time.time()
    specialist_results = await run_specialists(client, asst_id, policy_text, policy_classification)
    r1_time = time.time() - r1_start

    # Summarize specialist findings
    total_risks = sum(len(sr.get("risks", [])) for sr in specialist_results)
    log(f"Round 1 complete in {r1_time:.1f}s — {total_risks} risks from {len(specialist_results)} specialists")
    for sr in specialist_results:
        risks = sr.get("risks", [])
        if risks:
            cats = [r["category"] for r in risks]
            log(f"  {sr['specialist']}: {len(risks)} risks ({', '.join(cats)})")

    # Build validation context
    validation_context, specialist_risks = build_validation_context(specialist_results)
    log(f"\nSpecialist risks to validate: {len(specialist_risks)}")

    # ROUND 2: Demographic validation
    log(f"\nRound 2: {len(AGENTS)} demographic validators checking risks...")
    r2_start = time.time()
    validator_results = await run_validators(client, asst_id, AGENTS, policy_text, validation_context)
    r2_time = time.time() - r2_start

    # Summarize validation
    total_confirmations = 0
    for v in validator_results:
        for val in v.get("validations", []):
            if val.get("applies"):
                total_confirmations += 1
    missed_count = sum(1 for v in validator_results if v.get("missed_risk"))
    log(f"Round 2 complete in {r2_time:.1f}s — {total_confirmations} risk confirmations, {missed_count} new risks flagged")

    # Per-risk confirmation counts
    for i, risk in enumerate(specialist_risks):
        confirmed = sum(
            1 for v in validator_results
            for val in v.get("validations", [])
            if val.get("risk_index") == i + 1 and val.get("applies")
        )
        log(f"  Risk {i+1} [{risk['category']}]: {confirmed}/{len(validator_results)} confirmed — {risk['risk'][:80]}")

    # COORDINATOR: Synthesize risk report
    log("\nCoordinator synthesizing risk report...")
    c_start = time.time()
    risk_report = await run_coordinator(client, asst_id, policy_text, specialist_results, validator_results, specialist_risks)
    log(f"Coordinator complete in {time.time() - c_start:.1f}s")

    total_time = time.time() - start
    log(f"\nAnalysis complete in {total_time:.1f}s")

    # Save outputs
    output = {
        "policy": policy_text,
        "total_time_seconds": round(total_time, 2),
        "specialists_total": len(SPECIALISTS),
        "validators_total": len(AGENTS),
        "models": {
            "specialist": f"{SPECIALIST_PROVIDER}/{SPECIALIST_MODEL}",
            "validator": f"{VALIDATOR_PROVIDER}/{VALIDATOR_MODEL}",
            "coordinator": f"{COORDINATOR_PROVIDER}/{COORDINATOR_MODEL}",
        },
        "round_1_specialists": specialist_results,
        "round_2_validators": validator_results,
        "risk_report": risk_report,
    }

    with open("cache/round_1_specialists.json", "w") as f:
        json.dump(specialist_results, f, indent=2)
    with open("cache/round_2_validators.json", "w") as f:
        json.dump(validator_results, f, indent=2)
    with open("cache/full_simulation.json", "w") as f:
        json.dump(output, f, indent=2)

    # --- PRINT FULL REPORT ---
    print_report(specialist_results, specialist_risks, validator_results, risk_report, policy_text)

    # Confidence score
    confidence = calculate_confidence(
        policy_classification,
        CITY_PROFILES,
        specialist_results,
        validator_results,
    )
    output["confidence"] = confidence
    output["policy_classification"] = policy_classification

    # Seal for forward validation
    seal_id = seal_simulation(policy_text, output)
    output["seal_id"] = seal_id

    with open("cache/full_simulation.json", "w") as f:
        json.dump(output, f, indent=2)

    log(f"\nConfidence: {confidence['score']}/10 — {confidence['reason']}")
    log(f"Seal ID: {seal_id}")

    return output
