"""
upay AI Shield - Customer Profile & Behavior Intelligence Routes
Provides endpoints for Customer Behavioral Baseline vs Current Deviations, and Entity Network Graphs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Customer, Transaction
from backend.services.behavioral_service import behavioral_service
from backend.services.network_service import network_service

router = APIRouter(prefix="/customers", tags=["Customer Intelligence & Behavior"])


@router.get("/{customer_id}/behavior")
def get_customer_behavior_profile(
    customer_id: str,
    transaction_id: Optional[str] = Query(None, description="Optional transaction ID to compare current vs baseline"),
    db: Session = Depends(get_db)
):
    """
    Returns empirical customer baseline profile, latest transaction telemetry,
    and computed behavioral deviations.
    """
    cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    # Query customer's recent transactions
    tx_query = db.query(Transaction).filter(Transaction.customer_id == customer_id).order_by(Transaction.timestamp.desc())
    txs = tx_query.limit(10).all()

    if not cust and not txs:
        # Check if customer exists in general
        first_tx = db.query(Transaction).first()
        if first_tx:
            customer_id = first_tx.customer_id
            txs = db.query(Transaction).filter(Transaction.customer_id == customer_id).order_by(Transaction.timestamp.desc()).limit(10).all()
            cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found."
            )

    baseline = behavioral_service.get_customer_baseline(db, customer_id)

    # Determine current transaction for comparison
    current_tx = None
    if transaction_id:
        current_tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not current_tx and txs:
        current_tx = txs[0]

    current_data = None
    deviations = None
    if current_tx:
        current_data = {
            "transaction_id": current_tx.transaction_id,
            "amount": float(current_tx.amount),
            "amount_display": f"৳{float(current_tx.amount):,.2f}",
            "hour": int(current_tx.hour),
            "hour_display": f"{int(current_tx.hour):02d}:00",
            "device": "NEW / UNSEEN" if current_tx.is_new_device else (current_tx.device_id or "Known Device"),
            "receiver": "NEW / UNSEEN" if current_tx.is_new_receiver else (current_tx.receiver_id or "Known Receiver"),
            "location": current_tx.location or "Standard Location",
            "location_status": "CHANGED" if current_tx.location_changed else "NORMAL",
            "velocity_1h": int(current_tx.transactions_last_1h),
            "velocity_display": f"{int(current_tx.transactions_last_1h)}/hour",
            "is_new_device": bool(current_tx.is_new_device),
            "is_new_receiver": bool(current_tx.is_new_receiver),
            "location_changed": bool(current_tx.location_changed)
        }
        deviations = behavioral_service.compute_behavioral_deviation(baseline, {
            "amount": current_tx.amount,
            "hour": current_tx.hour,
            "is_new_device": current_tx.is_new_device,
            "is_new_receiver": current_tx.is_new_receiver,
            "location_changed": current_tx.location_changed,
            "transactions_last_1h": current_tx.transactions_last_1h,
            "transactions_last_24h": current_tx.transactions_last_24h,
            "failed_attempts": current_tx.failed_attempts,
            "location": current_tx.location
        })

    recent_list = []
    for t in txs:
        recent_list.append({
            "transaction_id": t.transaction_id,
            "amount": float(t.amount),
            "amount_display": f"৳{float(t.amount):,.2f}",
            "channel": t.channel,
            "transaction_type": t.transaction_type,
            "hour": t.hour,
            "timestamp": t.timestamp,
            "receiver_id": t.receiver_id,
            "device_id": t.device_id,
            "location": t.location,
            "risk_score": float(t.demo_risk_score if t.demo_risk_score else 25.0),
            "risk_level": t.risk_level or "LOW"
        })

    return {
        "customer_id": customer_id,
        "account_age_days": cust.account_age_days if cust else baseline.get("account_age_days", 365),
        "normal_behavior": {
            "average_amount": baseline.get("average_amount", 1250.0),
            "average_amount_display": f"৳{baseline.get('average_amount', 1250.0):,.2f}",
            "typical_hours": baseline.get("typical_hours", "08:00–22:00"),
            "known_devices_count": baseline.get("known_devices_count", 1),
            "known_devices": baseline.get("known_devices", []),
            "known_receivers_count": baseline.get("known_receivers_count", 1),
            "known_receivers": baseline.get("known_receivers", []),
            "average_daily_transactions": baseline.get("typical_daily_frequency", 4.0),
            "normal_locations": [baseline.get("primary_location", "Dhaka")],
            "average_velocity_1h": "1-2 / hour"
        },
        "current_transaction": current_data,
        "behavioral_deviations": deviations,
        "recent_transactions": recent_list
    }


@router.get("/{customer_id}/network")
def get_customer_network(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns multi-hop graph nodes and edges around the customer,
    including linked devices, receivers, locations, and other connected customers.
    """
    net = network_service.get_customer_network(db=db, customer_id=customer_id)
    return net
