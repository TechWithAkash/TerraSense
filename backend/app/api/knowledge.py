from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.knowledge.search import get_chunk_index
from app.models import CausalEdge, Claim, Intervention, Variable

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/graph")
def get_graph(db: Session = Depends(get_db)) -> dict:
    # exposes the causal graph itself, so the "how knowledge is retrieved and used" requirement
    # is answerable by hitting an endpoint, not just reading source code
    variables = db.query(Variable).all()
    edges = db.query(CausalEdge).all()
    return {
        "variables": [
            {
                "id": v.id,
                "label": v.label,
                "unit": v.unit,
                "category": v.category,
                "higher_is_worse": v.higher_is_worse,
            }
            for v in variables
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source_variable,
                "target": e.target_variable,
                "sign": e.sign,
                "confidence_tier": e.confidence_tier,
                "evidence_claim_ids": e.evidence_claim_ids,
                "notes": e.notes,
            }
            for e in edges
        ],
    }


@router.get("/interventions")
def list_interventions(db: Session = Depends(get_db)) -> list[dict]:
    interventions = db.query(Intervention).all()
    return [
        {
            "id": i.id,
            "label": i.label,
            "category": i.category,
            "reversibility": i.reversibility,
            "cost": i.cost,
        }
        for i in interventions
    ]


@router.get("/claims/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)) -> dict:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "id": claim.id,
        "document": claim.document,
        "publisher": claim.publisher,
        "year": claim.year,
        "study_design": claim.study_design,
        "target_variable": claim.target_variable,
        "source_variable": claim.source_variable,
        "intervention_id": claim.intervention_id,
        "summary": claim.summary,
    }


@router.get("/search")
def search_knowledge(q: str = Query(..., min_length=2), top_k: int = 5) -> dict:
    results = get_chunk_index().search(q, top_k=top_k)
    return {"query": q, "results": [r.__dict__ for r in results]}
