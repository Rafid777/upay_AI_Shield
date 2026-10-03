"""
upay AI Shield V3 - Live Risk Stream & Alert Center Routes
Provides endpoints for Simulated Live Stream and Risk Alert Center.
All live streams are explicitly labeled: 'SIMULATED LIVE STREAM'.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction
from backend.services.risk_fusion_service import risk_fusion

router = APIRouter(tags=["Live Stream & Alert Center"])


@router.get("/stream/live")
def get_live_risk_stream(
    limit: int = Query(15, ge=5, le=50),
    db: Session = Depends(get_db)
):
    """
    Returns an active simulated live transaction monitoring stream.
    Explicitly labeled as 'SIMULATED LIVE STREAM'.
    """
    # Fetch recent transactions
    txs = db.query(Transaction).order_by(Transaction.id.desc()).limit(limit).all()

    items = []
    for t in txs:
        # Determine main risk signal
        dev = float(t.amount_deviation or 1.0)
        is_new_dev = int(t.is_new_device or 0) == 1
        is_new_rec = int(t.is_new_receiver or 0) == 1
        hour = int(t.hour or 12)
        vel = int(t.transactions_last_1h or 1)

        signals = []
        if dev >= 5.0:
            signals.append(f"Surge ({dev:.1f}x)")
        if is_new_dev:
            signals.append("New Device")
        if is_new_rec and dev >= 2.0:
            signals.append("New Recipient")
        if 0 <= hour <= 5:
            signals.append("Nocturnal")
        if vel >= 5:
            signals.append(f"Burst ({vel}/h)")

        main_signal = " + ".join(signals[:2]) if signals else "Standard Transfer"
        score = float(t.demo_risk_score if t.demo_risk_score is not None else 10.0)

        items.append({
            "transaction_id": t.transaction_id,
            "amount": float(t.amount),
            "amount_display": f"৳{float(t.amount):,.2f}",
            "customer_id": t.customer_id,
            "channel": t.channel,
            "transaction_type": t.transaction_type,
            "risk_score": score,
            "risk_level": t.risk_level or "LOW",
            "main_signal": main_signal,
            "location": t.location,
            "timestamp": str(t.timestamp)
        })

    return {
        "stream_type": "SIMULATED LIVE STREAM",
        "stream_status": "ONLINE",
        "label": "SIMULATED LIVE STREAM (Prototype using historical synthetic baseline records)",
        "count": len(items),
        "transactions": items
    }


@router.get("/alerts")
def get_risk_alert_center(
    category: Optional[str] = Query(None, description="Filter by CRITICAL, HIGH, or MEDIUM"),
    limit: int = Query(20, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized operational fraud alerts categorized as CRITICAL, HIGH, or MEDIUM.
    Each alert directly links to investigation and formal case escalation.
    """
    # Query high and medium risk transactions
    txs = db.query(Transaction).filter(
        Transaction.risk_level.in_(["HIGH", "MEDIUM"])
    ).order_by(Transaction.id.desc()).limit(limit * 2).all()

    alerts = []
    for idx, t in enumerate(txs):
        score = float(t.demo_risk_score or 85.0)
        dev = float(t.amount_deviation or 1.0)
        is_new_dev = int(t.is_new_device or 0) == 1
        hour = int(t.hour or 12)
        vel = int(t.transactions_last_1h or 1)
        fails = int(t.failed_attempts or 0)

        # Categorize
        if is_new_dev and fails >= 2 and (0 <= hour <= 5 or dev >= 4.0):
            cat = "CRITICAL"
            title = "Potential Account Takeover Pattern"
            desc = f"Unregistered device login preceded by {fails} failed attempts during off-hours with {dev:.1f}x amount surge."
        elif dev >= 8.0 or float(t.amount) >= 40000.0:
            cat = "CRITICAL" if score >= 95.0 else "HIGH"
            title = "Unusual High-Value Transfer Pattern"
            desc = f"Substantial outflow of ৳{float(t.amount):,.2f} exceeding normal customer baseline by {dev:.1f}x."
        elif is_new_dev and int(t.is_new_receiver or 0) == 1:
            cat = "HIGH"
            title = "Unregistered Device to New Beneficiary"
            desc = "First-time transfer initiated from a novel hardware identifier to an unverified recipient."
        elif vel >= 5:
            cat = "HIGH"
            title = "Rapid Successive Transfer Surge"
            desc = f"{vel} transactions initiated within 60 minutes, characteristic of automated account drain."
        elif 0 <= hour <= 5 or int(t.location_changed or 0) == 1:
            cat = "MEDIUM"
            title = "Circadian / Geographic Telemetry Anomaly"
            desc = f"Session initiated at {hour:02d}:00 or from a distant geographic division ({t.location})."
        else:
            cat = "MEDIUM"
            title = "Behavioral Deviation Flag"
            desc = f"Transaction parameters exceed typical statistical baseline (Score: {score:.1f})."

        if category and category.upper() != "ALL" and cat != category.upper():
            continue

        alerts.append({
            "alert_id": f"ALT-{10000 + t.id}",
            "category": cat,
            "title": title,
            "description": desc,
            "transaction_id": t.transaction_id,
            "customer_id": t.customer_id,
            "amount": float(t.amount),
            "amount_display": f"৳{float(t.amount):,.2f}",
            "risk_score": score,
            "risk_level": t.risk_level,
            "channel": t.channel,
            "timestamp": str(t.timestamp)
        })

        if len(alerts) >= limit:
            break

    # Summary counts
    crit_count = sum(1 for a in alerts if a["category"] == "CRITICAL")
    high_count = sum(1 for a in alerts if a["category"] == "HIGH")
    med_count = sum(1 for a in alerts if a["category"] == "MEDIUM")

    return {
        "total_alerts": len(alerts),
        "counts": {
            "critical": crit_count,
            "high": high_count,
            "medium": med_count
        },
        "alerts": alerts
    }
