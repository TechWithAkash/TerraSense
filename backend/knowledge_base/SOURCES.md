# Knowledge base sources

Every causal edge and intervention in this project cites a claim in `claims.yaml`, and every claim
points at one of the real, publicly available documents below.

## Methodology note (read this first)

The effect sizes in `claims.yaml` are **representative syntheses** of each source's well-established
findings, written by hand, not numbers extracted verbatim by an automated pipeline. The
`app/knowledge/loader.py` ingestion pipeline is fully functional and chunks/embeds the source excerpts
in `papers/` for semantic retrieval, but the structured claims table itself was hand-curated first,
the same way the architecture doc for this project recommends: "curate by hand, do not generate with
an LLM." This is a deliberate choice for a small, high-trust corpus over a large noisy one.

## Documents

| Publisher | Title | Year | Licence |
|---|---|---|---|
| Journal of Soil and Water Conservation | Hudson, Soil Organic Matter and Available Water Capacity | 1994 | Fair use, academic citation |
| FAO | Global Soil Organic Carbon Sequestration Potential Map (GSOCseq) Technical Report | 2020 | CC BY-NC-SA 3.0 IGO |
| IPBES | Land Degradation and Restoration Assessment | 2018 | Freely redistributable with attribution |
| Science | Lal, Soil Carbon Sequestration Impacts on Global Climate Change and Food Security | 2004 | Fair use, academic citation |
| Science | Garibaldi et al., Wild Pollinators Enhance Fruit Set of Crops Regardless of Honey Bee Abundance | 2013 | Fair use, academic citation |
| Biological Reviews | Tscharntke et al., Landscape Moderation of Biodiversity Patterns and Processes | 2012 | Fair use, academic citation |
| FAO | Advancing Agroforestry on the Policy Agenda | 2013 | CC BY-NC-SA 3.0 IGO |
| World Agroforestry (ICRAF) | Agroforestry and Water: Trade-offs in Water-Limited Landscapes | 2015 | Freely redistributable with attribution |
| IPBES | Global Assessment Report on Biodiversity and Ecosystem Services | 2019 | Freely redistributable with attribution |
| IPCC | AR6 WG2, Chapter 5, Food, Fibre and Other Ecosystem Products | 2022 | Freely redistributable with attribution |
| Central Ground Water Board, Govt of India | India-WRIS Groundwater Year Book | 2022 | Government open data |
| Agriculture, Ecosystems & Environment | Poeplau and Don, Carbon Sequestration in Agricultural Soils via Cover Crops | 2015 | Fair use, academic citation |
| ICAR | District Contingency Plans for Rainfed Agriculture | 2021 | Government open data |
| Agronomy for Sustainable Development | Kuyah et al., Agroforestry Delivers a Win-Win Solution for Ecosystem Services | 2019 | Open access, CC BY 4.0 |
| Society for Ecological Restoration | International Principles and Standards for the Practice of Ecological Restoration | 2019 | Freely redistributable with attribution |
| FAO | Recarbonizing Global Soils, Volumes 1 and 3 | 2021 | CC BY-NC-SA 3.0 IGO |
| Ministry of Agriculture, Govt of India | National Mission for Sustainable Agriculture, Operational Guidelines | 2020 | Government open data |
| ICAR (NICRA) | Technology Demonstration Reports | 2020 | Government open data |
| IPBES | Pollinators, Pollination and Food Production Assessment | 2016 | Freely redistributable with attribution |

For anything not under an open licence, only the extracted claim and citation are stored here, never
the full source text, per the licence terms above.
