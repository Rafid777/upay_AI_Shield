"""
upay AI Shield - Scam Pattern Intelligence Routes
Evaluates multi-signal scam patterns against transaction telemetry and customer baselines.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction
from backend.schemas import ScamIntelligenceResponse
from backend.services.scam_service import scam_service
from backend.services.behavioral_service import behavioral_service

router = APIRouter(prefix="/transactions", tags=["Scam Pattern Intelligence"])


@router.get("/{transaction_id}/scam-intelligence", response_model=ScamIntelligenceResponse)
def get_scam_intelligence(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Evaluates empirical scam pattern indicators for a specific transaction.
    Detects patterns like UNUSUAL_HIGH_VALUE_TRANSFER, NEW_RECEIVER_TRANSFER,
    RAPID_REPEATED_TRANSFERS, NEW_DEVICE_TRANSFER, etc.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )

    cust_id = tx.customer_id or "CUST_DEFAULT"
    baseline = behavioral_service.get_customer_baseline(db, cust_id)

    tx_dict = {
        "transaction_id": tx.transaction_id,
        "customer_id": tx.customer_id,
        "amount": tx.amount,
        "hour": tx.hour,
        "is_new_receiver": tx.is_new_receiver,
        "is_new_device": tx.is_new_device,
        "location_changed": tx.location_changed,
        "transactions_last_1h": tx.transactions_last_1h,
        "transactions_last_24h": tx.transactions_last_24h,
        "failed_attempts": tx.failed_attempts,
        "amount_deviation": tx.amount_deviation,
        "channel": tx.channel
    }

    res = scam_service.analyze_scam_patterns(tx_dict, baseline)
    return res
