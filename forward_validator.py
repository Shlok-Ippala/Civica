import json
import os
import hashlib
from datetime import datetime, timezone

os.makedirs("validation_log", exist_ok=True)

def seal_simulation(policy_text: str, full_output: dict) -> str:
    """
    Timestamps and seals simulation output for future validation.
    Returns the seal ID.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    seal_id = hashlib.md5(f"{policy_text}{timestamp}".encode()).hexdigest()[:8]

    sealed = {
        "seal_id": seal_id,
        "timestamp": timestamp,
        "policy": policy_text,
        "simulation_output": full_output,
        "validation_status": "pending",
        "validated_against": None,
        "validation_date": None,
        "validation_match_score": None
    }

    path = f"validation_log/{seal_id}_{timestamp[:10]}.json"
    with open(path, "w") as f:
        json.dump(sealed, f, indent=2)

    print(f"Simulation sealed: ID {seal_id} | {timestamp[:10]}")
    return seal_id

def validate_against_reality(
    seal_id: str,
    real_outcome: str,
    match_score: int
) -> None:
    """
    Called manually after real-world outcome is known.
    Updates the sealed file with validation result.
    """
    files = [f for f in os.listdir("validation_log") if f.startswith(seal_id)]
    if not files:
        print(f"No sealed simulation found for ID {seal_id}")
        return

    path = f"validation_log/{files[0]}"
    with open(path) as f:
        sealed = json.load(f)

    sealed["validation_status"] = "validated"
    sealed["validated_against"] = real_outcome
    sealed["validation_date"] = datetime.now(timezone.utc).isoformat()
    sealed["validation_match_score"] = match_score

    with open(path, "w") as f:
        json.dump(sealed, f, indent=2)

    print(f"Validation recorded for seal {seal_id}: {match_score}/10 match")
