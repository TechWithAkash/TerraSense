import re

import yaml
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CausalEdge, Chunk, Claim, Intervention, Variable

settings = get_settings()

# section-aware-ish chunking: split on markdown headings first, then cap chunk size.
# good enough for a handful of short excerpt documents without pulling in a PDF layout parser.
_HEADING_PATTERN = re.compile(r"^#{1,3}\s+.+$", re.MULTILINE)
MAX_CHUNK_CHARS = 1200


def _split_into_chunks(text: str) -> list[str]:
    sections = _HEADING_PATTERN.split(text)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= MAX_CHUNK_CHARS:
            chunks.append(section)
            continue
        # a long section still gets split further, on paragraph boundaries
        paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) > MAX_CHUNK_CHARS and buffer:
                chunks.append(buffer.strip())
                buffer = paragraph
            else:
                buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if buffer:
            chunks.append(buffer.strip())
    return chunks


def load_knowledge_base(db: Session) -> dict[str, int]:
    kb_dir = settings.knowledge_base_dir
    counts = {"variables": 0, "edges": 0, "interventions": 0, "claims": 0, "chunks": 0}

    variables_yaml = yaml.safe_load((kb_dir / "variables.yaml").read_text())
    for entry in variables_yaml["variables"]:
        typical_range = entry.get("typical_range", [None, None])
        db.merge(
            Variable(
                id=entry["id"],
                label=entry["label"],
                unit=entry["unit"],
                category=entry["category"],
                typical_low=typical_range[0],
                typical_high=typical_range[1],
                higher_is_worse=entry.get("higher_is_worse", False),
                derived=entry.get("derived", False),
            )
        )
        counts["variables"] += 1

    edges_yaml = yaml.safe_load((kb_dir / "edges.yaml").read_text())
    for entry in edges_yaml["edges"]:
        effect = entry["effect"]
        db.merge(
            CausalEdge(
                id=entry["id"],
                source_variable=entry["source"],
                target_variable=entry["target"],
                sign=entry["sign"],
                per_unit_source=effect["per_unit_source"],
                delta_low=effect["delta_low"],
                delta_mid=effect["delta_mid"],
                delta_high=effect["delta_high"],
                unit=effect["unit"],
                transform=entry.get("transform", "linear"),
                saturation_point=entry.get("saturation_point"),
                context=entry.get("context", {}),
                confidence_tier=entry.get("confidence_tier", "medium"),
                evidence_claim_ids=entry.get("evidence_claim_ids", []),
                notes=entry.get("notes"),
            )
        )
        counts["edges"] += 1

    interventions_yaml = yaml.safe_load((kb_dir / "interventions.yaml").read_text())
    for entry in interventions_yaml["interventions"]:
        labour = entry.get("labour_days_per_ha", [None, None])
        db.merge(
            Intervention(
                id=entry["id"],
                label=entry["label"],
                category=entry["category"],
                direct_effects=entry["direct_effects"],
                applicable_when=entry.get("applicable_when", {}),
                excluded_when=entry.get("excluded_when", {}),
                cost=entry.get("cost", {}),
                labour_days_low=labour[0],
                labour_days_high=labour[1],
                time_to_first_effect_months=entry.get("time_to_first_effect_months"),
                reversibility=entry.get("reversibility", "medium"),
                trade_off_species_group=entry.get("trade_off_species_group"),
            )
        )
        counts["interventions"] += 1

    claims_yaml = yaml.safe_load((kb_dir / "claims.yaml").read_text())
    for entry in claims_yaml["claims"]:
        db.merge(
            Claim(
                id=entry["id"],
                document=entry["document"],
                publisher=entry["publisher"],
                year=entry["year"],
                study_design=entry["study_design"],
                target_variable=entry["target_variable"],
                source_variable=entry.get("source_variable"),
                intervention_id=entry.get("intervention_id"),
                n_studies=entry.get("n_studies"),
                summary=entry["summary"],
                context=entry.get("context", {}),
            )
        )
        counts["claims"] += 1

    db.query(Chunk).delete()  # chunks are cheap to rebuild, always regenerate from source on load
    papers_dir = kb_dir / "papers"
    for paper_path in sorted(papers_dir.glob("*.md")):
        text = paper_path.read_text()
        title = text.splitlines()[0].lstrip("# ").strip()
        for index, chunk_text in enumerate(_split_into_chunks(text)):
            db.add(
                Chunk(
                    source_file=paper_path.name, title=title, content=chunk_text, chunk_index=index
                )
            )
            counts["chunks"] += 1

    db.commit()
    return counts
