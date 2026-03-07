import asyncio
import json
import sys
from orchestrator import run_simulation

if __name__ == "__main__":
    # Check for comparison mode
    if "--compare" in sys.argv:
        print("Multi-policy comparison mode")
        policy_a = input("Policy A: ").strip()
        policy_b = input("Policy B: ").strip()
        if not policy_a:
            policy_a = "Canada builds 500,000 new homes over 3 years"
        if not policy_b:
            policy_b = "Canada implements a $10,000 first-time buyer tax credit"

        async def run_comparison():
            print(f"\nRunning both policies simultaneously...")
            results_a, results_b = await asyncio.gather(
                run_simulation(policy_a),
                run_simulation(policy_b)
            )

            # Print comparison summary
            print("\n=== COMPARISON RESULTS ===")
            print(f"\nPolicy A: {policy_a}")
            print(f"Confidence: {results_a['confidence']['score']}/10")
            print(f"Finding: {results_a['round_2']['coordinator']['emergent_finding']}")
            print(f"Risk: {results_a['round_2']['coordinator']['risk_flag']}")

            print(f"\nPolicy B: {policy_b}")
            print(f"Confidence: {results_b['confidence']['score']}/10")
            print(f"Finding: {results_b['round_2']['coordinator']['emergent_finding']}")
            print(f"Risk: {results_b['round_2']['coordinator']['risk_flag']}")

            # Save comparison
            comparison = {
                "policy_a": results_a,
                "policy_b": results_b
            }
            with open("cache/comparison.json", "w") as f:
                json.dump(comparison, f, indent=2)
            print("\nFull comparison saved to cache/comparison.json")

        asyncio.run(run_comparison())

    else:
        # Single policy mode
        policy = input("Enter policy to simulate (or press Enter for default): ").strip()
        if not policy:
            policy = "Canada builds 500,000 new homes over 3 years"

        asyncio.run(run_simulation(policy))
