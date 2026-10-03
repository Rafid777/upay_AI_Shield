"""
upay AI Shield - Network & Graph Intelligence API Route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Transaction
from backend.services.network_service import network_service

router = APIRouter(prefix="/network", tags=["Network & Entity Intelligence"])


@router.get("/graph/{transaction_id}")
def get_transaction_graph(transaction_id: str, db: Session = Depends(get_db)):
    """
    Returns localized multi-entity relationship graph (Customer, Receiver, Device, Location)
    and automated coordinated activity insights for a transaction.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction '{transaction_id}' not found.")
    
    return network_service.get_transaction_entity_network(db, transaction_id)


@router.get("/patterns")
def get_global_network_patterns(db: Session = Depends(get_db)):
    """
    Identifies high-fan-in beneficiaries and cross-account shared hardware devices across the dataset.
    """
    # Beneficiaries with highest number of distinct customer senders
    top_receivers = db.query(
        Transaction.receiver_id,
        func.count(func.distinct(Transaction.customer_id)).label("unique_senders"),
        func.count(Transaction.transaction_id).label("tx_count"),
        func.sum(Transaction.amount).label("total_volume")
    ).group_by(Transaction.receiver_id).having(
        func.count(func.distinct(Transaction.customer_id)) >= 3
    ).order_by(
        func.count(func.distinct(Transaction.customer_id)).desc()
    ).limit(8).all()

    # Devices shared across multiple customer accounts
    shared_devices = db.query(
        Transaction.device_id,
        func.count(func.distinct(Transaction.customer_id)).label("unique_users"),
        func.count(Transaction.transaction_id).label("tx_count")
    ).group_by(Transaction.device_id).having(
        func.count(func.distinct(Transaction.customer_id)) >= 2
    ).order_by(
        func.count(func.distinct(Transaction.customer_id)).desc()
    ).limit(8).all()

    return {
        "high_fan_in_beneficiaries": [
            {
                "receiver_id": r[0],
                "unique_senders_count": int(r[1]),
                "transaction_count": int(r[2]),
                "total_volume": round(float(r[3] or 0), 2),
                "pattern": "Potential Coordinated Inflow"
            } for r in top_receivers
        ],
        "cross_account_shared_devices": [
            {
                "device_id": d[0],
                "unique_users_count": int(d[1]),
                "transaction_count": int(d[2]),
                "pattern": "Multi-Account Device Reuse"
            } for d in shared_devices
        ],
        "disclaimer": "Automated network heuristics for triage. Does not confirm criminality or illicit behavior."
    }
