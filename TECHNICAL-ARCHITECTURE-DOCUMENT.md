
# TerraSense

**An AI Environmental Scientist for Land Restoration and Biodiversity Intelligence**

Built for the Darukaa.Earth AI Engineer Internship Challenge.

---

## Table of Contents

1. [What We Are Building](#1-what-we-are-building)
2. [Why This Design Wins](#2-why-this-design-wins)
3. [Complete System Flow Diagram](#3-complete-system-flow-diagram)
4. [High Level Architecture](#4-high-level-architecture)
5. [Repository Structure](#5-repository-structure)
6. [Environmental Data Sources](#6-environmental-data-sources)
7. [Scientific Literature Corpus](#7-scientific-literature-corpus)
8. [The Knowledge Layer](#8-the-knowledge-layer)
9. [Database Schema](#9-database-schema)
10. [Ingestion Pipeline](#10-ingestion-pipeline)
11. [Retrieval Pipeline](#11-retrieval-pipeline)
12. [The Causal Reasoning Engine](#12-the-causal-reasoning-engine)
13. [Confidence Scoring](#13-confidence-scoring)
14. [The LangGraph Agent](#14-the-langgraph-agent)
15. [API Design](#15-api-design)
16. [Frontend](#16-frontend)
17. [Evaluation Harness](#17-evaluation-harness)
18. [Local Setup](#18-local-setup)
19. [Deployment and CI/CD](#19-deployment-and-cicd)
20. [Build Order](#20-build-order)
21. [Limitations and Next Steps](#21-limitations-and-next-steps)

---

## 1. What We Are Building

### The problem in plain words

A farmer, a land manager, or a project developer has a piece of land. Something is wrong with it. The soil is thin, the birds are gone, the yield is falling, the water table is dropping. They want to know what to actually do about it.

Today they get one of two bad answers. Either a generic list of "sustainable practices" that means nothing, or an expensive consultant report that takes six weeks.

### What TerraSense does

You describe your land, or you just give coordinates. TerraSense figures out the current state of that land from open environmental datasets, asks you only for the few things it genuinely cannot find out on its own, and then returns a ranked set of interventions. Each intervention comes with:

- **What to do**, specifically, not vaguely
- **Why it works**, traced through an explicit chain of cause and effect
- **Which metrics improve and by how much**, as a numeric range and not a point guess
- **Over what time horizon**, split into short, medium and long term
- **What it is based on**, with a citation down to the page of the source document
- **What could go wrong**, because most interventions have a downside somewhere
- **How confident we are**, computed from the evidence and not invented by a language model

### The important distinction

This is **not a chatbot with a PDF search attached**. It is a reasoning system with a conversational interface. The reasoning happens in a structured causal model that we build and can inspect. The language model parses messy human input at the front and writes readable prose at the back. It does not invent the science in the middle.

That separation is the entire design.

### Why this shape matters for Darukaa

Darukaa.Earth works on digital MRV (Measurement, Reporting and Verification) for carbon removal and biodiversity credits. Their real business question is: what is the baseline state of this parcel, what changes it, by how much, and can that number survive an auditor.

TerraSense is deliberately built as a small version of that. Every output is framed as a baseline scenario versus an intervention scenario, with the difference being the claimed gain. That is exactly how credits are calculated.

---

## 2. Why This Design Wins

Most submissions to this challenge will look like this:

```
PDFs -> chunk -> embed -> vector DB -> retrieve top 5 -> stuff into prompt -> LLM writes answer
```

That approach fails the brief in four specific ways:

| Requirement                 | Why the naive approach fails                                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Multi-metric reasoning      | The LLM is asked to connect soil, water and species in a single prompt. It produces plausible sounding connections it cannot justify. |
| Evidence backed numbers     | Retrieved text mentions "15 to 25 percent increase". The LLM copies it without checking whether that study applies to this land.      |
| Non-obvious recommendations | Retrieval surfaces the most common advice, because common advice appears most often in documents.                                     |
| Confidence                  | The LLM writes "high confidence" because the prompt asked for a confidence field.                                                     |

Our seven differentiators, each of which maps directly to a line in the evaluation rubric:

**1. An explicit causal graph.** Environmental variables are nodes. Cause and effect links are edges with real effect sizes, time lags and citations. Multi-variable reasoning becomes graph propagation, which is deterministic, inspectable and reproducible.

**2. Structured claim extraction.** We do not just store chunks of papers. We extract typed quantitative claims from them into a table we can filter and query.

**3. Context transferability scoring.** A soil carbon number measured in temperate European loam does not transfer to semi-arid Indian sandy loam. We score that mismatch and discount the effect size and the confidence accordingly.

**4. Geo-enrichment.** Give us coordinates and we populate most of the site profile automatically from open APIs. We ask only for what we cannot fetch.

**5. Value-of-information questioning.** When something is missing, we ask for the variable that would most reduce uncertainty in the final answer, not the first blank field in a form.

**6. A verifier node.** Before any answer goes out, every number in it is checked back against the claim table. Unsupported numbers are repaired or removed, and the rejection is logged.

**7. An evaluation harness.** A golden set of scenarios and automated metrics for faithfulness, retrieval quality, multi-variable coverage and non-obviousness. Wired into CI.

---

## 3. Complete System Flow Diagram

This is the whole system, from a user typing a sentence to a final recommendation leaving the API.

```mermaid
flowchart TD
    %% ---------- INPUT ----------
    A1["User Input<br/>free text, JSON, or lat-long"] --> B1

    subgraph INTAKE["STAGE 1 - Understanding the Site"]
        B1["Intake Parser<br/>LLM extracts structured fields"]
        B2{"Coordinates<br/>provided?"}
        B3["Geo Enrichment Service<br/>SoilGrids, Open-Meteo, GBIF,<br/>WorldCover, Forest Watch"]
        B4["Site State Vector<br/>12 environmental variables<br/>each tagged: user, fetched, or unknown"]
        B1 --> B2
        B2 -->|Yes| B3 --> B4
        B2 -->|No| B4
    end

    B4 --> C1

    subgraph CLARIFY["STAGE 2 - Filling the Gaps"]
        C1["Gap Analysis<br/>which variables are missing"]
        C2["Value of Information Ranking<br/>which gap hurts the answer most"]
        C3{"Critical gap<br/>remaining?"}
        C4["Ask ONE targeted question<br/>and explain why it matters"]
        C1 --> C2 --> C3
        C3 -->|Yes| C4
    end

    C4 -.->|user replies, state persists| B1
    C3 -->|No| D1

    subgraph KNOW["STAGE 3 - Knowledge Retrieval"]
        D1["Candidate Intervention Generation<br/>filter catalogue by site context"]
        D2["Structured Claim Query<br/>Postgres filter on zone,<br/>soil, rainfall, scale"]
        D3["Semantic Chunk Search<br/>pgvector similarity"]
        D4["Hybrid Merge and Rerank"]
        D5["Transferability Scoring<br/>discount non-matching studies"]
        D1 --> D2
        D1 --> D3
        D2 --> D4
        D3 --> D4
        D4 --> D5
    end

    D5 --> E1

    subgraph REASON["STAGE 4 - Causal Reasoning"]
        E1["Load Causal Subgraph<br/>edges relevant to this site"]
        E2["Apply Intervention Perturbation<br/>seed the direct effects"]
        E3["Propagate Through Graph<br/>max depth 3, with attenuation"]
        E4["Monte Carlo Uncertainty<br/>5000 samples over effect ranges"]
        E5["Predicted Metric Deltas<br/>with 80 percent intervals"]
        E6["Trade-off Detection<br/>surface negative edges"]
        E1 --> E2 --> E3 --> E4 --> E5 --> E6
    end

    E6 --> F1

    subgraph FILTER["STAGE 5 - Making It Real"]
        F1["Feasibility Filter<br/>cost, labour, water, tenure,<br/>crop calendar"]
        F2["Multi Objective Ranking<br/>impact vs cost vs time vs risk"]
        F1 --> F2
    end

    F2 --> G1

    subgraph VALIDATE["STAGE 6 - Validation"]
        G1["Narration<br/>LLM writes the explanation"]
        G2["Verifier Node<br/>every number checked against<br/>the claim table"]
        G3{"All claims<br/>supported?"}
        G4["Repair or Drop<br/>log the rejection"]
        G1 --> G2 --> G3
        G3 -->|No| G4 --> G1
    end

    G3 -->|Yes| H1["Final Structured Response"]

    subgraph OUT["STAGE 7 - Output"]
        H1 --> H2["Ranked Recommendations"]
        H1 --> H3["Baseline vs Intervention Scenario"]
        H1 --> H4["Evidence Chain with Citations"]
        H1 --> H5["Monitoring Plan for MRV"]
    end

    H1 --> I1[("Session Memory<br/>Postgres checkpoint")]
    H1 --> I2[("Intervention Ledger<br/>expected vs observed")]

    classDef stage fill:#eef7f0,stroke:#2d6a4f,stroke-width:1px,color:#1b4332
    classDef store fill:#fff4e6,stroke:#b45309,stroke-width:1px,color:#7c2d12
    class INTAKE,CLARIFY,KNOW,REASON,FILTER,VALIDATE,OUT stage
    class I1,I2 store
```

### Reading the diagram in one paragraph

A user says something. We parse it into structured fields and, if we got coordinates, we go and fetch everything we can from open environmental APIs. We check what is still missing, and if a missing variable would badly damage the answer we ask about that one thing and wait. Once we have enough, we pick candidate interventions that make sense for this land, pull supporting evidence from both a structured claim table and a semantic search, discount that evidence for how well it transfers to this specific context, then run the interventions through our causal graph to compute what actually changes and by how much. We filter out anything the user could not realistically do, rank what is left, write it up, and then check every single number we wrote against our own evidence store before letting it out the door.

---

## 4. High Level Architecture

```mermaid
flowchart LR
    subgraph CLIENT["Frontend - Next.js"]
        UI1["Chat Panel"]
        UI2["Site Map and Baseline"]
        UI3["Reasoning Trace Viewer"]
    end

    subgraph API["Backend - FastAPI"]
        R1["REST + SSE Routes"]
        R2["Session Service"]
        R3["Site Service"]
    end

    subgraph AGENT["Agent Layer - LangGraph"]
        AG["Stateful Graph<br/>11 nodes, Postgres checkpointer"]
    end

    subgraph CORE["Reasoning Core - pure Python"]
        CG["Causal Graph Engine"]
        MC["Monte Carlo Simulator"]
        CS["Confidence Scorer"]
    end

    subgraph RAG["Knowledge Layer"]
        VS["pgvector<br/>chunk embeddings"]
        CL["Claims Table<br/>structured facts"]
        GR["Causal Edges Table"]
    end

    subgraph EXT["External Data"]
        E1["SoilGrids"]
        E2["Open-Meteo"]
        E3["GBIF"]
        E4["ESA WorldCover"]
        E5["Global Forest Watch"]
    end

    subgraph OBS["Observability"]
        O1["Langfuse Traces"]
        O2["Eval Harness"]
    end

    CLIENT --> API --> AGENT
    AGENT --> CORE
    AGENT --> RAG
    AGENT --> EXT
    CORE --> RAG
    AGENT --> OBS
```

### Component responsibilities

| Layer          | Responsibility                                                 | Key technology                   |
| -------------- | -------------------------------------------------------------- | -------------------------------- |
| Frontend       | Thin. Chat, a map, and a panel that shows the reasoning chain. | Next.js 15, Tailwind, MapLibre   |
| API            | HTTP surface, streaming, session lifecycle, validation         | FastAPI, Pydantic v2, SSE        |
| Agent          | Orchestration, state machine, memory, tool calls               | LangGraph, LangChain             |
| Reasoning core | Causal propagation and uncertainty. No LLM calls at all.       | Pure Python, NumPy, NetworkX     |
| Knowledge      | Storage and retrieval of evidence and causal structure         | PostgreSQL 16, pgvector          |
| External data  | Live environmental context for a coordinate                    | httpx async clients with caching |
| Observability  | Traces, evals, regression gates                                | Langfuse, pytest                 |

**The important rule:** the reasoning core has zero LLM dependencies. You can unit test it, you can run it deterministically, and its outputs are identical on every run given the same seed. That is what makes the numbers defensible.

---

## 5. Repository Structure

```
terrasense/
├── README.md
├── docker-compose.yml
├── Makefile
├── pyproject.toml                 # managed with uv
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py              # pydantic-settings
│   │   │
│   │   ├── api/
│   │   │   ├── routes_chat.py     # SSE streaming chat
│   │   │   ├── routes_sites.py    # site CRUD + baseline
│   │   │   ├── routes_simulate.py # direct simulation, no chat
│   │   │   ├── routes_evidence.py # citation drill-down
│   │   │   └── routes_admin.py    # ingestion triggers
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py           # LangGraph assembly
│   │   │   ├── state.py           # AgentState TypedDict
│   │   │   ├── nodes/
│   │   │   │   ├── intake.py
│   │   │   │   ├── geo_enrich.py
│   │   │   │   ├── gap_analysis.py
│   │   │   │   ├── clarify.py
│   │   │   │   ├── candidates.py
│   │   │   │   ├── simulate.py
│   │   │   │   ├── retrieve.py
│   │   │   │   ├── feasibility.py
│   │   │   │   ├── rank.py
│   │   │   │   ├── narrate.py
│   │   │   │   └── verify.py
│   │   │   └── prompts/           # versioned .md prompt files
│   │   │
│   │   ├── reasoning/             # NO LLM CALLS IN HERE
│   │   │   ├── graph_engine.py    # load + propagate
│   │   │   ├── propagation.py     # the core algorithm
│   │   │   ├── monte_carlo.py     # uncertainty
│   │   │   ├── transferability.py # context matching
│   │   │   ├── confidence.py      # confidence formula
│   │   │   └── voi.py             # value of information
│   │   │
│   │   ├── knowledge/
│   │   │   ├── ingest/
│   │   │   │   ├── loader.py      # PDF -> text
│   │   │   │   ├── chunker.py     # semantic chunking
│   │   │   │   ├── claim_extractor.py
│   │   │   │   └── embedder.py
│   │   │   ├── retrieval.py       # hybrid search
│   │   │   └── rerank.py
│   │   │
│   │   ├── geo/
│   │   │   ├── soilgrids.py
│   │   │   ├── openmeteo.py
│   │   │   ├── gbif.py
│   │   │   ├── worldcover.py
│   │   │   ├── forest_watch.py
│   │   │   └── aez.py             # India agro-ecological zone lookup
│   │   │
│   │   ├── models/                # SQLAlchemy ORM
│   │   ├── schemas/               # Pydantic request/response
│   │   └── services/
│   │
│   ├── alembic/                   # migrations
│   └── tests/
│
├── knowledge_base/
│   ├── papers/                    # source PDFs, git-lfs
│   ├── causal_graph/
│   │   ├── variables.yaml         # the 12 nodes
│   │   ├── edges.yaml             # HAND CURATED, the heart of the project
│   │   └── interventions.yaml     # the intervention catalogue
│   └── seed/
│       └── sample_sites.json
│
├── evals/
│   ├── golden_scenarios.yaml      # 30 test sites
│   ├── run_eval.py
│   ├── metrics/
│   └── reports/
│
├── frontend/                      # Next.js, deliberately small
│
└── .github/workflows/
    ├── ci.yml                     # lint, type, test, eval gate
    └── deploy.yml                 # Cloud Run
```

---

## 6. Environmental Data Sources

This is where the system gets its picture of a real piece of land. Everything here is free, open and has a public API or a downloadable dataset. No paid keys required except the LLM provider.

### 6.1 Live geo-enrichment APIs

These run at request time when a user gives coordinates.

| Source                                 | What it gives us                                                                                            | How we call it                                                                                                                                                                                          | Notes                                                                                                                                                                                                                                                                                                     |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ISRIC SoilGrids v2.0**         | Soil organic carbon, pH, clay/sand/silt fraction, bulk density, CEC, at 250m resolution and multiple depths | REST:`rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=soc&property=phh2o&property=clay&property=sand&property=bdod&depth=0-5cm&depth=5-15cm&value=mean&value=uncertainty` | Watch the units. SOC comes back in dg/kg, so divide by 100 for percent. pH comes back multiplied by 10. The API also returns an uncertainty layer, which we carry through into our confidence score.                                                                                                      |
| **Open-Meteo Archive API**       | Daily rainfall, temperature min/max, evapotranspiration, going back to 1940                                 | REST:`archive-api.open-meteo.com/v1/archive?latitude=&longitude=&start_date=&end_date=&daily=precipitation_sum,temperature_2m_mean,et0_fao_evapotranspiration`                                        | Free, no API key, generous rate limits. We compute a 20 year climatology, mean annual rainfall, rainfall seasonality index and an aridity index from this.                                                                                                                                                |
| **GBIF Occurrence API**          | Recorded species observations near the site                                                                 | REST:`api.gbif.org/v1/occurrence/search?decimalLatitude={lat-0.05},{lat+0.05}&decimalLongitude={lon-0.05},{lon+0.05}&hasCoordinate=true&limit=300`                                                    | This is our observed biodiversity baseline. We compute species richness, count of distinct families, functional group breakdown (pollinators, birds, soil fauna) and Shannon index from the returned records. This one is the demo highlight because it is real observed data for the user's actual land. |
| **ESA WorldCover 2021**          | 10m land cover classification, 11 classes                                                                   | STAC / COG read from`esa-worldcover` public bucket, or Terrascope WMS                                                                                                                                 | We sample a 1km buffer around the point to compute land cover proportions, patch count and a simple fragmentation index (edge to area ratio).                                                                                                                                                             |
| **Global Forest Watch / Hansen** | Tree cover in 2000 and annual loss since                                                                    | GFW Data API:`data-api.globalforestwatch.org/dataset/umd_tree_cover_loss`                                                                                                                             | Gives a deforestation trend, which feeds the human impact variable.                                                                                                                                                                                                                                       |
| **IUCN Red List API**            | Threat status for species found via GBIF                                                                    | `apiv3.iucnredlist.org/api/v3/species/{name}`                                                                                                                                                         | Requires a free token. Used to compute a conservation priority weighting on the species list.                                                                                                                                                                                                             |
| **India-WRIS**                   | Groundwater level trends for Indian districts                                                               | Bulk CSV download, loaded into a lookup table                                                                                                                                                           | Optional. Only relevant for Indian sites, which is our focus region.                                                                                                                                                                                                                                      |
| **Bhuvan / ISRO LULC**           | India specific 56m land use land cover                                                                      | Downloadable raster                                                                                                                                                                                     | Optional fallback and cross-check for Indian sites.                                                                                                                                                                                                                                                       |

### 6.2 Static reference datasets

Loaded once into the database during setup.

| Source                                            | What it gives us                                                                       | Format                                                                         |
| ------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **NBSS&LUP Agro-Ecological Zones of India** | The 20 AEZ classification. This is our master context key for transferability scoring. | Shapefile, loaded into PostGIS                                                 |
| **FAO GSOCmap**                             | Global baseline soil organic carbon stock, 1km                                         | GeoTIFF, used as a cross-check against SoilGrids                               |
| **Köppen-Geiger climate classification**   | Global climate zone for any coordinate                                                 | Raster, used for transferability when the site is outside India                |
| **FAO Ecocrop**                             | Crop and tree species environmental tolerance ranges                                   | CSV, used to sanity check whether a suggested species can survive at this site |

### 6.3 How the data flows into the site profile

```mermaid
flowchart LR
    LL["lat, lon"] --> S1["SoilGrids"] --> V1["soil_organic_carbon<br/>soil_ph<br/>soil_texture<br/>bulk_density"]
    LL --> S2["Open-Meteo"] --> V2["annual_rainfall<br/>rainfall_seasonality<br/>mean_temperature<br/>aridity_index"]
    LL --> S3["GBIF + IUCN"] --> V3["species_richness<br/>pollinator_presence<br/>threatened_species_count"]
    LL --> S4["ESA WorldCover"] --> V4["land_cover_class<br/>canopy_cover<br/>fragmentation_index"]
    LL --> S5["Global Forest Watch"] --> V5["tree_cover_loss_trend"]
    LL --> S6["AEZ Shapefile"] --> V6["agro_ecological_zone"]

    V1 --> SV["SITE STATE VECTOR"]
    V2 --> SV
    V3 --> SV
    V4 --> SV
    V5 --> SV
    V6 --> SV

    U["User provided<br/>crop, practice, budget,<br/>labour, water access"] --> SV
```

**The provenance rule:** every value in the site state vector is stamped with where it came from (`user`, `fetched`, `inferred`, `unknown`) and a per-value uncertainty. The user always sees which numbers we looked up versus which ones they told us. This matters enormously for credibility, and it is cheap to implement.

---

## 7. Scientific Literature Corpus

The causal graph edges and the claim table are both built from these. **Curate 40 to 60 documents, not 500.** A small corpus that is correctly extracted beats a large one that is noisy. The evaluators will spot-check your citations.

### 7.1 Core corpus

| Category                            | Documents                                                                                                                                                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Soil carbon**               | FAO*Recarbonizing Global Soils* (6 volumes, use vol 1 and the relevant regional volume), FAO *Global Soil Organic Carbon Sequestration Potential Map* technical report, Poeplau and Don 2015 meta-analysis on cover crops and SOC |
| **Soil physics**              | Hudson 1994 on organic matter and available water capacity, Minasny et al. 2017 "Soil carbon 4 per mille"                                                                                                                             |
| **Agroforestry**              | ICRAF / CIFOR agroforestry evidence syntheses, FAO*Advancing Agroforestry on the Policy Agenda*, Kuyah et al. 2019 agroforestry ecosystem services meta-analysis for Africa and South Asia                                          |
| **Climate assessments**       | IPCC AR6 WG2 Chapter 5 (Food and Fibre), IPCC AR6 WG3 Chapter 7 (AFOLU), IPCC Special Report on Climate Change and Land (SRCCL) chapters 4 and 6                                                                                      |
| **Biodiversity assessments**  | IPBES Global Assessment summary and Chapter 5, IPBES Land Degradation and Restoration Assessment, IPBES Pollinators Assessment                                                                                                        |
| **Pollinators and landscape** | Garibaldi et al. 2013 on wild pollinators and crop yield, Tscharntke et al. landscape moderation of biodiversity                                                                                                                      |
| **India specific**            | ICAR-CRIDA district contingency plans, NICRA project reports, NBSS&LUP AEZ technical bulletins, India's National Biodiversity Action Plan, National Mission for Sustainable Agriculture documents                                     |
| **Restoration practice**      | SER International Principles and Standards for Ecological Restoration, Bonn Challenge / IUCN ROAM methodology                                                                                                                         |
| **MRV and credits**           | Verra SD VISta and Plan Vivo methodology documents, Verra VM0042 for agricultural land management                                                                                                                                     |

### 7.2 Why include the MRV methodologies

Because the evaluators work on credit issuance. When your system can say "the soil carbon gain you would claim here is measurable under VM0042, and it would require this sampling design," you have moved from student project to someone who understands their business.

### 7.3 Licensing note

Include a `knowledge_base/SOURCES.md` listing every document, its URL, its licence, and the date retrieved. FAO, IPCC, IPBES and most Indian government documents are freely redistributable with attribution. For anything behind a paywall, store only the extracted claims and the DOI, not the PDF. Mention this explicitly in the README. Attention to licensing is exactly the kind of detail that separates careful engineers from careless ones.

---

## 8. The Knowledge Layer

This is the heart of the project. Three things live here, and they play different roles.

### 8.1 The three parts

```mermaid
flowchart TD
    subgraph KL["KNOWLEDGE LAYER"]
        A["1. VARIABLES<br/>the 12 things we track about land"]
        B["2. CAUSAL EDGES<br/>how variables affect each other,<br/>with numbers and citations"]
        C["3. CLAIMS TABLE<br/>typed quantitative facts<br/>extracted from papers"]
        D["4. CHUNK EMBEDDINGS<br/>narrative text for explanation<br/>and fallback retrieval"]
    end
    C -->|"effect sizes populate"| B
    D -->|"supporting prose for"| C
    A -->|"nodes of"| B
```

Think of it this way. The **claims table** is the evidence. The **causal edges** are the model we built from that evidence. The **chunks** are the prose we quote when explaining. The **variables** are the vocabulary everything shares.

### 8.2 The variables (nodes)

Defined in `knowledge_base/causal_graph/variables.yaml`. Keep it to twelve. More than that and you cannot curate the edges properly.

```yaml
variables:
  - id: soil_organic_carbon
    label: "Soil Organic Carbon"
    unit: "percent"
    typical_range: [0.1, 5.0]
    category: soil
    source_priority: [user, soilgrids, gsocmap]

  - id: soil_ph
    label: "Soil pH"
    unit: "pH"
    typical_range: [4.0, 9.0]
    category: soil

  - id: water_holding_capacity
    label: "Available Water Holding Capacity"
    unit: "mm per m"
    typical_range: [40, 220]
    category: water
    derived: true          # computed, never fetched directly

  - id: soil_moisture
    label: "Soil Moisture Availability"
    unit: "index_0_1"
    category: water

  - id: canopy_cover
    label: "Tree and Canopy Cover"
    unit: "percent"
    typical_range: [0, 100]
    category: land_use

  - id: habitat_patch_size
    label: "Mean Habitat Patch Size"
    unit: "hectares"
    category: land_use

  - id: fragmentation_index
    label: "Habitat Fragmentation"
    unit: "index_0_1"
    category: land_use
    higher_is_worse: true

  - id: species_richness
    label: "Species Richness"
    unit: "count"
    category: biodiversity

  - id: pollinator_abundance
    label: "Pollinator Abundance"
    unit: "index_0_1"
    category: biodiversity

  - id: soil_biota_activity
    label: "Soil Microbial and Faunal Activity"
    unit: "index_0_1"
    category: biodiversity

  - id: nutrient_runoff
    label: "Nutrient Runoff and Pollution Load"
    unit: "index_0_1"
    category: human_impact
    higher_is_worse: true

  - id: groundwater_depth
    label: "Groundwater Table Depth"
    unit: "metres below surface"
    category: water
    higher_is_worse: true
```

Notice this covers all five categories the brief demands: soil health, land use, biodiversity indicators, climate factors and human impact.

### 8.3 The causal edges

This file is the single most valuable artifact in the repository. **Curate it by hand. Do not generate it with an LLM.** Twenty carefully sourced edges beat two hundred invented ones, and the evaluators at a climate-tech company will check.

```yaml
edges:
  - id: soc_to_awc
    source: soil_organic_carbon
    target: water_holding_capacity
    sign: positive
    # for each +1 percentage point of SOC
    effect:
      per_unit_source: 1.0
      target_delta_low: 1.5
      target_delta_mid: 3.0
      target_delta_high: 5.0
      unit: "mm per m per percent SOC"
    transform: saturating      # effect flattens above ~4 percent SOC
    saturation_point: 4.0
    lag_months: [12, 36]
    context:
      soil_texture: [sandy, sandy_loam, loam]
      confidence_tier: high
    evidence_claim_ids: [clm_0043, clm_0044, clm_0111]
    notes: "Effect is strongest in coarse textured soils, weakest in clays."

  - id: awc_to_soil_moisture
    source: water_holding_capacity
    target: soil_moisture
    sign: positive
    effect:
      per_unit_source: 10.0
      target_delta_low: 0.02
      target_delta_mid: 0.05
      target_delta_high: 0.09
      unit: "index per 10mm per m"
    transform: linear
    lag_months: [0, 6]
    context:
      rainfall_regime: [low, moderate]
      confidence_tier: medium
    evidence_claim_ids: [clm_0067]

  - id: canopy_to_pollinators
    source: canopy_cover
    target: pollinator_abundance
    sign: positive
    effect:
      per_unit_source: 10.0
      target_delta_low: 0.04
      target_delta_mid: 0.09
      target_delta_high: 0.16
      unit: "index per 10 percent canopy"
    transform: saturating
    saturation_point: 40.0
    lag_months: [18, 48]
    context:
      confidence_tier: high
    evidence_claim_ids: [clm_0088, clm_0090]

  # A NEGATIVE edge. These are what produce non-obvious trade-offs.
  - id: eucalyptus_canopy_to_groundwater
    source: canopy_cover
    target: groundwater_depth
    sign: positive          # depth increases = water table drops = bad
    effect:
      per_unit_source: 10.0
      target_delta_low: 0.1
      target_delta_mid: 0.4
      target_delta_high: 1.2
      unit: "metres per 10 percent canopy"
    transform: linear
    lag_months: [24, 60]
    context:
      species_group: [eucalyptus, high_transpiration]
      rainfall_regime: [low]
      aridity: [semi_arid, arid]
      confidence_tier: medium
    evidence_claim_ids: [clm_0132]
    notes: "Only applies to high water demand species in water limited zones."
```

### 8.4 The intervention catalogue

Interventions are the entry points. Each one directly perturbs one or more variables, and the graph handles the rest.

```yaml
interventions:
  - id: legume_cover_crop
    label: "Legume based cover cropping"
    category: soil_management
    direct_effects:
      - variable: soil_organic_carbon
        delta_low: 0.10
        delta_mid: 0.22
        delta_high: 0.40
        unit: "percentage points over 3 years"
        evidence_claim_ids: [clm_0012, clm_0013]
      - variable: soil_biota_activity
        delta_low: 0.08
        delta_mid: 0.18
        delta_high: 0.30
        evidence_claim_ids: [clm_0021]
    applicable_when:
      land_cover: [cropland]
      rainfall_mm_min: 350
    cost:
      capex_inr_per_ha: [2000, 6000]
      opex_inr_per_ha_yr: [1500, 4000]
    labour_days_per_ha: [4, 9]
    time_to_first_effect_months: 12
    reversibility: high
    mrv_note: "SOC gain is claimable under Verra VM0042 with a stratified soil sampling design."

  - id: alley_agroforestry
    label: "Alley cropping with nitrogen fixing trees"
    category: agroforestry
    direct_effects:
      - variable: canopy_cover
        delta_low: 8
        delta_mid: 15
        delta_high: 25
        unit: "percentage points over 5 years"
      - variable: soil_organic_carbon
        delta_low: 0.15
        delta_mid: 0.35
        delta_high: 0.60
    applicable_when:
      land_cover: [cropland, grassland]
      rainfall_mm_min: 500
    excluded_when:
      groundwater_depth_m_min: 15    # do not add transpiration demand where water is already deep
    cost:
      capex_inr_per_ha: [15000, 45000]
    labour_days_per_ha: [15, 30]
    time_to_first_effect_months: 24
    reversibility: low

  - id: contour_bunding
    label: "Contour bunding and staggered trenches"
    category: water_management
    direct_effects:
      - variable: soil_moisture
        delta_low: 0.06
        delta_mid: 0.14
        delta_high: 0.24
      - variable: groundwater_depth
        delta_low: -1.5
        delta_mid: -0.6
        delta_high: -0.1
    applicable_when:
      slope_percent_min: 2
    cost:
      capex_inr_per_ha: [8000, 25000]

  - id: field_margin_hedgerow
    label: "Native species field margins and hedgerows"
    category: habitat
    direct_effects:
      - variable: habitat_patch_size
        delta_low: 0.2
        delta_mid: 0.5
        delta_high: 1.0
      - variable: fragmentation_index
        delta_low: -0.15
        delta_mid: -0.08
        delta_high: -0.03
      - variable: pollinator_abundance
        delta_low: 0.10
        delta_mid: 0.20
        delta_high: 0.35
    cost:
      capex_inr_per_ha: [4000, 12000]
    land_opportunity_cost_percent: [2, 5]
```

Aim for **12 to 18 interventions** across five categories: soil management, water management, agroforestry, habitat creation and input reduction. That is enough for genuine variety without being unmaintainable.

---

## 9. Database Schema

PostgreSQL 16 with the `pgvector` and `postgis` extensions. One database, clean separation by concern.

### 9.1 Knowledge tables

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Source documents
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    authors         TEXT,
    publisher       TEXT,                 -- FAO, IPCC, IPBES, ICAR ...
    year            INT,
    doi             TEXT,
    url             TEXT,
    licence         TEXT,
    document_type   TEXT,                 -- meta_analysis | field_trial | assessment | methodology
    content_hash    TEXT UNIQUE NOT NULL, -- makes ingestion idempotent
    ingested_at     TIMESTAMPTZ DEFAULT now()
);

-- Narrative chunks for semantic search
CREATE TABLE chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number     INT,
    section_path    TEXT,                 -- "Chapter 4 > 4.2 > Soil Carbon"
    content         TEXT NOT NULL,
    token_count     INT,
    embedding       vector(1536)
);
CREATE INDEX idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops);

-- THE CLAIMS TABLE. This is what makes retrieval structured.
CREATE TABLE claims (
    id                    TEXT PRIMARY KEY,          -- clm_0043
    document_id           UUID REFERENCES documents(id),
    chunk_id              UUID REFERENCES chunks(id),
    page_number           INT,
    verbatim_span         TEXT NOT NULL,             -- exact sentence, for audit

    intervention_id       TEXT,                      -- nullable, some claims are variable-to-variable
    source_variable       TEXT,
    target_variable       TEXT NOT NULL,

    effect_direction      TEXT CHECK (effect_direction IN ('increase','decrease','no_effect','mixed')),
    effect_low            NUMERIC,
    effect_mid            NUMERIC,
    effect_high           NUMERIC,
    effect_unit           TEXT,

    time_horizon_months   INT4RANGE,

    -- CONTEXT FIELDS. These drive transferability scoring.
    agro_ecological_zone  TEXT[],
    koppen_zone           TEXT[],
    soil_texture          TEXT[],
    rainfall_regime       TEXT,                      -- low | moderate | high
    farm_scale            TEXT,                      -- smallholder | medium | commercial
    country               TEXT,

    -- EVIDENCE STRENGTH FIELDS. These drive confidence.
    study_design          TEXT,                      -- meta_analysis | rct | long_term_trial |
                                                     -- observational | modelled | expert_opinion
    n_sites               INT,
    n_studies             INT,
    duration_years        NUMERIC,

    extraction_confidence NUMERIC,                   -- how sure the extractor was
    human_reviewed        BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_claims_target ON claims(target_variable);
CREATE INDEX idx_claims_intervention ON claims(intervention_id);
CREATE INDEX idx_claims_aez ON claims USING GIN(agro_ecological_zone);
CREATE INDEX idx_claims_texture ON claims USING GIN(soil_texture);

-- The causal model, loaded from edges.yaml but stored for queryability
CREATE TABLE causal_edges (
    id                  TEXT PRIMARY KEY,
    source_variable     TEXT NOT NULL,
    target_variable     TEXT NOT NULL,
    sign                TEXT CHECK (sign IN ('positive','negative')),
    per_unit_source     NUMERIC NOT NULL,
    delta_low           NUMERIC NOT NULL,
    delta_mid           NUMERIC NOT NULL,
    delta_high          NUMERIC NOT NULL,
    unit                TEXT,
    transform           TEXT DEFAULT 'linear',   -- linear | saturating | log | threshold
    saturation_point    NUMERIC,
    lag_months_min      INT,
    lag_months_max      INT,
    context             JSONB,                   -- soil_texture, rainfall_regime, aridity ...
    confidence_tier     TEXT,                    -- high | medium | low
    evidence_claim_ids  TEXT[],
    notes               TEXT
);
CREATE INDEX idx_edges_source ON causal_edges(source_variable);

CREATE TABLE interventions (
    id                      TEXT PRIMARY KEY,
    label                   TEXT NOT NULL,
    category                TEXT,
    direct_effects          JSONB NOT NULL,
    applicable_when         JSONB,
    excluded_when           JSONB,
    cost                    JSONB,
    labour_days_per_ha      NUMRANGE,
    time_to_first_effect_months INT,
    reversibility           TEXT,
    mrv_note                TEXT
);
```

### 9.2 Site and session tables

```sql
CREATE TABLE sites (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_ref      TEXT,
    label         TEXT,
    geom          GEOGRAPHY(POINT, 4326),
    area_hectares NUMERIC,
    country       TEXT,
    aez           TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- One row per variable per site. Provenance is first class.
CREATE TABLE site_states (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id       UUID REFERENCES sites(id) ON DELETE CASCADE,
    variable_id   TEXT NOT NULL,
    value         NUMERIC,
    value_low     NUMERIC,            -- uncertainty band on the observation itself
    value_high    NUMERIC,
    unit          TEXT,
    provenance    TEXT CHECK (provenance IN ('user','fetched','inferred','unknown')),
    source_name   TEXT,               -- "SoilGrids v2.0"
    fetched_at    TIMESTAMPTZ,
    UNIQUE (site_id, variable_id)
);

CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id     UUID REFERENCES sites(id),
    created_at  TIMESTAMPTZ DEFAULT now(),
    last_active TIMESTAMPTZ DEFAULT now()
);

-- LangGraph writes its checkpoints here via PostgresSaver
CREATE TABLE checkpoints (
    thread_id     TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_id     TEXT,
    checkpoint    JSONB NOT NULL,
    metadata      JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE TABLE recommendations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id        UUID REFERENCES sessions(id),
    site_id           UUID REFERENCES sites(id),
    intervention_id   TEXT REFERENCES interventions(id),
    rank              INT,
    predicted_deltas  JSONB NOT NULL,   -- per variable: low, mid, high, horizon
    causal_paths      JSONB NOT NULL,   -- the exact edges traversed, for the trace view
    trade_offs        JSONB,
    confidence_score  NUMERIC,
    confidence_breakdown JSONB,
    cited_claim_ids   TEXT[],
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- The MRV nod. Log what was actually adopted, compare later.
CREATE TABLE intervention_ledger (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id            UUID REFERENCES sites(id),
    recommendation_id  UUID REFERENCES recommendations(id),
    adopted_on         DATE,
    area_hectares      NUMERIC,
    expected_trajectory JSONB,          -- what we predicted, frozen at adoption time
    observations       JSONB DEFAULT '[]'::jsonb,  -- what was later measured
    status             TEXT DEFAULT 'active'
);
```

### 9.3 Why the schema looks like this

Three deliberate choices worth defending in an interview:

1. **Claims are separate from chunks.** Chunks are for reading, claims are for reasoning. You can filter claims with plain SQL before you ever touch a vector index, which is faster and far more precise than similarity search alone.
2. **`site_states` has a provenance column.** Never lose track of whether a number came from the user or from an API. This single column is what lets the system honestly say "I assumed your soil carbon was 0.4 percent based on SoilGrids, correct me if you have a lab test."
3. **`recommendations.causal_paths` stores the actual traversal.** That is what powers the reasoning trace in the UI and what makes the output auditable months later.

---

## 10. Ingestion Pipeline

This runs offline, not on user requests. One command, fully reproducible.

```mermaid
flowchart LR
    P["PDF in<br/>knowledge_base/papers"] --> L["Loader<br/>PyMuPDF + layout parse"]
    L --> H{"content_hash<br/>already in DB?"}
    H -->|Yes| SKIP["Skip"]
    H -->|No| M["Metadata Extraction<br/>title, year, DOI, type"]
    M --> CH["Semantic Chunker<br/>section aware, 500-900 tokens"]
    CH --> EM["Embedder<br/>text-embedding-3-small"]
    EM --> VDB[("chunks + pgvector")]
    CH --> CE["Claim Extractor<br/>LLM with strict Pydantic schema"]
    CE --> VAL["Validator<br/>units, ranges, direction sanity"]
    VAL --> REV{"Passes<br/>auto-check?"}
    REV -->|Yes| CDB[("claims table")]
    REV -->|No| Q["review_queue.csv<br/>for human check"]
```

### 10.1 Chunking

Do not use naive fixed size splitting. Use a section aware splitter:

- Detect headings from font size and numbering patterns with PyMuPDF
- Keep tables intact as single chunks and convert them to markdown
- Target 500 to 900 tokens with 15 percent overlap
- Store `section_path` so citations can say "IPCC AR6 WG3, Chapter 7, Section 7.4.3, page 811"

### 10.2 Claim extraction

This is the step that most people skip and the one that carries the most value. For each chunk, ask the LLM to return zero or more claims against a strict schema. Zero is a valid and common answer, and the prompt must say so explicitly or you will get invented claims from narrative text.

```python
class ExtractedClaim(BaseModel):
    intervention_id: str | None
    source_variable: str | None
    target_variable: str
    effect_direction: Literal["increase", "decrease", "no_effect", "mixed"]
    effect_low: float | None
    effect_mid: float | None
    effect_high: float | None
    effect_unit: str | None
    time_horizon_months: tuple[int, int] | None
    agro_ecological_zone: list[str]
    soil_texture: list[str]
    rainfall_regime: Literal["low", "moderate", "high"] | None
    farm_scale: Literal["smallholder", "medium", "commercial"] | None
    country: str | None
    study_design: Literal["meta_analysis", "rct", "long_term_trial",
                          "observational", "modelled", "expert_opinion"]
    n_sites: int | None
    n_studies: int | None
    duration_years: float | None
    verbatim_span: str      # MUST be copied exactly from the chunk
    extraction_confidence: float
```

**The critical guardrail:** after extraction, verify that `verbatim_span` appears character for character inside the source chunk. If it does not, the claim is hallucinated and gets dropped with a log line. This one check catches the majority of extraction failures and takes ten lines of code.

### 10.3 Validation rules

Run these automatically before a claim is accepted:

- `effect_low <= effect_mid <= effect_high`
- Target variable exists in `variables.yaml`
- Effect unit is convertible to the variable's declared unit
- Effect magnitude is within a plausible range for that variable (a 400 percent SOC increase is an extraction error)
- Direction agrees with the sign of the effect values

Anything that fails goes to `review_queue.csv` and you fix it by hand. Ship the reviewed count in the README: "412 claims extracted, 361 auto-validated, 51 human reviewed, 8 rejected." Numbers like that signal rigour.

---

## 11. Retrieval Pipeline

Retrieval happens in three stages and the vector search is the *last* one, not the first.

```mermaid
flowchart TD
    Q["Query context:<br/>site state + candidate intervention"] --> S1

    S1["STAGE 1 - Structured Filter<br/>SQL on claims table"]
    S1 --> S1a["filter by target_variable<br/>filter by intervention_id<br/>site AEZ overlaps claim AEZ<br/>site texture overlaps claim texture"]
    S1a --> S2

    S2["STAGE 2 - Semantic Expansion<br/>pgvector on chunks"]
    S2 --> S2a["Narrative support and<br/>anything the filter missed"]
    S2a --> S3

    S3["STAGE 3 - Transferability Scoring"]
    S3 --> S3a["Score each claim on<br/>climate, soil, scale, country match"]
    S3a --> S4

    S4["Rerank and Merge<br/>final evidence bundle"]
```

### 11.1 Why structured first

If a user's land is semi-arid sandy loam in AEZ 6, a SQL filter finds the claims that actually apply in milliseconds and with perfect precision. Vector search would surface the most textually similar passages, which are often from a temperate long-term trial in Germany. Filter first, then let embeddings fill the gaps.

### 11.2 Transferability scoring

```python
def transferability(claim: Claim, site: SiteState) -> float:
    """Returns 0.0 to 1.0. How well does this study apply to THIS land?"""
    scores = {
        "climate":  match_climate(claim.koppen_zone, site.koppen),       # weight 0.35
        "soil":     match_texture(claim.soil_texture, site.texture),     # weight 0.25
        "rainfall": match_regime(claim.rainfall_regime, site.regime),    # weight 0.20
        "scale":    match_scale(claim.farm_scale, site.scale),           # weight 0.10
        "region":   match_region(claim.country, site.country),           # weight 0.10
    }
    return weighted_geometric_mean(scores, WEIGHTS)
```

Use a geometric mean, not arithmetic. A total climate mismatch should tank the score even if everything else matches, and geometric mean does that naturally while arithmetic mean does not.

Then apply it: `adjusted_effect_mid = claim.effect_mid * (0.5 + 0.5 * transferability)`. A perfectly transferable study keeps its full effect size. A poorly transferable one gets halved and is flagged in the output.

**Surface this to the user.** A line like "this estimate is derived largely from temperate zone trials and has been discounted by 35 percent for semi-arid transfer" is the single most credible sentence your system can produce.

---

## 12. The Causal Reasoning Engine

Pure Python. No LLM. Deterministic given a seed. This is the part you can unit test and the part that makes your numbers defensible.

### 12.1 The algorithm in plain words

1. Load the causal edges that are valid for this site's context (matching soil texture, rainfall regime, aridity).
2. Take the chosen intervention and apply its direct effects as the starting perturbation.
3. Walk outward through the graph. For each edge, compute how much the target variable moves given how much the source moved.
4. Stop at depth 3. Beyond that, effects are too diluted and too uncertain to claim.
5. Attenuate as you go, because each hop adds uncertainty. Multiply effect by 0.85 per hop.
6. Repeat the whole thing 5000 times, each time sampling effect sizes from their range instead of using the midpoint. That gives you a distribution, and the distribution gives you honest intervals.

### 12.2 The propagation code shape

```python
ATTENUATION_PER_HOP = 0.85
MAX_DEPTH = 3

def propagate(
    intervention: Intervention,
    site: SiteState,
    edges: list[CausalEdge],
    rng: np.random.Generator,
) -> dict[str, float]:
    """One Monte Carlo sample. Returns delta per variable."""
    deltas: dict[str, float] = {}
    frontier: list[tuple[str, float, int]] = []

    # Seed with direct effects, sampled from the range
    for eff in intervention.direct_effects:
        d = sample_triangular(eff.low, eff.mid, eff.high, rng)
        deltas[eff.variable] = deltas.get(eff.variable, 0.0) + d
        frontier.append((eff.variable, d, 0))

    # Breadth first propagation
    while frontier:
        var, delta, depth = frontier.pop(0)
        if depth >= MAX_DEPTH:
            continue
        for edge in outgoing(edges, var):
            if not context_matches(edge, site):
                continue
            magnitude = apply_transform(edge, source_delta=delta, site=site)
            sampled = sample_triangular(
                edge.delta_low, edge.delta_mid, edge.delta_high, rng
            )
            contribution = (
                magnitude
                * sampled
                * (ATTENUATION_PER_HOP ** (depth + 1))
                * (-1 if edge.sign == "negative" else 1)
            )
            deltas[edge.target] = deltas.get(edge.target, 0.0) + contribution
            frontier.append((edge.target, contribution, depth + 1))

    return deltas
```

### 12.3 Transforms

Not every relationship is a straight line. Support four:

| Transform      | When to use                                | Behaviour                                                                                                                                      |
| -------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `linear`     | Default, small perturbations               | delta_target proportional to delta_source                                                                                                      |
| `saturating` | Most biological responses                  | Effect flattens as source approaches`saturation_point`. Adding canopy from 5 to 15 percent helps pollinators far more than 45 to 55 percent. |
| `threshold`  | Effects with a floor                       | No effect until source crosses a minimum, then linear                                                                                          |
| `log`        | Diminishing returns without a hard ceiling | delta proportional to log of source change                                                                                                     |

Getting saturating curves right is what stops your system from claiming absurd gains on already healthy land. If a site already has 3.8 percent SOC, cover cropping should show a small gain, not the same headline number a degraded site gets. **That single behaviour will visibly separate you from every prompt-only submission.**

### 12.4 Monte Carlo and output

```python
def simulate(intervention, site, edges, n=5000, seed=42):
    rng = np.random.default_rng(seed)
    samples = [propagate(intervention, site, edges, rng) for _ in range(n)]
    result = {}
    for var in all_touched_variables(samples):
        vals = np.array([s.get(var, 0.0) for s in samples])
        result[var] = {
            "p10": float(np.percentile(vals, 10)),
            "p50": float(np.percentile(vals, 50)),
            "p90": float(np.percentile(vals, 90)),
            "prob_positive": float((vals > 0).mean()),
        }
    return result
```

Fixing the seed means your demo produces identical output every time, which matters when someone re-runs it during review.

### 12.5 Trade-off detection

After propagation, scan the result for any variable where the change moves in a harmful direction (a rise in `fragmentation_index`, `nutrient_runoff` or `groundwater_depth`, or a fall in anything else). Every one of those becomes an explicit trade-off in the output, with the causal path that caused it and a suggested mitigation.

This is where non-obvious recommendations come from for free. The graph finds tensions a prompt would never surface:

> Alley agroforestry raises soil carbon and pollinator abundance, but in your semi-arid zone with the water table already at 18 metres, the added transpiration demand is projected to deepen it a further 0.4 to 1.2 metres over 5 years. Mitigation: pair with contour bunding, or select low water demand native species instead of eucalyptus.

That paragraph, produced structurally rather than by prompting, is what wins the depth of reasoning score.

### 12.6 Baseline versus intervention framing

Always compute two trajectories, never one number:

- **Baseline scenario:** where these variables go over 5 years with no action, using observed trends (tree cover loss trend, rainfall trend, current management).
- **Intervention scenario:** baseline plus the propagated intervention effect.
- **The claimed gain is the difference**, which is exactly how additionality is defined in carbon and biodiversity credit methodologies.

Present it as a small table in every recommendation. Darukaa will recognise the shape immediately.

---

## 13. Confidence Scoring

Never let the LLM decide confidence. Compute it from five components.

```python
def confidence(rec: Recommendation) -> ConfidenceBreakdown:
    components = {
        # How good is the underlying science
        "evidence_strength": evidence_strength(rec.claims),      # w 0.30
        # Does that science apply to THIS land
        "transferability":   mean_transferability(rec.claims),   # w 0.25
        # Do we actually know enough about the site
        "input_completeness": completeness(rec.site),            # w 0.20
        # Longer causal chains are less certain
        "path_directness":   1.0 / (1 + 0.4 * rec.mean_path_length),  # w 0.15
        # Do the sources agree with each other
        "study_agreement":   agreement(rec.claims),              # w 0.10
    }
    score = weighted_geometric_mean(components, WEIGHTS)
    return ConfidenceBreakdown(
        score=score,
        band=to_band(score),        # Low / Medium / Medium-High / High
        components=components,
        limiting_factor=min(components, key=components.get),
    )
```

### Study design weights

| Design                           | Weight |
| -------------------------------- | ------ |
| Meta analysis                    | 1.00   |
| Long term trial, 5 years or more | 0.90   |
| Randomised controlled trial      | 0.85   |
| Short field trial                | 0.70   |
| Observational study              | 0.55   |
| Modelled projection              | 0.45   |
| Expert opinion                   | 0.30   |

### Always report the limiting factor

The output should not just say "Medium-High confidence". It should say:

> **Confidence: Medium-High (0.71).** Limited mainly by input completeness: soil texture was inferred from SoilGrids rather than measured, and no information was provided on current tillage practice. A soil texture test would raise this to roughly 0.82.

That last sentence, telling the user how to increase confidence, is the value-of-information calculation surfaced in plain language. It is a small feature that reads as very senior.

---

## 14. The LangGraph Agent

### 14.1 The state object

```python
class AgentState(TypedDict):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

    # Site understanding
    site_id: str | None
    coordinates: tuple[float, float] | None
    state_vector: dict[str, SiteVariable]      # value + provenance + uncertainty
    site_context: SiteContext                  # aez, koppen, texture, regime, scale

    # Gap handling
    missing_variables: list[str]
    voi_ranking: list[tuple[str, float]]
    clarification_rounds: int                  # hard cap at 3
    pending_question: str | None

    # Reasoning
    candidate_interventions: list[str]
    evidence_bundle: dict[str, list[Claim]]
    simulation_results: dict[str, SimResult]
    trade_offs: list[TradeOff]
    ranked_recommendations: list[Recommendation]

    # Validation
    draft_response: str | None
    verification_report: VerificationReport | None
    verification_attempts: int                 # hard cap at 2
```

### 14.2 The node graph

```mermaid
stateDiagram-v2
    [*] --> intake
    intake --> geo_enrich: has coordinates
    intake --> gap_analysis: no coordinates
    geo_enrich --> gap_analysis
    gap_analysis --> clarify: critical gap and rounds < 3
    gap_analysis --> candidates: enough information
    clarify --> [*]: wait for user reply
    candidates --> retrieve
    retrieve --> simulate
    simulate --> feasibility
    feasibility --> rank
    rank --> narrate
    narrate --> verify
    verify --> narrate: unsupported claims and attempts < 2
    verify --> persist: passed
    persist --> [*]
```

### 14.3 What each node does

| Node             | LLM? | Job                                                                                                                                                                                    |
| ---------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `intake`       | Yes  | Parse free text or JSON into structured fields. Detect intent: new site, follow up question, what-if, or general query. Extract any coordinates, crop, practice, constraint mentioned. |
| `geo_enrich`   | No   | Fire all external API calls concurrently with`asyncio.gather`. 8 second timeout each, degrade gracefully, cache by rounded coordinate for 30 days.                                   |
| `gap_analysis` | No   | Compare the state vector against what the candidate interventions need. Run the VoI calculation to rank the gaps.                                                                      |
| `clarify`      | Yes  | Ask exactly one question, the highest VoI one, and explain in a sentence why it matters. Hard cap of 3 rounds so the system never traps the user in a questionnaire.                   |
| `candidates`   | No   | Filter the intervention catalogue against`applicable_when` and `excluded_when`. Typically narrows 15 down to 5 or 6.                                                               |
| `retrieve`     | No   | The three stage retrieval from section 11.                                                                                                                                             |
| `simulate`     | No   | The causal engine from section 12. Runs for every candidate.                                                                                                                           |
| `feasibility`  | No   | Apply user constraints: budget ceiling, labour availability, water access, land tenure, crop calendar conflicts. Drop or flag anything that fails.                                     |
| `rank`         | No   | Multi objective score. Default weights: biodiversity impact 0.35, cost efficiency 0.25, time to effect 0.20, risk and reversibility 0.20. User can override.                           |
| `narrate`      | Yes  | Write the explanation. Receives only the simulation output and the evidence bundle, and is explicitly forbidden from introducing numbers that are not in its input.                    |
| `verify`       | Yes  | Extract every numeric claim from the draft, match each against the evidence bundle and simulation output, and produce a pass/fail report per claim.                                    |
| `persist`      | No   | Write the recommendation, the causal paths and the confidence breakdown to Postgres.                                                                                                   |

### 14.4 The verifier in more detail

This node is your strongest trust signal, so implement it properly.

```python
class VerificationReport(BaseModel):
    total_numeric_claims: int
    supported: list[SupportedClaim]
    unsupported: list[UnsupportedClaim]   # with the offending text span
    passed: bool

# Rules
# 1. Every number in the draft must trace to either a simulation result
#    or a claim id in the evidence bundle. Tolerance: 5 percent.
# 2. Every citation must reference a real document id that is in the bundle.
# 3. No superlatives without a supporting comparison ("the most effective").
# 4. Time horizons must match the lag ranges of the edges that were traversed.
```

On failure, loop back to `narrate` once with the specific failures listed. On the second failure, strip the offending sentences and append a note. **Log every rejection to Langfuse**, then put the aggregate in your README: "across the 30 evaluation scenarios the verifier caught 47 unsupported numeric claims, a 6.2 percent hallucination rate at the narration stage, all repaired before output."

That statistic alone is a better argument for your engineering than three paragraphs of prose.

### 14.5 Memory, three tiers

| Tier                | What it holds                                                              | Where it lives                                | Lifetime                          |
| ------------------- | -------------------------------------------------------------------------- | --------------------------------------------- | --------------------------------- |
| Conversation        | Message history, node state, clarification progress                        | LangGraph`PostgresSaver` on `checkpoints` | Session                           |
| Site profile        | The state vector with provenance, the AEZ, the geometry                    | `sites` and `site_states`                 | Permanent, reused across sessions |
| Intervention ledger | What the user actually adopted, what we predicted, what was later observed | `intervention_ledger`                       | Permanent                         |

The third tier is the MRV feature. When a user comes back after eight months and says "I planted the hedgerows in March," the system logs it against the frozen prediction and can later compare expected against observed. Even a stub implementation communicates that you understood what Darukaa actually does.

---

## 15. API Design

FastAPI, versioned under `/api/v1`, Pydantic models everywhere, SSE for streaming.

### 15.1 Endpoints

| Method   | Path                                      | Purpose                                                                           |
| -------- | ----------------------------------------- | --------------------------------------------------------------------------------- |
| `POST` | `/api/v1/sessions`                      | Create a session, optionally bound to an existing site                            |
| `POST` | `/api/v1/sessions/{id}/messages`        | Send a message. Returns SSE stream of tokens plus structured events.              |
| `GET`  | `/api/v1/sessions/{id}`                 | Full conversation state and current site vector                                   |
| `POST` | `/api/v1/sites`                         | Create a site from coordinates or manual values                                   |
| `GET`  | `/api/v1/sites/{id}/baseline`           | The enriched state vector with provenance per field                               |
| `POST` | `/api/v1/sites/{id}/simulate`           | Run the causal engine directly, bypassing chat. Takes a list of intervention ids. |
| `GET`  | `/api/v1/recommendations/{id}`          | Full recommendation with causal paths                                             |
| `GET`  | `/api/v1/recommendations/{id}/evidence` | Every claim cited, with verbatim spans and page numbers                           |
| `POST` | `/api/v1/ledger`                        | Record an adopted intervention                                                    |
| `POST` | `/api/v1/ledger/{id}/observations`      | Log a later field measurement                                                     |
| `GET`  | `/api/v1/knowledge/graph`               | The causal graph, for visualisation                                               |
| `POST` | `/api/v1/admin/ingest`                  | Trigger ingestion. Protected.                                                     |
| `GET`  | `/healthz`, `/readyz`                 | Liveness and readiness                                                            |

### 15.2 The structured output contract

Every recommendation returns this shape. It maps one to one onto the brief's output requirements.

```json
{
  "recommendation_id": "rec_a91f",
  "rank": 1,
  "intervention": {
    "id": "alley_agroforestry",
    "label": "Alley cropping with nitrogen fixing trees",
    "specifics": "Gliricidia sepium hedgerows at 6m spacing between wheat alleys, pruned twice yearly for green manure"
  },
  "why_it_works": "Nitrogen fixing hedgerows add 2 to 4 tonnes of biomass per hectare per year as prunings...",
  "causal_chain": [
    {"from": "intervention", "to": "soil_organic_carbon", "effect": "+0.35 pp", "edge_id": "agro_soc", "claims": ["clm_0012"]},
    {"from": "soil_organic_carbon", "to": "water_holding_capacity", "effect": "+1.1 mm/m", "edge_id": "soc_to_awc", "claims": ["clm_0043"]},
    {"from": "water_holding_capacity", "to": "soil_moisture", "effect": "+0.05 index", "edge_id": "awc_to_moisture", "claims": ["clm_0067"]}
  ],
  "impacted_metrics": [
    {
      "variable": "soil_organic_carbon",
      "baseline": 0.31,
      "projected_p10": 0.46,
      "projected_p50": 0.58,
      "projected_p90": 0.74,
      "unit": "percent",
      "horizon": "medium_term",
      "horizon_months": [24, 60]
    },
    {
      "variable": "pollinator_abundance",
      "baseline": 0.22,
      "projected_p50": 0.39,
      "horizon": "medium_term"
    }
  ],
  "baseline_vs_intervention": {
    "soil_organic_carbon": {"no_action_5yr": 0.28, "with_intervention_5yr": 0.58, "additionality": 0.30}
  },
  "time_horizon": "medium_term",
  "trade_offs": [
    {
      "variable": "groundwater_depth",
      "direction": "worsens",
      "magnitude": "+0.4 to +1.2 m over 5 years",
      "cause_path": ["canopy_cover", "groundwater_depth"],
      "mitigation": "Pair with contour bunding, or select low transpiration natives over eucalyptus"
    }
  ],
  "feasibility": {
    "capex_inr_per_ha": [15000, 45000],
    "labour_days_per_ha": [15, 30],
    "time_to_first_effect_months": 24,
    "reversibility": "low"
  },
  "confidence": {
    "score": 0.71,
    "band": "Medium-High",
    "limiting_factor": "input_completeness",
    "how_to_improve": "A soil texture test would raise this to approximately 0.82",
    "components": {
      "evidence_strength": 0.86,
      "transferability": 0.64,
      "input_completeness": 0.55,
      "path_directness": 0.78,
      "study_agreement": 0.81
    }
  },
  "evidence": [
    {
      "claim_id": "clm_0012",
      "source": "Kuyah et al. 2019, Agroforestry delivers ecosystem services",
      "page": 47,
      "verbatim": "Agroforestry increased soil organic carbon by 21 percent on average across 53 studies",
      "study_design": "meta_analysis",
      "n_studies": 53,
      "transferability_to_site": 0.64,
      "transferability_note": "Derived largely from sub-Saharan sites; discounted for South Asian semi-arid transfer"
    }
  ],
  "mrv_note": "SOC gain is claimable under Verra VM0042 with stratified sampling at 0-30cm, minimum 3 composite samples per stratum."
}
```

### 15.3 Streaming events

The SSE stream should emit typed events, not just tokens, so the frontend can show progress honestly:

```
event: stage      data: {"stage": "geo_enrich", "message": "Fetching soil data from SoilGrids"}
event: stage      data: {"stage": "simulate", "message": "Running 5000 Monte Carlo samples"}
event: token      data: {"text": "Based on"}
event: recommendation  data: { ...full object... }
event: done       data: {"session_id": "...", "verification_passed": true}
```

Watching the stages tick past is a surprisingly effective demo because it makes the depth of the pipeline visible.

---

## 16. Frontend

The brief says explicitly this is not a UI contest. So build three panels and nothing else. Next.js 15 App Router, Tailwind, MapLibre GL for the map. No component library beyond a few shadcn primitives.

### 16.1 Layout

```
+---------------------------+-------------------------------+
|                           |   SITE PANEL                  |
|   CHAT                    |   - map with the parcel       |
|                           |   - baseline table with       |
|   messages, streaming     |     provenance badges         |
|   stage indicators        |     (user / SoilGrids / GBIF) |
|                           +-------------------------------+
|                           |   REASONING TRACE             |
|                           |   - the causal chain as a     |
|                           |     small node diagram        |
|                           |   - click an edge to see the  |
|                           |     study behind it           |
+---------------------------+-------------------------------+
```

### 16.2 The one thing worth polishing

The **reasoning trace panel**. It is content, not decoration. Render the causal chain for the selected recommendation as a small left to right node diagram, with each edge labelled with its effect and each edge clickable to reveal the verbatim citation, the study design and the transferability score.

That panel is your entire thesis made visible: the reasoning is structural, the evidence is traceable, and nothing is a black box. It takes maybe four hours to build with React Flow and it is the thing a reviewer will screenshot.

### 16.3 Provenance badges

In the baseline table, colour code each value by provenance. Green for user provided, blue for fetched, amber for inferred, grey for unknown. One glance tells the user what the system actually knows versus what it assumed. Cheap to build, disproportionately convincing.

---

## 17. Evaluation Harness

The job description names AI evaluation as a responsibility. Almost nobody will ship this in a take-home, which is exactly why you should.

### 17.1 The golden set

`evals/golden_scenarios.yaml`, 30 site scenarios covering:

- 6 Indian agro-ecological zones, semi-arid to humid
- Degraded and healthy sites, so you can test that saturation works
- Complete and deliberately incomplete inputs, to test the clarification logic
- Text input, JSON input and coordinate-only input
- 3 adversarial cases: a site where the obvious answer is wrong (for example agroforestry where groundwater is already critical)

```yaml
- id: sc_007
  name: "Semi-arid Marathwada, degraded monoculture"
  input_mode: coordinates_plus_text
  coordinates: [19.15, 76.30]
  user_message: "My wheat yields keep dropping and I barely see bees anymore."
  known_context:
    crop: wheat_monoculture
    budget_inr_per_ha: 20000
  expected_intervention_families: [soil_management, water_management, habitat]
  must_not_recommend: [high_water_agroforestry]
  must_mention_variables: [soil_organic_carbon, soil_moisture, pollinator_abundance]
  min_variables_connected: 3
```

### 17.2 Metrics

| Metric                             | How it is measured                                                                             | Target |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- | ------ |
| **Citation faithfulness**    | Fraction of numeric claims in the final output that trace to a claim id or a simulation result | > 0.98 |
| **Verbatim integrity**       | Fraction of stored claims whose`verbatim_span` is found exactly in the source chunk          | 1.00   |
| **Retrieval recall@10**      | Against hand labelled relevant claims for each scenario                                        | > 0.80 |
| **Multi-variable coverage**  | Fraction of recommendations connecting 3 or more variables (the brief's hard requirement)      | 1.00   |
| **Non-obviousness**          | Fraction of recommendations not matching a banned generic phrase list                          | > 0.90 |
| **Trade-off surfacing**      | Fraction of adversarial scenarios where the known trade-off was flagged                        | > 0.85 |
| **Clarification efficiency** | Mean number of questions asked before a usable answer                                          | < 2.0  |
| **Constraint compliance**    | Fraction of recommendations respecting the stated budget and labour ceiling                    | 1.00   |
| **Latency p95**              | End to end, cached geo data                                                                    | < 12s  |

### 17.3 The banned phrase list

Non-obviousness is measurable if you define it. Keep a list in `evals/metrics/generic_phrases.txt`:

```
use sustainable practices
plant more trees
improve soil health
adopt organic farming
conserve water
maintain biodiversity
follow best practices
```

Any recommendation whose action text matches one of these without a specific species, spacing, quantity or timing attached fails the non-obviousness check. This is a crude heuristic and you should say so in the README, but a crude measured heuristic beats an unmeasured claim.

### 17.4 Wire it into CI

```makefile
eval:
	uv run python evals/run_eval.py --scenarios evals/golden_scenarios.yaml \
	    --output evals/reports/latest.json --fail-under 0.85
```

Then gate the GitHub Actions workflow on it. Commit the report. **Put the results table directly in the README.** A reviewer who sees measured numbers for your own system's faithfulness will read the rest of your repository very differently.

---

## 18. Local Setup

Target: a reviewer clones the repo and has it running in under five minutes with two commands. Test this on a clean machine before you submit, because a broken setup is the fastest way to lose a reviewer.

### 18.1 Prerequisites

- Docker and Docker Compose
- Python 3.12
- `uv`
- An OpenAI or Anthropic API key

### 18.2 Commands

```bash
git clone https://github.com/<you>/terrasense.git
cd terrasense

cp .env.example .env
# add your LLM key

make setup     # docker compose up -d, alembic upgrade head,
               # load variables/edges/interventions, restore the prebuilt
               # knowledge base dump, seed sample sites

make dev       # backend on :8000, frontend on :3000
```

### 18.3 Ship a prebuilt knowledge base dump

Do not make the reviewer run the full ingestion. It costs money and takes twenty minutes. Commit a `pg_dump` of the populated `documents`, `chunks`, `claims`, `causal_edges` and `interventions` tables (git-lfs if it is large) and restore it in `make setup`. Keep `make ingest` available for anyone who wants to rebuild from the PDFs.

This one decision is the difference between a reviewer seeing your system work and a reviewer seeing an error.

### 18.4 Environment variables

```bash
DATABASE_URL=postgresql+asyncpg://terrasense:terrasense@localhost:5432/terrasense
LLM_PROVIDER=openai
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
REASONING_MODEL=gpt-4o           # intake, narration
EXTRACTION_MODEL=gpt-4o-mini     # claim extraction, verification
IUCN_API_TOKEN=                  # optional
LANGFUSE_PUBLIC_KEY=             # optional
GEO_CACHE_TTL_DAYS=30
MONTE_CARLO_SAMPLES=5000
MONTE_CARLO_SEED=42
```

---

## 19. Deployment and CI/CD

### 19.1 Target

GCP, because the job description names it.

| Piece          | Service                                                              |
| -------------- | -------------------------------------------------------------------- |
| Backend        | Cloud Run, container, min instances 0, concurrency 20                |
| Database       | Cloud SQL for PostgreSQL 16 with`pgvector` and `postgis` enabled |
| Frontend       | Vercel (fastest) or Cloud Run                                        |
| Secrets        | Secret Manager, mounted as env vars                                  |
| Static rasters | Cloud Storage bucket                                                 |
| Ingestion jobs | Cloud Run Jobs, triggered manually                                   |

### 19.2 CI workflow

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy backend/app
      - run: uv run pytest -v --cov=backend/app --cov-fail-under=70
      - run: uv run python evals/run_eval.py --fail-under 0.85   # the eval gate
      - uses: actions/upload-artifact@v4
        with: { name: eval-report, path: evals/reports/ }
```

### 19.3 Deploy workflow

On a push to `main` that passes CI: build the image, push to Artifact Registry, run Alembic migrations as a Cloud Run Job, deploy the service, then hit `/readyz` as a smoke test and roll back on failure.

### 19.4 Testing strategy

| Type        | What it covers                                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| Unit        | The reasoning core. Deterministic, no network, no LLM. Fast and thorough, this is where most of your tests should live. |
| Contract    | External API clients, with recorded fixtures via`respx`. Never hit real APIs in CI.                                   |
| Integration | Retrieval against a small seeded database                                                                               |
| Agent       | Full graph runs with a stubbed LLM returning canned responses, asserting on the node path taken                         |
| Eval        | The golden set, run against the real LLM, nightly and on release                                                        |

Aim for high coverage on `backend/app/reasoning/`. That is the part whose correctness you are actually claiming.

---

## 20. Build Order

You will not finish everything. Build in this order so that whenever you stop, you have something coherent.

### Phase 1: The spine (highest value, do this first)

1. Docker Compose with Postgres, pgvector, postgis. Alembic baseline.
2. `variables.yaml` with all 12 variables.
3. **`edges.yaml` with 20 to 25 hand curated, hand cited edges.** This is the project. Do not rush it and do not generate it.
4. `interventions.yaml` with 12 to 15 interventions.
5. The reasoning core: propagation, transforms, Monte Carlo, trade-off detection. Fully unit tested.
6. A CLI that takes a JSON site and prints ranked recommendations. **No LLM yet, no API yet.**

At the end of Phase 1 you already have the thing that wins the assignment. Everything after this is delivery.

### Phase 2: Knowledge

7. Ingest 40 to 60 documents. Chunk, embed, extract claims.
8. Human review the claim queue. Link claim ids into your edges.
9. Hybrid retrieval plus transferability scoring.
10. Confidence scoring.

### Phase 3: Intelligence

11. LangGraph with all nodes. Postgres checkpointer.
12. Geo-enrichment: SoilGrids, Open-Meteo, GBIF first. WorldCover and GFW if time allows.
13. Gap analysis and VoI questioning.
14. The verifier node.

### Phase 4: Surface

15. FastAPI routes with SSE streaming.
16. Frontend: chat, map, reasoning trace.
17. Deploy to Cloud Run.

### Phase 5: Proof

18. The 30 golden scenarios.
19. The eval harness and the CI gate.
20. README with the results table, the architecture diagram and one full worked example.

### What to cut, in this order

Authentication. Multi user support. Any fine tuning. Frontend polish beyond the three panels. The India-WRIS and Bhuvan integrations. Extra documents beyond 60. The intervention ledger UI (keep the API and the table, skip the screens).

### What never to cut

The hand curated causal graph. The verifier. The evaluation harness. The worked example in the README. Those four are the entire argument for your submission.

---

## 21. Limitations and Next Steps

Write this section honestly in your final README. Reviewers read it first to find out whether you know what you do not know, and a candid limitations section reads as far more senior than an overclaimed feature list.

### Honest limitations

1. **The causal graph is hand curated and small.** 25 edges across 12 variables covers common agricultural interventions in Indian semi-arid and sub-humid zones well, and covers wetlands, coastal systems and high altitude ecosystems not at all.
2. **Effect sizes are linear or simply transformed approximations.** Real ecological responses have thresholds, hysteresis and regime shifts that this model does not capture.
3. **Attenuation per hop is a heuristic**, not a calibrated parameter. It is a reasonable way to express declining certainty with causal distance, but it is not derived from data.
4. **SoilGrids is a 250m model prediction, not a measurement.** Field variation within a single hectare can exceed the difference the system is reporting between scenarios.
5. **GBIF occurrence data is biased toward roads, protected areas and places where people with cameras go.** Low recorded richness may mean low sampling effort, not low biodiversity. The system should say so, and does.
6. **No temporal validation.** Predicted trajectories have not been checked against observed outcomes, because no such paired dataset was used.
7. **Claim extraction is LLM assisted with automated validation and partial human review.** Some extraction errors will remain in the store.

### What I would build next

1. **Remote sensing time series.** Pull Sentinel-2 NDVI and Landsat history for the parcel to establish a real observed baseline trend instead of assuming a static baseline. This is the single biggest accuracy upgrade available.
2. **Graph calibration against long term trial data.** Use ICAR NICRA and similar long term experiment datasets to fit the attenuation and effect parameters rather than asserting them.
3. **Regime shift modelling.** Add threshold edges for known tipping points such as salinisation and gully formation.
4. **Verifier-grade uncertainty.** Extend the Monte Carlo to account for measurement uncertainty in the site inputs as well as in the effect sizes, producing intervals that a credit auditor could interrogate.
5. **Field feedback loop.** Turn the intervention ledger into a live learning system where observed outcomes update the edge posteriors.
6. **Multilingual input.** Marathi and Hindi intake for actual farmer usage, since the intake node is the only LLM touchpoint that needs it.

---

## Appendix A: One Complete Worked Example

Put a version of this in your final README. One good end to end walkthrough communicates more than ten pages of description.

**User input:**

> "I have 4 hectares near 19.15, 76.30. Growing wheat every year. Soil looks dead and I haven't seen bees in two seasons. I can spend maybe 20 thousand rupees per hectare."

**Step 1, intake.** Parsed: coordinates present, area 4 ha, crop wheat monoculture, budget 20000 INR/ha, reported symptoms are soil degradation and pollinator loss.

**Step 2, geo-enrichment.** SoilGrids returns SOC 0.31 percent, pH 7.9, sandy loam. Open-Meteo returns 682mm mean annual rainfall, highly seasonal, aridity index 0.41 (semi-arid). GBIF returns 47 records in a 5km radius across 19 families, with only 2 pollinator records in the last 5 years. WorldCover shows 91 percent cropland, fragmentation index 0.78. AEZ lookup gives AEZ 6, Deccan Plateau hot semi-arid. **Nine of twelve variables populated automatically.**

**Step 3, gap analysis.** Missing: current tillage practice, groundwater depth, slope. VoI ranking says groundwater depth matters most, because it gates whether agroforestry is safe. System asks one question:

> "One thing would change my answer a lot: roughly how deep is your borewell water level now, and has it dropped in recent years? It decides whether tree based options are safe here or would make your water problem worse."

**User replies:** "About 18 metres, it's gone down maybe 4 metres in 6 years."

**Step 4, candidates.** 15 interventions filtered to 6. Alley agroforestry is retained but flagged, because `excluded_when.groundwater_depth_m_min: 15` triggers.

**Step 5, retrieval.** Structured filter on AEZ 6 plus sandy loam plus low rainfall returns 34 claims. Semantic search adds 11 narrative chunks. Transferability scores range from 0.42 (temperate European trials) to 0.88 (ICAR Deccan plateau trials), and the effect sizes are discounted accordingly.

**Step 6, simulation.** 5000 Monte Carlo samples per candidate. Legume cover cropping plus contour bunding plus field margin hedgerows emerges as the strongest combination under the budget ceiling. Alley agroforestry scores well on biodiversity but its trade-off edge to groundwater depth triggers.

**Step 7, ranking and output.** Top recommendation:

> **1. Legume cover cropping with contour bunding, combined.**
>
> Sow horsegram or cowpea in the post-wheat fallow, and cut contour bunds on the 3 percent slope before the monsoon.
>
> **Why it works:** The bunds hold monsoon runoff long enough for infiltration, which raises soil moisture in the dry months. That moisture is what lets the legume residue actually decompose into stable carbon rather than blowing away. Cover crop alone on this soil at 0.31 percent SOC would build carbon slowly because decomposition is moisture limited. The two together are worth more than the sum of the parts, and that interaction is the reason this pairing is ranked above either one alone.
>
> **Projected changes over 3 years:**
>
> | Metric               | Now   | No action | With intervention | Gain             |
> | -------------------- | ----- | --------- | ----------------- | ---------------- |
> | Soil organic carbon  | 0.31% | 0.29%     | 0.47 to 0.61%     | +0.18 to 0.32 pp |
> | Soil moisture index  | 0.24  | 0.22      | 0.33 to 0.41      | +0.11 to 0.19    |
> | Pollinator abundance | 0.15  | 0.14      | 0.21 to 0.29      | +0.07 to 0.15    |
> | Soil biota activity  | 0.19  | 0.18      | 0.34 to 0.46      | +0.16 to 0.28    |
>
> **Time horizon:** short to medium. First soil moisture effect in one monsoon, carbon gain measurable from year 2.
>
> **Cost:** approximately 10,000 to 31,000 INR per hectare in year one, of which bunding is a one time cost. Within your stated budget if bunding is phased across two seasons.
>
> **Trade-off:** pollinator gain from cover crops alone is modest, because your landscape is 91 percent cropland with a fragmentation index of 0.78. Bees need continuous forage, not one flowering window. This is why recommendation 2 (field margin hedgerows) matters more than it looks.
>
> **Confidence: Medium-High (0.74).** Limited by input completeness, since tillage practice is unknown. Evidence includes 2 meta-analyses and 3 ICAR Deccan plateau trials with transferability 0.81 to 0.88.
>
> **Evidence:** Poeplau and Don 2015, p.38, cover crops increased SOC stocks by 0.32 tonnes C per hectare per year across 139 plots, meta-analysis, transferability 0.71. ICAR-CRIDA Contingency Plan Beed District, p.12, transferability 0.88.
>
> **MRV note:** The soil carbon gain here is claimable under Verra VM0042 with stratified sampling at 0 to 30cm.

**Step 8, verification.** 14 numeric claims in the draft. All 14 traced to simulation output or claim ids. Passed on the first attempt.

**And the deliberately withheld recommendation:**

> **Not recommended: alley agroforestry.** It would score highest on biodiversity gain, but your water table is at 18 metres and falling roughly 0.7 metres a year. Adding tree transpiration demand is projected to deepen it a further 0.4 to 1.2 metres over 5 years. Revisit this once the bunding has stabilised recharge, likely in year 3 or 4.

Showing what you decided *not* to recommend, and why, is the clearest possible demonstration of multi-variable reasoning. Make sure your system does this, and make sure your demo shows it.
