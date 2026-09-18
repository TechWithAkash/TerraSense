# TerraSense — Nature Intelligence Platform

[![Backend Status](https://img.shields.io/badge/Backend-Live%20on%20Render-009245?style=flat&logo=render)](https://errasense-api.onrender.com/healthz)
[![Frontend Status](https://img.shields.io/badge/Frontend-Live%20on%20Vercel-black?style=flat&logo=vercel)](https://terra-sense.vercel.app)
[![Tests Passing](https://img.shields.io/badge/Tests-55%20passed%20(100%25)-009245?style=flat&logo=pytest)](backend/tests)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat&logo=python)](backend/pyproject.toml)
[![Framework](https://img.shields.io/badge/Next.js-16%20Turbopack-black?style=flat&logo=next.js)](frontend)

> **An AI Environmental Scientist for Land Restoration & Biodiversity Intelligence**  
> Built for the **Darukaa.Earth AI Biodiversity Intelligence Chatbot Challenge**.  
> Designed according to the official **[Darukaa Earth Design System](https://darukaa.earth/)**.

---

## 🌐 Live Demo & Endpoints

| Service | Live URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | [https://terra-sense.vercel.app](https://terra-sense.vercel.app) | Interactive conversational interface with site telemetry & evidence cards |
| **Backend API** | [https://errasense-api.onrender.com](https://errasense-api.onrender.com) | FastAPI REST service running the causal propagation engine |
| **Swagger API Docs** | [https://errasense-api.onrender.com/docs](https://errasense-api.onrender.com/docs) | Interactive OpenAPI documentation to test endpoints directly |
| **API Health Check** | [https://errasense-api.onrender.com/healthz](https://errasense-api.onrender.com/healthz) | Production liveness probe (returns `{"status":"ok"}`) |

---

## 💡 What is TerraSense?

Most AI environmental prototypes fail in four critical ways: they hallucinate scientific connections, copy effect numbers without checking context transferability, offer generic fluff like *"adopt sustainable practices"*, and fabricate arbitrary confidence percentages.

**TerraSense is not a chatbot with a PDF search attached.** It is a **deterministic causal reasoning system** paired with an intuitive conversational interface:
* **Decoupled Reasoning:** The core multi-variable causal propagation runs in **pure Python with zero LLM calls** (`app/reasoning/graph_engine.py`). It is fully deterministic, unit-tested, and inspectable.
* **Scientific Evidence Layer:** Every recommendation is backed by real, peer-reviewed literature (**FAO**, **IPBES**, **IPCC AR6**, **ICAR-CRIDA**, and meta-analyses like *Poeplau & Don 2015*).
* **Mathematical Confidence:** Confidence is computed through a 5-factor weighted geometric formula (`app/reasoning/confidence.py`) incorporating evidence strength, input completeness, and causal hop directness—never invented by a prompt.
* **Trade-Off Discovery:** Explicitly flags ecological conflicts (e.g., high-transpiration agroforestry lowering critical groundwater levels in semi-arid regions).

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 16)                   │
│   • Darukaa Earth Design System (Manrope + JetBrains Mono)  │
│   • Conversational Chat UI + JSON Input Toggle              │
│   • Real-Time Site State Panel with Provenance Badges       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Render)                 │
│                                                             │
│   ┌───────────────────────────┐ ┌───────────────────────┐   │
│   │ 1. Intake & Normalization │ │ 2. Knowledge Layer    │   │
│   │    • Free text (LLM/Regex)│ │    • 11 Core Metrics  │   │
│   │    • Structured JSON      │ │    • Causal Edges     │   │
│   │    • Key alias resolution │ │    • Structured Claims│   │
│   └─────────────┬─────────────┘ └───────────┬───────────┘   │
│                 ▼                           │               │
│   ┌───────────────────────────┐             │               │
│   │ 3. Gap Analysis Engine    │             │               │
│   │    • Checks blocking gaps │             │               │
│   │    • Max 3 smart questions│             │               │
│   └─────────────┬─────────────┘             │               │
│                 ▼                           ▼               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 4. Deterministic Causal Propagation Engine          │   │
│   │    • Breadth-first graph walk (max depth 3)         │   │
│   │    • Attenuation (0.85/hop) + Saturating transforms │   │
│   │    • Multi-metric propagation (connects ≥3 vars)    │   │
│   │    • Ecological trade-off detection                 │   │
│   └─────────────────────────┬───────────────────────────┘   │
│                             ▼                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 5. Multi-Factor Confidence & Ranking                │   │
│   │    • Weighted geometric mean of 5 evidence factors  │   │
│   │    • Citations to FAO, IPCC, IPBES & ICAR           │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Rubric Alignment (How Requirements Are Met)

| Assignment Requirement | Challenge Weight | How TerraSense Solves It | Source File |
| :--- | :---: | :--- | :--- |
| **Depth of Reasoning** | **30%** | Multi-metric graph propagation connecting $\ge 3$ variables (e.g. SOC $\rightarrow$ Water Capacity $\rightarrow$ Soil Moisture $\rightarrow$ Species Richness). Detects negative trade-offs. | [`app/reasoning/graph_engine.py`](backend/app/reasoning/graph_engine.py) |
| **Scientific Grounding** | **25%** | Recommendations cite concrete effect sizes from peer-reviewed studies (FAO 2020, IPCC AR6, IPBES, Lal 2004, Poeplau & Don 2015). Zero generic advice. | [`knowledge_base/claims.yaml`](backend/knowledge_base/claims.yaml) |
| **Knowledge System Design** | **20%** | Structured SQL claims layer + TF-IDF semantic chunk retrieval across 5 environmental categories (Soil, Water, Land, Climate, Biodiversity). | [`app/knowledge/retrieval.py`](backend/app/knowledge/retrieval.py) |
| **Conversational Intelligence**| **15%** | Asks targeted clarifying questions on incomplete inputs; retains multi-turn session state in SQLite; handles bare answers. | [`app/conversation/gap_analysis.py`](backend/app/conversation/gap_analysis.py) |
| **Output Clarity** | **10%** | Clean JSON schema output containing: what to do, why it works, metric deltas (low/mid/high), time horizon, and confidence. | [`app/schemas.py`](backend/app/schemas.py) |

---

## 🧪 The Assignment's Worked Example (Live Verification)

The challenge brief outlines an explicit reference scenario:
> **Input:** `Soil organic carbon: 0.3%, Rainfall: low, Crop: monoculture wheat, Region: semi-arid`

### 1. Incomplete Input $\rightarrow$ Intelligent Clarification
When tested with vague input (*"Biodiversity is declining on my land"*), TerraSense does **not** hallucinate generic answers. It asks for the critical missing variables:
```json
{
  "reply": "What is this land currently used for — cropland, grassland, or forest? (it decides which interventions are even applicable here)",
  "clarifying_question": "What is this land currently used for — cropland, grassland, or forest?",
  "done": false
}
```

### 2. Full Input $\rightarrow$ Multi-Variable Evidence Output
Once the baseline profile is established, TerraSense propagates the changes through the causal graph:
* **Top Recommendation:** *Legume-based cover cropping*
* **Multi-Variable Impact:** 
  * Soil Organic Carbon: $+0.10 \rightarrow +0.40\%$
  * Water Holding Capacity: $+1.5 \rightarrow +5.0\text{ mm/m}$
  * Soil Moisture Availability: $+0.02 \rightarrow +0.09\text{ index}$
  * Soil Microbial & Faunal Activity: $+0.08 \rightarrow +0.30\text{ index}$
* **Peer-Reviewed Citations:** 
  * *Food and Agriculture Organization (2020)*: GSOCseq Technical Report
  * *Poeplau and Don (2015)*: Meta-analysis on cover crops and SOC
  * *Hudson (1994)*: Organic matter and available water capacity
* **Confidence:** `0.66 (Medium-High)` — limited honestly by inferred soil texture.

---

## 🛠️ Local Development Setup

Get the entire stack running locally in under **2 minutes**:

### Prerequisites
* Python 3.12+ and `uv`
* Node.js 18+ and `npm`

### Step 1: Start Backend (Port 8000)
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```
*The SQLite database and knowledge base load automatically at startup.*

### Step 2: Start Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev
```
*Open [http://localhost:3000](http://localhost:3000) in your browser.*

### Step 3: Run the Test Suite
```bash
cd backend
uv run pytest -v
```
```
============================== 55 passed in 1.42s ==============================
```
*55 automated tests covering intake regex/LLM parsing, gap analysis, causal graph propagation, ranking constraints, trade-off detection, and golden scenario end-to-end runs.*

---

## 🗄️ Database Schema

SQLite by default for zero-friction evaluation; easily swapped to PostgreSQL via `DATABASE_URL`.

| Table | Purpose |
| :--- | :--- |
| `variables` | The 11 monitored ecological variables (soil, water, climate, biodiversity, human impact) |
| `causal_edges` | Causal links between variables with numeric deltas, transforms (saturating/linear), and citations |
| `interventions` | Ecological management practices with direct effect ranges, costs (INR/ha), and applicability rules |
| `claims` | Structured evidence store linking scientific papers to variables and interventions |
| `chunks` | Narrative excerpts for TF-IDF semantic retrieval |
| `sites` / `site_states` | Spatial parcel profile with per-variable provenance tracking (`user`, `inferred`, `looked_up`) |
| `sessions` / `messages` | Multi-turn conversational memory and context accumulation |

---

## 🚀 Deployment Architecture

* **Backend:** Deployed as a containerized web service on **Render** using Python 3.12, `uv`, and FastAPI with zero-downtime health probes (`/healthz`).
* **Frontend:** Deployed on **Vercel** with Next.js 16 App Router, Turbopack, and automated preview builds.
* **CI/CD:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) executes linting (`ruff`), automated tests (`pytest`), and frontend builds on every commit.

---

## 📋 Reviewer Access Note

If the repository is set to private, collaborator access has been granted to the Darukaa evaluation team:
* `ankita.dasgupta@darukaa.com`
* `harsh.kumar@darukaa.com`
* `utkarsh.gauniyal@darukaa.com`
* `guneet.mutreja@darukaa.com`
