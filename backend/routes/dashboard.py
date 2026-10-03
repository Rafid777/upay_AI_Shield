"""
upay AI Shield - Dashboard Analytics API Route
Computes operational KPIs, risk distribution, hourly trends, model validation,
top behavioral signals, business impact simulations, and human feedback analytics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Transaction, AnalystFeedback
from backend.schemas import (
    DashboardStatsResponse, RiskBreakdown, TransactionResponse,
    BusinessImpactSimulation, TopRiskSignalStat, FeedbackStatsResponse, FeedbackResponse,
    ChannelStat
)
from backend.services.model_service import model_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retrieves operational KPIs, risk distribution, hourly trends, model performance,
    top risk signals, business impact simulation, and feedback audit metrics.
    All data is derived dynamically from actual database records.
    """
    total = db.query(Transaction).count() or 1
    
    # Risk counts
    high_count = db.query(Transaction).filter(Transaction.risk_level == "HIGH").count()
    med_count = db.query(Transaction).filter(Transaction.risk_level == "MEDIUM").count()
    low_count = db.query(Transaction).filter(Transaction.risk_level == "LOW").count()

    # Feedback Loop counts
    total_feedbacks = db.query(AnalystFeedback).count()
    suspicious_count = db.query(AnalystFeedback).filter(AnalystFeedback.decision == "SUSPICIOUS").count()
    legitimate_count = db.query(AnalystFeedback).filter(AnalystFeedback.decision == "LEGITIMATE").count()
    needs_review_count = db.query(AnalystFeedback).filter(AnalystFeedback.decision == "NEEDS_REVIEW").count()

    recent_fb_records = db.query(AnalystFeedback).order_by(AnalystFeedback.created_at.desc()).limit(10).all()
    suspicious_rate = round(suspicious_count / max(total_feedbacks, 1) * 100, 2)

    feedback_stats = FeedbackStatsResponse(
        total_reviewed=total_feedbacks,
        confirmed_suspicious=suspicious_count,
        marked_legitimate=legitimate_count,
        needs_investigation=needs_review_count,
        suspicious_rate_pct=suspicious_rate,
        recent_feedbacks=[FeedbackResponse.model_validate(f) for f in recent_fb_records]
    )

    # Top Risk Signals aggregation
    new_device_count = db.query(Transaction).filter(Transaction.is_new_device == 1).count()
    new_receiver_count = db.query(Transaction).filter(Transaction.is_new_receiver == 1).count()
    loc_changed_count = db.query(Transaction).filter(Transaction.location_changed == 1).count()
    amount_surge_count = db.query(Transaction).filter(Transaction.amount_deviation >= 3.0).count()
    failed_auth_count = db.query(Transaction).filter(Transaction.failed_attempts >= 1).count()
    velocity_burst_count = db.query(Transaction).filter(Transaction.transactions_last_1h >= 5).count()

    top_signals = [
        TopRiskSignalStat(signal_name="Unregistered Device", count=new_device_count, percentage=round(new_device_count / total * 100, 1)),
        TopRiskSignalStat(signal_name="First-Time Recipient", count=new_receiver_count, percentage=round(new_receiver_count / total * 100, 1)),
        TopRiskSignalStat(signal_name="Geographic Location Shift", count=loc_changed_count, percentage=round(loc_changed_count / total * 100, 1)),
        TopRiskSignalStat(signal_name="High Amount Deviation (>=3x)", count=amount_surge_count, percentage=round(amount_surge_count / total * 100, 1)),
        TopRiskSignalStat(signal_name="Prior Failed Logins", count=failed_auth_count, percentage=round(failed_auth_count / total * 100, 1)),
        TopRiskSignalStat(signal_name="Short-Term Velocity Burst (>=5/h)", count=velocity_burst_count, percentage=round(velocity_burst_count / total * 100, 1))
    ]
    top_signals.sort(key=lambda s: s.count, reverse=True)

    # Financial volumes & Business impact calculation
    total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0.0
    high_risk_amount = db.query(func.sum(Transaction.amount)).filter(Transaction.risk_level == "HIGH").scalar() or 0.0
    auto_continue_pct = round(low_count / total * 100, 2)

    business_impact = BusinessImpactSimulation(
        high_risk_detected=high_count,
        human_reviews_required=high_count,
        potentially_suspicious_amount=round(float(high_risk_amount), 2),
        total_monitored_amount=round(float(total_amount), 2),
        review_volume_reduction_pct=auto_continue_pct,
        automated_continue_pct=auto_continue_pct,
        disclaimer="Prototype Simulation / Synthetic Dataset Evaluation. Not real upay production values."
    )

    # Recent high-risk transactions
    recent_high = db.query(Transaction).filter(
        Transaction.risk_level == "HIGH"
    ).order_by(
        Transaction.amount_deviation.desc(),
        Transaction.amount.desc()
    ).limit(8).all()

    # Hourly distribution
    hourly_rows = db.query(
        Transaction.hour, func.count(Transaction.transaction_id)
    ).group_by(Transaction.hour).all()
    hourly_dist = {f"{h:02d}:00": count for h, count in sorted(hourly_rows, key=lambda x: x[0])}

    # Channel Intelligence
    channels = ["APP", "USSD", "WEB", "AGENT"]
    channel_stats = []
    for ch in channels:
        ch_txs = db.query(Transaction).filter(Transaction.channel == ch)
        ch_count = ch_txs.count()
        if ch_count > 0:
            ch_total = db.query(func.sum(Transaction.amount)).filter(Transaction.channel == ch).scalar() or 0.0
            ch_high = db.query(Transaction).filter(Transaction.channel == ch, Transaction.risk_level == "HIGH").count()
            channel_stats.append(ChannelStat(
                channel=ch,
                transaction_count=ch_count,
                total_amount_bdt=round(float(ch_total), 2),
                average_amount_bdt=round(float(ch_total) / ch_count, 2),
                high_risk_count=ch_high,
                high_risk_percentage=round(ch_high / ch_count * 100, 2)
            ))
        else:
            channel_stats.append(ChannelStat(
                channel=ch,
                transaction_count=0,
                total_amount_bdt=0.0,
                average_amount_bdt=0.0,
                high_risk_count=0,
                high_risk_percentage=0.0
            ))

    # Case Management counts
    from backend.models import Case
    open_cases_count = db.query(Case).filter(Case.status == "OPEN").count()
    if open_cases_count == 0 and db.query(Case).count() == 0:
        from backend.services.case_service import case_service
        case_service._seed_initial_cases(db)
        open_cases_count = db.query(Case).filter(Case.status == "OPEN").count()

    # Potential Scam & ATO counts from actual database records
    scam_count = db.query(Transaction).filter(
        Transaction.risk_level == "HIGH",
        Transaction.amount_deviation >= 3.0,
        Transaction.is_new_receiver == 1
    ).count()

    ato_count = db.query(Transaction).filter(
        Transaction.is_new_device == 1,
        Transaction.location_changed == 1
    ).count()

    metadata = model_service.get_metadata()
    metrics = metadata.get("evaluation_metrics", {})

    return DashboardStatsResponse(
        total_transactions=total,
        low_risk=RiskBreakdown(count=low_count, percentage=round(low_count / total * 100, 2)),
        medium_risk=RiskBreakdown(count=med_count, percentage=round(med_count / total * 100, 2)),
        high_risk=RiskBreakdown(count=high_count, percentage=round(high_count / total * 100, 2)),
        human_reviews_count=high_count,
        confirmed_suspicious_count=suspicious_count,
        false_positive_reviews_count=legitimate_count,
        open_cases_count=open_cases_count,
        potential_scam_count=scam_count,
        potential_ato_count=ato_count,
        model_metrics=metrics,
        business_impact=business_impact,
        recent_high_risk=[TransactionResponse.model_validate(t) for t in recent_high],
        hourly_distribution=hourly_dist,
        top_risk_signals=top_signals,
        channel_stats=channel_stats,
        feedback_stats=feedback_stats
    )
