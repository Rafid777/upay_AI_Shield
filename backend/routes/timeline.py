"""
upay AI Shield - Risk Story & Timeline Routes
Generates chronological event narratives explaining why a transaction was flagged.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction, RiskPrediction
from backend.schemas import RiskStoryResponse
from backend.services.timeline_service import timeline_service

router = APIRouter(prefix="/transactions", tags=["Risk Story & Timeline"])


@router.get("/{transaction_id}/risk-story", response_model=RiskStoryResponse)
def get_transaction_risk_story(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Constructs a chronological forensic timeline and narrative explanation
    from customer history and transaction telemetry.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )

    # Determine risk score and level
    pred = db.query(RiskPrediction).filter(RiskPrediction.transaction_id == transaction_id).first()
    score = pred.risk_score if pred else float(tx.demo_risk_score or 75.0)
    level = pred.risk_level if pred else (tx.risk_level or "HIGH")

    story = timeline_service.generate_risk_story(
        db=db,
        transaction_id=transaction_id,
        risk_score=score,
        risk_level=level
    )
    return story
