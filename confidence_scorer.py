def calculate_confidence(
    policy_classification: dict,
    city_profiles: dict,
    round1_results: list,
    round2_results: list
) -> dict:
    """
    Calculates simulation confidence score. Zero runtime cost — pure math.
    """
    score = 10

    # Deduct for non-housing policies — less StatsCan data available
    if policy_classification.get("market") == "non_housing":
        score -= 2

    # Deduct for rural/remote heavy policies — sparse data
    rural_agents = [r for r in round1_results if any(
        x in r["city"] for x in ["Northern", "Nunavut", "Reserve", "PEI", "Rural"]
    )]
    if len(rural_agents) > 8:
        score -= 1

    # Deduct for high variance between rounds (risk count shift)
    r1_risks = sum(1 for r in round1_results if r["category"] != "none")
    r2_risks = sum(1 for r in round2_results if r["category"] != "none")
    if abs(r1_risks - r2_risks) > 15:
        score -= 1

    # Deduct for high no-response rate
    no_response = [r for r in round1_results if r["risk"] == "no response received"]
    if len(no_response) > 5:
        score -= 2

    # Deduct if all agents agree on same category (groupthink signal)
    r2_cats = {}
    for r in round2_results:
        cat = r["category"]
        r2_cats[cat] = r2_cats.get(cat, 0) + 1
    if r2_cats and max(r2_cats.values()) > 40:
        score -= 1

    # Build reason string
    reasons = []
    if score >= 8:
        reasons.append("strong StatsCan data coverage for this policy type")
    if policy_classification.get("geography") == "national":
        reasons.append("national scope matches agent distribution well")
    if len(no_response) == 0:
        reasons.append("all agents responded successfully")
    if score < 7:
        reasons.append("limited data coverage for some demographic groups")

    return {
        "score": max(1, min(10, score)),
        "out_of": 10,
        "reason": "; ".join(reasons) if reasons else "standard simulation conditions",
        "caveat": "This is a hypothesis generation tool. Findings should be validated against real survey data before informing policy decisions."
    }
