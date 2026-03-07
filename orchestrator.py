import asyncio
import aiohttp
import json
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv
from agents import AGENTS, get_demographic_breakdowns

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:0.5b"
DEMOGRAPHIC_GROUPS = get_demographic_breakdowns(AGENTS)
os.makedirs("cache", exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


def log(msg):
    print(msg, flush=True)


# --- Single agent call ---

async def call_agent(session, agent, policy_text, round_context="none"):
    prompt = f"""You are a JSON classifier. Return only valid JSON. No explanation. No markdown.

Profile: {agent['age_bracket']} {agent['tenure']} in {agent['city']}, {agent['income_bracket']} income, {agent['family_size']}, {agent['employment_type']}, {agent['immigration_status']}, {agent['debt_load']} debt
Policy: {policy_text}
Round context: {round_context}

Return exactly: {{"s":"positive/negative/mixed","i":1|2|3,"c":"max 8 words describing concern or benefit"}}
Where i means: 1=low impact, 2=medium impact, 3=high impact"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "num_predict": 60,
            "temperature": 0.7,
        },
    }

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
        "s": "mixed",
        "i": 2,
        "c": "no response received",
    }

    for attempt in range(2):
        try:
            async with session.post(OLLAMA_URL, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                raw = data.get("response", "{}")
                parsed = json.loads(raw)
                assert "s" in parsed and "i" in parsed and "c" in parsed
                s = parsed["s"] if parsed["s"] in ("positive", "negative", "mixed") else "mixed"
                i_val = parsed["i"] if isinstance(parsed["i"], int) and 1 <= parsed["i"] <= 3 else 2
                c = str(parsed["c"])[:80]
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
                    "s": s,
                    "i": i_val,
                    "c": c,
                }
        except Exception:
            if attempt == 0:
                continue
            return fallback

    return fallback


# --- Batch runner ---

async def warm_model(session):
    """Fire one dummy call to load model into memory before real run"""
    await call_agent(session, AGENTS[0], "warmup", "none")
    print("Model warmed.", flush=True)


async def run_all_agents(agents, policy_text, round_context="none"):
    batch_size = 4
    results = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(agents), batch_size):
            batch = agents[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[call_agent(session, a, policy_text, round_context) for a in batch],
                return_exceptions=True,
            )
            results += [r for r in batch_results if not isinstance(r, Exception)]
    return results


# --- Round 2 context builder ---

def build_round2_context(round1_results):
    total = len(round1_results)
    neg = [r for r in round1_results if r["s"] == "negative"]
    pos = [r for r in round1_results if r["s"] == "positive"]
    mixed = [r for r in round1_results if r["s"] == "mixed"]
    avg_i = sum(r["i"] for r in round1_results) / total if total else 0
    top_concerns = sorted(
        set(r["c"] for r in round1_results if r["s"] == "negative"),
        key=lambda c: sum(1 for r in round1_results if r["c"] == c),
        reverse=True,
    )[:5]
    renter_sentiment = [r["s"] for r in round1_results if r["tenure"] == "renter"]
    owner_sentiment = [r["s"] for r in round1_results if r["tenure"] == "owner"]

    return (
        f"R1 summary: {len(neg)}/50 negative, {len(pos)}/50 positive, {len(mixed)}/50 mixed. "
        f"Avg impact: {avg_i:.1f}/3. "
        f"Top concerns: {', '.join(top_concerns) if top_concerns else 'none'}. "
        f"Renters: {renter_sentiment.count('negative')} neg / {renter_sentiment.count('positive')} pos. "
        f"Owners: {owner_sentiment.count('negative')} neg / {owner_sentiment.count('positive')} pos."
    )


# --- Coordinator (Gemini) ---

def build_coordinator_prompt(policy_text, round_results, round_num):
    def group_summary(group_results):
        if not group_results:
            return "no data"
        neg = sum(1 for r in group_results if r["s"] == "negative")
        pos = sum(1 for r in group_results if r["s"] == "positive")
        avg = sum(r["i"] for r in group_results) / len(group_results)
        return f"{neg} neg / {pos} pos / avg_impact {avg:.1f}"

    return f"""You are analyzing Canadian policy impact across real StatsCan 2021 demographic groups.

Policy: {policy_text}
Round: {round_num}/2

Demographic breakdown:
- All renters ({len(DEMOGRAPHIC_GROUPS['renters'])} agents): {group_summary([r for r in round_results if r["tenure"] == "renter"])}
- All owners ({len(DEMOGRAPHIC_GROUPS['owners'])} agents): {group_summary([r for r in round_results if r["tenure"] == "owner"])}
- Age 18-34: {group_summary([r for r in round_results if r["age_bracket"] in ["18-24", "25-34"]])}
- Age 65+: {group_summary([r for r in round_results if r["age_bracket"] == "65+"])}
- Low income: {group_summary([r for r in round_results if r["income_bracket"] in ["very_low", "low"]])}
- High income: {group_summary([r for r in round_results if r["income_bracket"] in ["high", "very_high"]])}
- Recent immigrants: {group_summary([r for r in round_results if r["immigration_status"] in ["recent_immigrant", "refugee"]])}
- Rural/remote: {group_summary([r for r in round_results if any(x in r["city"] for x in ["Northern", "Rural", "Nunavut", "PEI", "Reserve"])])}

Top negative concerns: {list(set(r["c"] for r in round_results if r["s"] == "negative"))[:8]}

Full agent results:
{json.dumps(round_results, indent=2)}

Return exactly this JSON and nothing else:
{{
  "emergent_finding": "one sentence — the non-obvious finding nobody predicted",
  "coalition_map": "one sentence — which demographic groups aligned and which diverged",
  "risk_flag": "one sentence — the most dangerous unintended consequence",
  "sentiment_shift": "one sentence — how Round 2 opinions changed vs Round 1 (Round 2 only, else null)"
}}"""


async def run_coordinator(policy_text, round_results, round_num):
    prompt = build_coordinator_prompt(policy_text, round_results, round_num)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        log(f"  [WARN] Coordinator failed: {e}")
        return {
            "emergent_finding": "coordinator unavailable",
            "coalition_map": "coordinator unavailable",
            "risk_flag": "coordinator unavailable",
            "sentiment_shift": None,
        }


# --- Main simulation loop ---

async def run_simulation(policy_text):
    log(f"\nPolicySim starting: '{policy_text}'")
    log(f"Agents: {len(AGENTS)} | Rounds: 2 | Model: {OLLAMA_MODEL}")
    log(f"Renters: {len(DEMOGRAPHIC_GROUPS['renters'])} | Owners: {len(DEMOGRAPHIC_GROUPS['owners'])}")
    log(f"Rural/remote: {len(DEMOGRAPHIC_GROUPS['rural'])} | Recent immigrants: {len(DEMOGRAPHIC_GROUPS['recent_immigrants'])}\n")
    start = time.time()

    # WARM MODEL
    async with aiohttp.ClientSession() as session:
        await warm_model(session)

    # ROUND 1
    log("Round 1: Cold reaction...")
    r1_start = time.time()
    round1_results = await run_all_agents(AGENTS, policy_text, round_context="none")
    r1_time = time.time() - r1_start
    r1_neg = sum(1 for r in round1_results if r["s"] == "negative")
    r1_pos = sum(1 for r in round1_results if r["s"] == "positive")
    r1_mix = sum(1 for r in round1_results if r["s"] == "mixed")
    r1_avg = sum(r["i"] for r in round1_results) / len(round1_results) if round1_results else 0
    log(f"Round 1 complete in {r1_time:.1f}s — {r1_pos} pos / {r1_neg} neg / {r1_mix} mixed — avg impact {r1_avg:.1f}/3")

    # Pre-compute Round 2 context
    round2_context = build_round2_context(round1_results)
    log(f"R2 context: {round2_context}\n")

    # Filter active agents for Round 2 — only intensity >= 2
    active_ids = {r["agent_id"] for r in round1_results if r["i"] >= 2}
    active_agents = [a for a in AGENTS if a["id"] in active_ids]
    inactive_results = [
        {**r, "c": "no change from round 1"} for r in round1_results if r["i"] < 2
    ]
    log(f"Round 2: {len(active_agents)} active agents, {len(inactive_results)} unchanged\n")

    # ROUND 2 + COORDINATOR ROUND 1 — run in parallel
    log("Round 2 + Round 1 coordinator running in parallel...")
    r2_start = time.time()
    round2_active, coordinator_r1 = await asyncio.gather(
        run_all_agents(active_agents, policy_text, round_context=round2_context),
        run_coordinator(policy_text, round1_results, 1),
    )
    round2_results = round2_active + inactive_results
    r2_time = time.time() - r2_start
    r2_neg = sum(1 for r in round2_results if r["s"] == "negative")
    r2_pos = sum(1 for r in round2_results if r["s"] == "positive")
    r2_mix = sum(1 for r in round2_results if r["s"] == "mixed")
    r2_avg = sum(r["i"] for r in round2_results) / len(round2_results) if round2_results else 0
    log(f"Round 2 + Coordinator R1 complete in {r2_time:.1f}s — {r2_pos} pos / {r2_neg} neg / {r2_mix} mixed — avg impact {r2_avg:.1f}/3")

    # COORDINATOR ROUND 2
    log("\nCoordinator synthesizing Round 2...")
    c2_start = time.time()
    coordinator_r2 = await run_coordinator(policy_text, round2_results, 2)
    log(f"Coordinator R2 complete in {time.time() - c2_start:.1f}s")

    total_time = time.time() - start
    log(f"\nSimulation complete in {total_time:.1f}s")

    # Save outputs
    output = {
        "policy": policy_text,
        "total_time_seconds": round(total_time, 2),
        "agents_total": len(AGENTS),
        "round_1": {"agents": round1_results, "coordinator": coordinator_r1},
        "round_2": {"agents": round2_results, "coordinator": coordinator_r2},
    }

    with open("cache/round_1.json", "w") as f:
        json.dump({"agents": round1_results, "coordinator": coordinator_r1}, f, indent=2)
    with open("cache/round_2.json", "w") as f:
        json.dump({"agents": round2_results, "coordinator": coordinator_r2}, f, indent=2)
    with open("cache/full_simulation.json", "w") as f:
        json.dump(output, f, indent=2)

    log("\n" + "=" * 70)
    log("  RESULTS")
    log("=" * 70)
    log(f"  R1 Finding:  {coordinator_r1['emergent_finding']}")
    log(f"  R1 Risk:     {coordinator_r1['risk_flag']}")
    log(f"  R1 Coalition:{coordinator_r1['coalition_map']}")
    log(f"  R2 Finding:  {coordinator_r2['emergent_finding']}")
    log(f"  R2 Shift:    {coordinator_r2['sentiment_shift']}")
    log(f"  R2 Coalition:{coordinator_r2['coalition_map']}")
    log(f"  R2 Risk:     {coordinator_r2['risk_flag']}")
    log("=" * 70)

    return output
