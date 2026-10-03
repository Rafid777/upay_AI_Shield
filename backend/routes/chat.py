"""
upay AI Shield - Chat API Route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import ChatRequest, ChatResponse
from backend.services.investigation_service import investigation_service

router = APIRouter(prefix="/chat", tags=["AI Investigation Assistant"])


@router.post("", response_model=ChatResponse)
def chat_with_assistant(
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Interactive Q&A assistant for fraud analysts.
    Answers case-specific inquiries using transaction evidence and SHAP explainability.
    """
    try:
        res = investigation_service.chat_with_assistant(
            db=db,
            transaction_id=payload.transaction_id,
            message=payload.message
        )
        return ChatResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )
