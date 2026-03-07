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
AGENT_PROVIDER = "anthropic"
AGENT_MODEL = "claude-3-haiku-20240307"
PROMPT_PROVIDER = "openai"
PROMPT_MODEL = "gpt-4o"
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

os.makedirs("cache", exist_ok=True)


def log(msg):
    print(msg, flush=True)


# --- City data builder (shared between rounds) ---

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


# --- Prompt Generator: one expensive call to frame the analysis ---

async def generate_policy_brief(client, asst_id, policy_text, policy_classification):
    """Call an expensive model once to produce an economic brief and diverse risk angles."""
    prompt = f"""You are a senior policy economist. Analyze this Canadian government policy and produce a briefing that junior analysts will use to identify risks across different demographic groups.

Policy: {policy_text}
Classification: {json.dumps(policy_classification)}

Your job:
1. Explain the policy's ECONOMIC MECHANISMS — how does it actually work? What are the first-order effects (direct), second-order effects (market responses), and third-order effects (behavioral changes)?
2. Identify 6-8 DISTINCT risk angles that different demographic groups might face. These should span different categories: {", ".join(c for c in RISK_CATEGORIES if c != "none")}. Not every policy has risks in every category — only include genuine ones.
3. For each risk angle, note which demographic groups (by age, income, tenure, geography, employment) are most exposed.

CRITICAL: Only identify risks that the policy CREATES or WORSENS — not pre-existing problems the policy fails to fully solve. "Housing is still expensive" is not a risk of a housing supply policy. "Construction boom causes labor shortages that raise costs across the economy" IS a risk.

Return exactly this JSON:
{{
    "economic_mechanisms": "2-3 sentences explaining how this policy actually works economically — include supply/demand effects, price signals, labor market impacts, fiscal implications",
    "risk_angles": [
        {{
            "category": "one of: {"|".join(c for c in RISK_CATEGORIES if c != "none")}",
            "angle": "one sentence describing this specific risk angle",
            "most_exposed": "which demographic groups should examine this"
        }}
    ]
}}"""

    try:
        thread = await client.create_thread(asst_id)
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=prompt,
            llm_provider=PROMPT_PROVIDER,
            model_name=PROMPT_MODEL,
            stream=False,
        )
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        log(f"  [WARN] Prompt generator failed: {e}")
        return None


def assign_risk_angle(agent, risk_angles):
    """Assign a risk angle to an agent based on demographic fit."""
    if not risk_angles:
        return None
    # Distribute angles across agents to ensure coverage
    # Use agent_id as index to spread evenly
    idx = (agent["id"] - 1) % len(risk_angles)
    return risk_angles[idx]


# --- Round 1: Independent risk identification ---

async def call_agent_r1(client, thread_id, agent, policy_text, policy_brief=None):
    city_line, age_income_line = build_city_context(agent)

    # Build the prompt using the policy brief if available
    if policy_brief:
        assigned = assign_risk_angle(agent, policy_brief.get("risk_angles", []))
        angle_line = f"\nPriority risk angle to examine: {assigned['category']} — {assigned['angle']}" if assigned else ""

        prompt = f"""You are a policy risk analyst. Examine this policy through the lens of ONE specific demographic group.

Economic context (from senior analyst):
{policy_brief['economic_mechanisms']}

Demographic lens: {agent['age_bracket']} {agent['tenure']} in {agent['city']}, {agent['income_bracket']} income, {agent['family_size']}, {agent['employment_type']}, {agent['immigration_status']}, {agent['debt_load']} debt
Real city data: {city_line}{age_income_line}
Policy: {policy_text}
{angle_line}

Using the economic context and real data, identify the single most significant risk this policy CREATES OR WORSENS for someone matching this demographic profile. You MUST ground your analysis in the economic mechanisms described above — do not contradict them. Do NOT flag pre-existing problems the policy fails to fully solve — only flag things that get WORSE because of this policy. If there is genuinely no risk created by this policy, set category to "none" — that is valid and important signal.

Return only valid JSON, no explanation:
{{"risk":"one sentence describing the specific risk grounded in the data","severity":1|2|3,"category":"{"|".join(RISK_CATEGORIES)}","who_bears_it":"brief description of who is most affected"}}
Where severity means: 1=minor concern, 2=significant risk, 3=severe risk"""
    else:
        prompt = f"""You are a policy risk analyst. Examine this policy through the lens of ONE specific demographic group to identify the most significant risk they would face.

Demographic lens: {agent['age_bracket']} {agent['tenure']} in {agent['city']}, {agent['income_bracket']} income, {agent['family_size']}, {agent['employment_type']}, {agent['immigration_status']}, {agent['debt_load']} debt
Real city data: {city_line}{age_income_line}
Policy: {policy_text}

Using the real data, identify the single most significant risk this policy creates for someone matching this demographic profile. If there is genuinely no meaningful risk, set category to "none" — that is valid and useful signal.

Return only valid JSON, no explanation:
{{"risk":"one sentence describing the specific risk grounded in the data","severity":1|2|3,"category":"{"|".join(RISK_CATEGORIES)}","who_bears_it":"brief description of who is most affected"}}
Where severity means: 1=minor concern, 2=significant risk, 3=severe risk"""

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
        "risk": "no response received",
        "severity": 1,
        "category": "none",
        "who_bears_it": "unknown",
    }

    for attempt in range(2):
        try:
            response = await client.add_message(
                thread_id=thread_id,
                content=prompt,
                llm_provider=AGENT_PROVIDER,
                model_name=AGENT_MODEL,
                stream=False,
            )
            raw = response.content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            assert "risk" in parsed and "severity" in parsed and "category" in parsed
            severity = parsed["severity"] if isinstance(parsed["severity"], int) and 1 <= parsed["severity"] <= 3 else 1
            category = parsed["category"] if parsed["category"] in RISK_CATEGORIES else "none"
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
                "risk": str(parsed["risk"])[:200],
                "severity": severity,
                "category": category,
                "who_bears_it": str(parsed.get("who_bears_it", ""))[:100],
            }
        except Exception:
            if attempt == 0:
                continue
            return fallback

    return fallback


# --- Round 2: Cross-pollination and cascade detection ---

def build_round2_context(round1_results):
    risks_by_category = {}
    for r in round1_results:
        cat = r["category"]
        if cat == "none":
            continue
        if cat not in risks_by_category:
            risks_by_category[cat] = []
        risks_by_category[cat].append(r["risk"])

    lines = []
    for cat, risks in risks_by_category.items():
        unique_risks = list(set(risks))[:3]
        lines.append(f"- {cat} ({len(risks)} agents): {'; '.join(unique_risks)}")

    no_risk_count = sum(1 for r in round1_results if r["category"] == "none")
    lines.append(f"- no risk identified: {no_risk_count} agents")

    return "Risks identified in Round 1:\n" + "\n".join(lines)


async def call_agent_r2(client, thread_id, agent, policy_text, round2_context):
    city_line, age_income_line = build_city_context(agent)

    prompt = f"""You are a policy risk analyst. In Round 1, risks were identified across 50 demographic groups. Now examine whether any of these risks ALSO affect your demographic group, or if risks combine to create cascade effects.

Demographic lens: {agent['age_bracket']} {agent['tenure']} in {agent['city']}, {agent['income_bracket']} income, {agent['family_size']}, {agent['employment_type']}, {agent['immigration_status']}, {agent['debt_load']} debt
Real city data: {city_line}{age_income_line}
Policy: {policy_text}

{round2_context}

Considering all risks above, what is the most significant risk for your demographic group? It can be:
- A risk from Round 1 that also affects you (even if you didn't flag it initially)
- A cascade effect where multiple risks compound (e.g., labor shortage → delays → cost overruns → tax increases)
- A new risk you see now that wasn't apparent before
- "none" if genuinely no risk applies after reviewing everything

Return only valid JSON, no explanation:
{{"risk":"one sentence — the most significant risk after considering all evidence","severity":1|2|3,"category":"{"|".join(RISK_CATEGORIES)}","who_bears_it":"brief description","cascade":"null or one sentence describing how risks compound"}}"""

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
        "risk": "no response received",
        "severity": 1,
        "category": "none",
        "who_bears_it": "unknown",
        "cascade": None,
    }

    for attempt in range(2):
        try:
            response = await client.add_message(
                thread_id=thread_id,
                content=prompt,
                llm_provider=AGENT_PROVIDER,
                model_name=AGENT_MODEL,
                stream=False,
            )
            raw = response.content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            assert "risk" in parsed and "severity" in parsed and "category" in parsed
            severity = parsed["severity"] if isinstance(parsed["severity"], int) and 1 <= parsed["severity"] <= 3 else 1
            category = parsed["category"] if parsed["category"] in RISK_CATEGORIES else "none"
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
                "risk": str(parsed["risk"])[:200],
                "severity": severity,
                "category": category,
                "who_bears_it": str(parsed.get("who_bears_it", ""))[:100],
                "cascade": str(parsed.get("cascade", ""))[:200] if parsed.get("cascade") else None,
            }
        except Exception:
            if attempt == 0:
                continue
            return fallback

    return fallback


# --- Batch runner ---

async def create_thread(client, asst_id):
    thread = await client.create_thread(asst_id)
    return thread.thread_id


async def run_all_agents(client, asst_id, agents, call_fn, **kwargs):
    batch_size = 4
    results = []

    threads = await asyncio.gather(
        *[create_thread(client, asst_id) for _ in agents]
    )

    for i in range(0, len(agents), batch_size):
        batch_agents = agents[i : i + batch_size]
        batch_threads = threads[i : i + batch_size]
        batch_results = await asyncio.gather(
            *[
                call_fn(client, tid, a, **kwargs)
                for tid, a in zip(batch_threads, batch_agents)
            ],
            return_exceptions=True,
        )
        results += [r for r in batch_results if not isinstance(r, Exception)]
    return results


# --- Coordinator: Risk synthesis ---

def build_coordinator_prompt(policy_text, round1_results, round2_results):
    # Cluster risks by category
    def risk_cluster(results, category):
        cluster = [r for r in results if r["category"] == category]
        if not cluster:
            return None
        risks = list(set(r["risk"] for r in cluster))[:5]
        cities = list(set(r["city"] for r in cluster))
        demographics = list(set(f"{r['age_bracket']} {r['tenure']} {r['income_bracket']}" for r in cluster))
        avg_severity = sum(r["severity"] for r in cluster) / len(cluster)
        return {
            "count": len(cluster),
            "avg_severity": round(avg_severity, 1),
            "sample_risks": risks,
            "cities": cities,
            "demographics": demographics[:5],
        }

    clusters = {}
    for cat in RISK_CATEGORIES:
        if cat == "none":
            continue
        c = risk_cluster(round2_results, cat)
        if c:
            clusters[cat] = c

    # Cascade effects from R2
    cascades = [r["cascade"] for r in round2_results if r.get("cascade")]

    no_risk_r1 = sum(1 for r in round1_results if r["category"] == "none")
    no_risk_r2 = sum(1 for r in round2_results if r["category"] == "none")

    return f"""You are a senior policy risk analyst synthesizing findings from 50 demographic-specific risk assessments of a Canadian policy.

Policy: {policy_text}

Risk clusters from Round 2 (after cross-pollination):
{json.dumps(clusters, indent=2)}

Cascade effects identified:
{json.dumps(cascades, indent=2) if cascades else "None identified"}

Agents reporting no risk: {no_risk_r1} in Round 1, {no_risk_r2} in Round 2

Produce a risk report. Rank risks by: (1) how many diverse demographic groups flagged them, (2) severity, (3) whether cascade effects amplify them. A risk flagged by both renters AND owners across multiple cities is higher signal than one flagged by similar agents.

CRITICAL DISTINCTION: Only include risks that the policy CREATES or WORSENS. Do NOT include pre-existing problems that the policy merely fails to fully solve — that is policy insufficiency, not policy risk. For example, if housing is already unaffordable and the policy doesn't fix it completely, that is NOT a risk of the policy. A risk is something that gets WORSE because of the policy (e.g., labor shortages caused by rapid construction, displacement from development zones, infrastructure strain from new density).

For each risk, provide a REASONING CHAIN that walks the reader through the logic step by step: what economic mechanism THIS POLICY triggers, what data points support the risk, who is exposed and why their characteristics make them vulnerable, and how confident we should be in this conclusion.

Return exactly this JSON and nothing else:
{{
  "risks": [
    {{
      "rank": 1,
      "title": "short risk title",
      "severity": "HIGH|MEDIUM|LOW",
      "reasoning": "3-5 sentence reasoning chain: (1) the economic mechanism at play, (2) the specific data points from city profiles that support this risk, (3) which demographic groups are most exposed and why their characteristics make them vulnerable, (4) how confident we are based on how many independent agent groups flagged this",
      "affected_groups": "who bears this risk",
      "agents_flagged": 0,
      "cities": ["list", "of", "affected", "cities"],
      "cascade_effect": "how this risk compounds with others, or null"
    }}
  ],
  "blind_spots": "one sentence — what demographics or perspectives are missing from this analysis",
  "overall_risk_level": "HIGH|MEDIUM|LOW",
  "key_insight": "one sentence — the single most important non-obvious finding"
}}"""


async def run_coordinator(client, asst_id, policy_text, round1_results, round2_results):
    prompt = build_coordinator_prompt(policy_text, round1_results, round2_results)
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
    log(f"Agents: {len(AGENTS)} | Rounds: 2 | Agent model: {AGENT_PROVIDER}/{AGENT_MODEL}")
    log(f"Prompt generator: {PROMPT_PROVIDER}/{PROMPT_MODEL} | Coordinator: {COORDINATOR_PROVIDER}/{COORDINATOR_MODEL}")
    log(f"Renters: {len(DEMOGRAPHIC_GROUPS['renters'])} | Owners: {len(DEMOGRAPHIC_GROUPS['owners'])}")
    log(f"Rural/remote: {len(DEMOGRAPHIC_GROUPS['rural'])} | Recent immigrants: {len(DEMOGRAPHIC_GROUPS['recent_immigrants'])}\n")
    start = time.time()

    # Create assistant
    assistant = await client.create_assistant(
        name="Civica Risk Analyst",
        system_prompt="You are a policy risk analyst. You identify risks in government policies by examining them through specific demographic lenses. Always return valid JSON only.",
    )
    asst_id = assistant.assistant_id
    log(f"Created Backboard assistant: {asst_id}")

    # Classify policy
    log("Classifying policy...")
    policy_classification = await classify_policy(client, asst_id, policy_text)
    log(f"Policy classified: {policy_classification['type']} | affects: {policy_classification['primary_affected']}")

    # Generate policy brief (one expensive call)
    log("Generating policy brief...")
    pb_start = time.time()
    policy_brief = await generate_policy_brief(client, asst_id, policy_text, policy_classification)
    if policy_brief:
        log(f"Policy brief generated in {time.time() - pb_start:.1f}s")
        log(f"Economic mechanisms: {policy_brief['economic_mechanisms'][:200]}...")
        log(f"Risk angles: {len(policy_brief.get('risk_angles', []))} — {', '.join(a['category'] for a in policy_brief.get('risk_angles', []))}")
    else:
        log("Policy brief failed — agents will use default prompts")

    # ROUND 1: Independent risk identification
    log("\nRound 1: Independent risk identification...")
    r1_start = time.time()
    round1_results = await run_all_agents(
        client, asst_id, AGENTS, call_agent_r1,
        policy_text=policy_text,
        policy_brief=policy_brief,
    )
    r1_time = time.time() - r1_start
    r1_risks = sum(1 for r in round1_results if r["category"] != "none")
    r1_none = sum(1 for r in round1_results if r["category"] == "none")
    r1_avg_sev = sum(r["severity"] for r in round1_results if r["category"] != "none") / max(r1_risks, 1)
    log(f"Round 1 complete in {r1_time:.1f}s — {r1_risks} risks identified, {r1_none} no-risk, avg severity {r1_avg_sev:.1f}/3")

    # Show R1 risk categories
    r1_cats = {}
    for r in round1_results:
        cat = r["category"]
        r1_cats[cat] = r1_cats.get(cat, 0) + 1
    log(f"R1 categories: {dict(sorted(r1_cats.items(), key=lambda x: -x[1]))}")

    # Build Round 2 context
    round2_context = build_round2_context(round1_results)
    log(f"\n{round2_context}\n")

    # ROUND 2: Cross-pollination and cascade detection (all agents participate)
    log("Round 2: Cross-pollination and cascade detection...")
    r2_start = time.time()
    round2_results = await run_all_agents(
        client, asst_id, AGENTS, call_agent_r2,
        policy_text=policy_text,
        round2_context=round2_context,
    )
    r2_time = time.time() - r2_start
    r2_risks = sum(1 for r in round2_results if r["category"] != "none")
    r2_none = sum(1 for r in round2_results if r["category"] == "none")
    r2_avg_sev = sum(r["severity"] for r in round2_results if r["category"] != "none") / max(r2_risks, 1)
    r2_cascades = sum(1 for r in round2_results if r.get("cascade"))
    log(f"Round 2 complete in {r2_time:.1f}s — {r2_risks} risks, {r2_none} no-risk, avg severity {r2_avg_sev:.1f}/3, {r2_cascades} cascade effects")

    # COORDINATOR: Synthesize risk report
    log("\nCoordinator synthesizing risk report...")
    c_start = time.time()
    risk_report = await run_coordinator(client, asst_id, policy_text, round1_results, round2_results)
    log(f"Coordinator complete in {time.time() - c_start:.1f}s")

    total_time = time.time() - start
    log(f"\nAnalysis complete in {total_time:.1f}s")

    # Save outputs
    output = {
        "policy": policy_text,
        "total_time_seconds": round(total_time, 2),
        "agents_total": len(AGENTS),
        "models": {
            "agent": f"{AGENT_PROVIDER}/{AGENT_MODEL}",
            "coordinator": f"{COORDINATOR_PROVIDER}/{COORDINATOR_MODEL}",
        },
        "round_1": {"agents": round1_results},
        "round_2": {"agents": round2_results},
        "risk_report": risk_report,
    }

    with open("cache/round_1.json", "w") as f:
        json.dump({"agents": round1_results}, f, indent=2)
    with open("cache/round_2.json", "w") as f:
        json.dump({"agents": round2_results}, f, indent=2)
    with open("cache/full_simulation.json", "w") as f:
        json.dump(output, f, indent=2)

    # Print risk report
    log("\n" + "=" * 70)
    log(f"  RISK REPORT: {policy_text}")
    log(f"  Overall risk level: {risk_report.get('overall_risk_level', 'UNKNOWN')}")
    log("=" * 70)

    for risk in risk_report.get("risks", []):
        log(f"\n  #{risk['rank']} {risk['title']} (severity: {risk['severity']})")
        log(f"     Affected: {risk.get('affected_groups', 'N/A')}")
        log(f"     Cities: {', '.join(risk['cities']) if risk.get('cities') else 'N/A'}")
        log(f"     Agents flagged: {risk.get('agents_flagged', '?')}")
        log(f"\n     Reasoning:")
        reasoning = risk.get('reasoning', risk.get('description', 'N/A'))
        # Word-wrap reasoning at ~80 chars for readability
        words = reasoning.split()
        line = "       "
        for word in words:
            if len(line) + len(word) + 1 > 85:
                log(line)
                line = "       " + word
            else:
                line += " " + word if line.strip() else "       " + word
        if line.strip():
            log(line)
        if risk.get("cascade_effect"):
            log(f"\n     Cascade: {risk['cascade_effect']}")

    log(f"\n  Key insight: {risk_report.get('key_insight', 'N/A')}")
    log(f"  Blind spots: {risk_report.get('blind_spots', 'N/A')}")
    log("=" * 70)

    # Calculate confidence score
    confidence = calculate_confidence(
        policy_classification,
        CITY_PROFILES,
        round1_results,
        round2_results,
    )
    output["confidence"] = confidence
    output["policy_classification"] = policy_classification

    # Seal for forward validation
    seal_id = seal_simulation(policy_text, output)
    output["seal_id"] = seal_id

    # Save updated output
    with open("cache/full_simulation.json", "w") as f:
        json.dump(output, f, indent=2)

    log(f"\nConfidence: {confidence['score']}/10 — {confidence['reason']}")
    log(f"Seal ID: {seal_id}")

    return output
