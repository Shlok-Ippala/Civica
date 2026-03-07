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

    # Deduct for high variance between rounds
    r1_sentiments = [r["s"] for r in round1_results]
    r2_sentiments = [r["s"] for r in round2_results]
    r1_neg = r1_sentiments.count("negative")
    r2_neg = r2_sentiments.count("negative")
    if abs(r1_neg - r2_neg) > 15:
        score -= 1

    # Deduct for high no-response rate
    no_response = [r for r in round1_results if r["c"] == "no response received"]
    if len(no_response) > 5:
        score -= 2

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
