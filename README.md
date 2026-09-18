# TerraSense

An AI environmental scientist for land restoration and biodiversity intelligence, built for the
Darukaa.Earth AI Biodiversity Intelligence Chatbot Challenge.

You describe a piece of land — free text, structured JSON, or both — and TerraSense asks only for
what it genuinely cannot infer, then returns ranked interventions. Every recommendation comes with
what to do, why it works (traced through an explicit causal chain), which metrics move and by how
much, over what time horizon, a computed confidence score, and a citation to a real source.

This is **not a chatbot with a PDF search attached**. The reasoning runs in a structured causal graph
that is pure Python with zero LLM calls, deterministic, and unit tested. The LLM (when configured) only
parses messy input at the front and phrases the answer at the back — it never invents the science.

## 1. Architecture

```
┌────────────┐      ┌──────────────────┐      ┌─────────────────────────┐
│  Frontend  │ HTTP │  FastAPI backend  │      │      Knowledge layer     │
│  Next.js   │ ───▶ │  /api/v1/chat     │ ───▶ │  variables / edges /     │
│  chat UI   │      │                   │      │  interventions / claims  │
└────────────┘      └────────┬──────────┘      │  (hand-curated YAML,     │
                              │                 │   loaded into SQLite)    │
                              ▼                 └─────────────────────────┘
                    ┌───────────────────┐
                    │  Conversation      │  intake (LLM or regex) → gap
                    │  layer             │  analysis → clarifying question
                    └────────┬───────────┘  OR generate recommendations
                              ▼
                    ┌───────────────────┐
                    │  Reasoning core     │  pure Python, no LLM calls
                    │  (the part that     │  causal graph propagation,
                    │  has to be right)   │  confidence scoring, ranking
                    └────────┬───────────┘
                              ▼
                    ┌───────────────────┐
                    │  Narration          │  templated + optional LLM
                    │  (numbers locked)   │  polish, verified against the
                    └───────────────────┘  numbers it was given
```

**Why the reasoning core has no LLM calls.** An LLM asked to "connect soil, water, and biodiversity"
produces plausible-sounding connections it cannot justify, and asked for "confidence" it just writes a
number that sounds right. Instead, `app/reasoning/graph_engine.py` walks a small, hand-curated causal
graph (`knowledge_base/edges.yaml`) with real effect sizes and citations, and `app/reasoning/confidence.py`
computes confidence from evidence quality, edge reliability, how much of the site is actually known, and
causal path length — never from the model's own judgement. That is what makes the output reproducible
and defensible instead of persuasive-sounding.

**Retrieval is structured first, semantic second.** `app/knowledge/retrieval.py` filters the `claims`
table by intervention with plain SQL before falling back to TF-IDF similarity search over the source
excerpts in `knowledge_base/papers/` (`app/knowledge/search.py`). A SQL filter on `intervention_id` finds
exactly the claims that apply, with perfect precision; semantic search only fills in narrative context
the filter might miss. See [`knowledge_base/SOURCES.md`](backend/knowledge_base/SOURCES.md) for every
source cited and its licence.

## 2. Database schema

SQLite by default (zero setup, `sqlalchemy` handles the dialect swap), Postgres in one env var change.
Full model definitions: [`backend/app/models.py`](backend/app/models.py).

| Table | Purpose |
|---|---|
| `variables` | The 11 metrics TerraSense tracks (soil, water, land use, biodiversity, human impact) |
| `causal_edges` | Hand-curated variable → variable causal links, with effect ranges and citations |
| `interventions` | The catalogue of actions; each one seeds the graph with direct effects |
| `claims` | Structured evidence: one row per citation, filterable by variable/intervention/context |
| `chunks` | Source excerpt text, used for TF-IDF semantic search |
| `sites` / `site_states` | A piece of land and its known variables, each tagged `user`, `inferred`, or `fetched` |
| `sessions` / `messages` | Conversation memory across turns |
| `recommendations` | Persisted output: predicted deltas, causal paths, confidence breakdown, cited claims |

The `provenance` column on `site_states` is the single most important design choice in the schema: the
system always knows, and can always say, which numbers came from the user and which it assumed.

## 3. Local setup

Requires Python 3.12+, `uv`, and Node 20+. No API keys required to run the full pipeline — an OpenAI key
is optional and only improves free-text parsing and prose quality (see §5).

```bash
# backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
# knowledge base loads automatically on startup

# frontend, in a second terminal
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`. Or with Docker:

```bash
docker compose up --build
```

### Try it

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Biodiversity is declining on my land"}'
```

This reproduces the assignment brief's own example exactly: TerraSense asks for land use, then
(if tree-based interventions are plausible) groundwater depth, then rainfall, before returning ranked,
cited recommendations. See [`backend/knowledge_base/SOURCES.md`](backend/knowledge_base/SOURCES.md) and
run `uv run pytest -v` in `backend/` for the reasoning core's test suite (26 tests, all on the
LLM-free code paths).

## 4. CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and PR:

- **Backend:** `ruff check`, `ruff format --check`, `pytest` with coverage
- **Frontend:** `eslint`, `next build`

Both `Dockerfile`s (`backend/Dockerfile`, `frontend/Dockerfile`) build production images; `docker-compose.yml`
wires them together locally. No deploy workflow is included — see Limitations below.

## 5. How each assignment requirement is met

| Requirement | Where |
|---|---|
| Structured, retrievable knowledge layer | `knowledge_base/*.yaml` + `chunks` table, loaded and queried through `app/knowledge/` |
| Soil, land use, biodiversity, climate, human impact coverage | `knowledge_base/variables.yaml`, all 5 categories represented |
| Clarifying questions on incomplete input | `app/conversation/gap_analysis.py`, capped at 3 rounds, asks the highest-value gap first |
| Multi-turn memory | `sessions` / `messages` tables, session persists across chat turns |
| Evidence-backed recommendations (what/why/metric/reference) | `RecommendationOut` schema, every claim traces to a real source in `claims.yaml` |
| Multi-metric reasoning (≥3 variables) | `app/reasoning/graph_engine.py` propagates through the causal graph up to 3 hops |
| Text + structured (JSON) input | `ChatRequest.message` and `.structured_input` |
| Output with recommendation, metrics, horizon, confidence | `RecommendationOut` |

## 6. What was cut, and why

Built for a multi-day take-home, not a funded team project. Scoped down deliberately from an earlier,
much heavier draft architecture:

- **No LangGraph / Monte Carlo simulation.** A deterministic low/mid/high propagation over the causal
  graph proves multi-variable reasoning just as well and is far easier to test and defend.
- **No live external geo APIs.** Geo-coordinates are an explicit bonus in the brief, not a requirement.
- **TF-IDF instead of a hosted embedding model.** No API key needed for ingestion, runs instantly offline.
- **No GCP/Cloud Run deploy pipeline.** `docker compose up` is the reviewer-facing story.

## 7. Honest limitations

1. The causal graph is hand-curated and small — 14 edges across 11 variables, covering common
   agricultural interventions well and wetlands, coastal, or high-altitude systems not at all.
2. Effect sizes are linear or saturating approximations; real ecological responses have thresholds and
   regime shifts this model doesn't capture.
3. Confidence scoring is a defensible heuristic, not a calibrated statistical model — it has never been
   checked against observed outcomes, because no such paired dataset was used.
4. Claim effect sizes in `claims.yaml` are representative syntheses of real, cited literature written by
   hand, not machine-extracted verbatim numbers — see the methodology note in `SOURCES.md`.
5. Intake without an LLM key falls back to regex extraction, which is reliable for the phrasing patterns
   it was built against but will miss more creative phrasing than an LLM would.

### What I'd build next

Real geo-enrichment (SoilGrids, Open-Meteo, GBIF) to auto-populate the site state vector from
coordinates; a hosted embedding model behind the same retrieval interface; calibrating edge effect sizes
against long-term field trial data instead of literature synthesis; and a small golden-scenario eval
harness wired into CI once there's a stable enough claim set to regression-test against.
