from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.knowledge.search import ScoredChunk, get_chunk_index
from app.models import Claim

# retrieval runs structured SQL first, semantic search second.
# a SQL filter on target_variable finds exactly the claims that apply, with perfect precision.
# semantic search over the chunk text fills in narrative context the structured filter might miss.


@dataclass
class EvidenceBundle:
    claims: list[Claim]
    supporting_chunks: list[ScoredChunk]


def structured_claims_for_intervention(db: Session, intervention_id: str) -> list[Claim]:
    return db.query(Claim).filter(Claim.intervention_id == intervention_id).all()


def structured_claims_for_edge_target(
    db: Session, target_variable: str, claim_ids: list[str]
) -> list[Claim]:
    if not claim_ids:
        return []
    return db.query(Claim).filter(Claim.id.in_(claim_ids)).all()


def semantic_search(query: str, top_k: int = 3) -> list[ScoredChunk]:
    return get_chunk_index().search(query, top_k=top_k)


def gather_evidence(db: Session, intervention_id: str, intervention_label: str) -> EvidenceBundle:
    claims = structured_claims_for_intervention(db, intervention_id)
    chunks = semantic_search(intervention_label, top_k=3)
    return EvidenceBundle(claims=claims, supporting_chunks=chunks)


def claims_by_ids(db: Session, claim_ids: list[str]) -> list[Claim]:
    if not claim_ids:
        return []
    return db.query(Claim).filter(Claim.id.in_(claim_ids)).all()
