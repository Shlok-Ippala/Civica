# Civica

A multi-agent policy simulation engine that stress-tests Canadian government policies before they reach the public. You describe a policy. Civica deploys 8 domain specialists and 50 demographically grounded validators to find what goes wrong — and who gets hurt most.

Built for Hack Canada 2026.

---

## How it works

**Round 1 — Specialist Analysis**

Eight domain experts analyze the policy simultaneously: a labor economist, urban planner, fiscal analyst, housing economist, equity researcher, regional analyst, construction analyst, and demographic economist. Each surfaces risks with severity ratings, affected groups, and causal mechanisms.

**Round 2 — Demographic Validation**

Fifty synthetic Canadian residents — distributed across 20 cities, grounded in Statistics Canada income, vacancy, and employment data — each read the specialist risks and respond from their own position. A 25-year-old renter in Nunavut sees the policy differently than a 55-year-old homeowner in Vancouver. They confirm, reject, or flag entirely new risks the specialists missed.

**Coordinator Synthesis**

A coordinator model reads everything and produces the final intelligence report: overall risk level, key insight, blind spots, and a ranked breakdown of every risk with agent agreement scores.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Server-Sent Events |
| AI routing | Backboard SDK |
| Specialists + Coordinator | GPT-4o (OpenAI) |
| Validators | Claude Haiku (Anthropic) |
| Frontend | React 19, TypeScript, Vite, Framer Motion |
| Data | Statistics Canada (20 city profiles) |

---

## Running locally

**Prerequisites:** Python 3.11+, Node 18+

**1. Clone and install**

```bash
git clone https://github.com/Shlok-Ippala/Civica.git
cd Civica
pip install fastapi uvicorn httpx python-dotenv requests pandas stats-can
cd frontend && npm install && cd ..
```

**2. Set up environment**

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
BACKBOARD_API_KEY=espr_...
```

**3. Start the backend**

```bash
python server.py
```

Runs on `http://localhost:8000`

**4. Start the frontend**

```bash
cd frontend
npm run dev
```

Runs on `http://localhost:5173`

---

## Project structure

```
Civica/
├── server.py              # FastAPI server, SSE streaming, input validation
├── orchestrator.py        # Simulation pipeline (specialists → validators → coordinator)
├── agents.py              # 50 demographic validator personas
├── policy_classifier.py   # Pre-simulation policy classification
├── confidence_scorer.py   # Post-simulation confidence scoring
├── forward_validator.py   # Seals outputs for future real-world validation
├── data_pipeline.py       # StatsCan data loader and city profile builder
├── backboard.py           # Backboard SDK client
├── main.py                # CLI entry point (single policy or --compare mode)
├── data/
│   └── city_profiles.json # Prebuilt city profiles from StatsCan
└── frontend/
    └── src/
        ├── App.tsx                        # Stage orchestration and SSE handling
        ├── types.ts                       # Shared TypeScript types
        ├── components/
        │   ├── Stage1Input.tsx            # Policy input UI
        │   ├── Stage2Simulation.tsx       # Live agent animation
        │   └── Stage3Findings.tsx         # Intelligence report
        └── index.css                      # Design tokens and global styles
```

---

## What makes an interesting policy

The simulation produces the richest output when a policy has internal tension — groups it helps and groups it hurts, urban/rural splits, short-term vs long-term tradeoffs, or implementation gaps between provinces. Straightforwardly good or bad policies tend to produce flat results.

Some prompts that worked well:

- National rent control capping annual increases at 2%, including new construction, with a 3-year clawback
- Eliminating traditional grading in all public schools by 2027, with private schools exempt
- Mandating 30% indigenous procurement on all federal infrastructure projects over $10M

---

## Forward validation

Every simulation is sealed with a hash and timestamp in `validation_log/`. The intent is to run the same policy through the simulation after real-world outcomes are known and score the match. `forward_validator.py` handles this — it's not automated yet, but the infrastructure is there.

---

## Limitations

- Validator personas are synthetic. They are statistically grounded but not real people.
- City profiles are point-in-time StatsCan snapshots, not live data.
- The coordinator model can be overconfident. Check the blind spots section of every report.
- Parallel validator calls mean occasional empty responses — these are filtered out automatically.
