import asyncio
import json
import os
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from orchestrator import run_simulation

# Common English words that suggest a real policy (not gibberish)
_POLICY_WORDS = re.compile(
    r'\b(canada|canadian|government|policy|program|fund|tax|housing|health|energy|'
    r'build|create|invest|support|reduce|increase|provide|expand|implement|deploy|'
    r'reform|regulate|national|federal|provincial|initiative|strategy|plan|budget|'
    r'benefit|worker|income|community|infrastructure|climate|transit|immigration|'
    r'indigenous|affordable|education|nuclear|clean|foreign|trade|aid)\b',
    re.IGNORECASE,
)

def _validate_policy(text: str) -> str | None:
    """Returns an error string if the policy is invalid, else None."""
    text = text.strip()
    if len(text) < 30:
        return "Policy is too short. Please describe a specific policy proposal."
    if len(text) > 2000:
        return "Policy is too long. Please keep it under 2000 characters."
    words = text.split()
    if len(words) < 5:
        return "Policy must be a complete sentence, not a single word or phrase."
    # Check ratio of non-alphabetic characters (catches keyboard mashing)
    alpha_chars = sum(c.isalpha() or c.isspace() for c in text)
    if alpha_chars / len(text) < 0.7:
        return "Input does not appear to be a valid policy proposal."
    # Must contain at least one recognisable policy-related word
    if not _POLICY_WORDS.search(text):
        return "Input does not appear to describe a government policy. Please be more specific."
    return None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class PolicyRequest(BaseModel):
    policy: str


@app.post("/simulate")
async def simulate(body: PolicyRequest):
    err = _validate_policy(body.policy)
    if err:
        return JSONResponse({"error": err}, status_code=422)

    queue: asyncio.Queue = asyncio.Queue()

    async def run():
        try:
            await run_simulation(body.policy, event_queue=queue)
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put(None)  # sentinel

    asyncio.create_task(run())

    async def stream():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/results/latest")
async def latest():
    path = os.path.join(os.path.dirname(__file__), "cache", "full_simulation.json")
    if not os.path.exists(path):
        return JSONResponse({"error": "No simulation results found"}, status_code=404)
    with open(path) as f:
        return JSONResponse(json.load(f))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
