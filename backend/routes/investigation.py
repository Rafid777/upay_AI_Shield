"""
upay AI Shield - Investigation API Route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import InvestigateRequest, InvestigationResponse
from backend.services.investigation_service import investigation_service

router = APIRouter(prefix="/investigate", tags=["AI Investigation Assistant"])


@router.post("", response_model=InvestigationResponse)
def trigger_ai_investigation(
    payload: InvestigateRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers Gemini AI Investigation Assistant on a flagged transaction.
    Synthesizes transaction facts, XGBoost probability, and SHAP explainability factors.
    """
    try:
        result = investigation_service.investigate_transaction(db, payload.transaction_id)
        return InvestigationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation error: {str(e)}"
        )
