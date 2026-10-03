"""
upay AI Shield - Analyst Feedback API Route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import AnalystFeedback, Transaction
from backend.schemas import FeedbackCreate, FeedbackResponse, FeedbackStatsResponse

router = APIRouter(prefix="/feedback", tags=["Human Feedback Loop"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_analyst_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submits human analyst review decision and feedback for a monitored transaction.
    Allowed decisions: SUSPICIOUS, LEGITIMATE, NEEDS_REVIEW.
    Recorded in database for governance audit trails and future active learning retrains.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == payload.transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{payload.transaction_id}' does not exist in records."
        )

    # Use comment or reason interchangeably
    reason_text = payload.reason or payload.comment or ""

    feedback_record = AnalystFeedback(
        transaction_id=payload.transaction_id,
        predicted_risk=payload.predicted_risk or tx.demo_risk_score,
        predicted_level=payload.predicted_level or tx.risk_level,
        decision=payload.decision,
        comment=reason_text,
        reason=reason_text,
        analyst_id=payload.analyst_id or "lead_analyst_1"
    )

    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)

    return FeedbackResponse.model_validate(feedback_record)


@router.get("/stats", response_model=FeedbackStatsResponse)
def get_feedback_stats(db: Session = Depends(get_db)):
    """Retrieves aggregated analyst decision statistics and recent reviews."""
    total = db.query(AnalystFeedback).count()
    suspicious = db.query(AnalystFeedback).filter(AnalystFeedback.decision.in_(["SUSPICIOUS", "CONFIRM_SUSPICIOUS"])).count()
    legitimate = db.query(AnalystFeedback).filter(AnalystFeedback.decision.in_(["LEGITIMATE", "MARK_LEGITIMATE"])).count()
    needs_review = db.query(AnalystFeedback).filter(AnalystFeedback.decision.in_(["NEEDS_REVIEW", "NEEDS_MORE_INVESTIGATION"])).count()

    recent = db.query(AnalystFeedback).order_by(AnalystFeedback.created_at.desc()).limit(15).all()

    return FeedbackStatsResponse(
        total_reviewed=total,
        confirmed_suspicious=suspicious,
        marked_legitimate=legitimate,
        needs_investigation=needs_review,
        suspicious_rate_pct=round(suspicious / max(total, 1) * 100, 2),
        recent_feedbacks=[FeedbackResponse.model_validate(f) for f in recent]
    )


@router.post("/export")
def export_feedback_dataset(db: Session = Depends(get_db)):
    """
    Exports analyst-reviewed transactions and labels into a CSV dataset
    for offline model retraining and validation.
    """
    import csv
    import io
    from fastapi.responses import Response

    feedbacks = db.query(AnalystFeedback).order_by(AnalystFeedback.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header fields as required by spec:
    # transaction features, model prediction, risk score, risk level, analyst decision, analyst reason, timestamp
    writer.writerow([
        "transaction_id",
        "customer_id",
        "amount_bdt",
        "channel",
        "transaction_type",
        "hour",
        "day_of_week",
        "is_new_receiver",
        "is_new_device",
        "location_changed",
        "transactions_last_1h",
        "transactions_last_24h",
        "failed_attempts",
        "account_age_days",
        "receiver_transaction_count",
        "amount_deviation",
        "predicted_risk_score",
        "predicted_risk_level",
        "analyst_decision",
        "analyst_reason",
        "analyst_id",
        "review_timestamp"
    ])

    for fb in feedbacks:
        tx = db.query(Transaction).filter(Transaction.transaction_id == fb.transaction_id).first()
        writer.writerow([
            fb.transaction_id,
            tx.customer_id if tx else "N/A",
            float(tx.amount) if tx else 0.0,
            tx.channel if tx else "APP",
            tx.transaction_type if tx else "SEND_MONEY",
            tx.hour if tx else 12,
            tx.day_of_week if tx else 0,
            tx.is_new_receiver if tx else 0,
            tx.is_new_device if tx else 0,
            tx.location_changed if tx else 0,
            tx.transactions_last_1h if tx else 0,
            tx.transactions_last_24h if tx else 0,
            tx.failed_attempts if tx else 0,
            tx.account_age_days if tx else 365,
            tx.receiver_transaction_count if tx else 0,
            tx.amount_deviation if tx else 1.0,
            fb.predicted_risk or (tx.demo_risk_score if tx else 0.0),
            fb.predicted_level or (tx.risk_level if tx else "LOW"),
            fb.decision,
            fb.comment or fb.reason or "",
            fb.analyst_id or "analyst",
            fb.created_at.isoformat() if fb.created_at else ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=upay_retraining_feedback_dataset.csv"
        }
    )

