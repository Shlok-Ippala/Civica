def calculate_confidence(
    policy_classification: dict,
    city_profiles: dict,
    specialist_results: list,
    validator_results: list
) -> dict:
    """
    Calculates simulation confidence score. Zero runtime cost — pure math.
    """
    score = 10

    # Deduct for non-housing policies — less StatsCan data available
    if policy_classification.get("market") == "non_housing":
        score -= 2

    # Deduct if specialists produced few risks (low signal)
    total_risks = sum(len(sr.get("risks", [])) for sr in specialist_results)
    if total_risks < 4:
        score -= 1

    # Deduct for high no-response rate in validators
    no_response = [v for v in validator_results if not v.get("validations")]
    if len(no_response) > 5:
        score -= 2

    # Deduct if validators mostly disagree with specialists (low confirmation rate)
    total_confirmations = sum(
        1 for v in validator_results
        for val in v.get("validations", [])
        if val.get("applies")
    )
    total_validations = sum(
        len(v.get("validations", []))
        for v in validator_results
    )
    if total_validations > 0:
        confirmation_rate = total_confirmations / total_validations
        if confirmation_rate < 0.2:
            score -= 1

    # Build reason string
    reasons = []
    if score >= 8:
        reasons.append("strong StatsCan data coverage for this policy type")
    if policy_classification.get("geography") == "national":
        reasons.append("national scope matches agent distribution well")
    if len(no_response) == 0:
        reasons.append("all validators responded successfully")
    if total_risks >= 8:
        reasons.append("specialists identified diverse risk angles")
    if score < 7:
        reasons.append("limited data coverage for some demographic groups")

    return {
        "score": max(1, min(10, score)),
        "out_of": 10,
        "reason": "; ".join(reasons) if reasons else "standard simulation conditions",
        "caveat": "This is a hypothesis generation tool. Findings should be validated against real survey data before informing policy decisions."
    }
