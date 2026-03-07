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
            for label, policy, results in [("A", policy_a, results_a), ("B", policy_b, results_b)]:
                report = results.get("risk_report", {})
                print(f"\nPolicy {label}: {policy}")
                print(f"  Confidence: {results.get('confidence', {}).get('score', '?')}/10")
                print(f"  Overall risk level: {report.get('overall_risk_level', 'UNKNOWN')}")
                print(f"  Key insight: {report.get('key_insight', 'N/A')}")
                top_risks = report.get("risks", [])[:3]
                for r in top_risks:
                    print(f"  #{r['rank']} {r['title']} ({r['severity']})")

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
