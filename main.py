import subprocess
import os
import requests

# Start Ollama with parallel processing unlocked
os.environ["OLLAMA_NUM_PARALLEL"] = "4"

import asyncio
from orchestrator import run_simulation

if __name__ == "__main__":
    policy = input("Enter policy to simulate (or press Enter for default): ").strip()
    if not policy:
        policy = "Canada builds 500,000 new homes over 3 years"

    # Verify Ollama is running with parallel enabled
    try:
        requests.get("http://localhost:11434")
    except Exception:
        print("ERROR: Ollama is not running. Start it with: OLLAMA_NUM_PARALLEL=8 ollama serve")
        exit(1)

    asyncio.run(run_simulation(policy))
