import json
import os
from backboard import BackboardClient
from dotenv import load_dotenv

load_dotenv()

async def classify_policy(client, asst_id, policy_text: str) -> dict:
    """
    Runs before simulation starts.
    Classifies policy type to activate relevant agent attributes.
    """
    thread = await client.create_thread(asst_id)
    response = await client.add_message(
        thread_id=thread.thread_id,
        content=f"""Classify this Canadian government policy for demographic simulation purposes.

Policy: {policy_text}

Return exactly this JSON and nothing else:
{{
    "type": "supply|demand|tax|healthcare|transit|labour|immigration|environment|education|other",
    "primary_affected": "renters|owners|all|low_income|immigrants|seniors|youth|indigenous|workers",
    "market": "rental|ownership|both|non_housing",
    "geography": "national|provincial|urban|rural|regional",
    "time_horizon": "immediate|short_term|long_term",
    "key_attributes": ["list", "of", "3-5", "demographic", "attributes", "most", "relevant", "to", "this", "policy"]
}}""",
        llm_provider="openai",
        model_name="gpt-4o",
        stream=False,
    )
    raw = response.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {
            "type": "other",
            "primary_affected": "all",
            "market": "non_housing",
            "geography": "national",
            "time_horizon": "short_term",
            "key_attributes": ["age_bracket", "income_bracket", "employment_type"],
        }
