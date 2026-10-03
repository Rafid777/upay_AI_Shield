"""
upay AI Shield - Pydantic Schemas
Comprehensive request/response validation schemas for transactions,
predictions, SHAP explanations, behavioral intelligence, ATO detection,
AI investigations, analyst feedback, and dashboard metrics.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ==========================================
# TRANSACTION SCHEMAS
# ==========================================

class TransactionFeatures(BaseModel):
    amount: float = Field(..., ge=0, description="Transaction amount in currency units")
    hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of the week (0-6)")
    is_new_receiver: int = Field(..., ge=0, le=1, description="1 if receiver is unseen, 0 otherwise")
    is_new_device: int = Field(..., ge=0, le=1, description="1 if device is unrecognized, 0 otherwise")
    location_changed: int = Field(..., ge=0, le=1, description="1 if location is different from usual, 0 otherwise")
    transactions_last_1h: int = Field(..., ge=0, description="Velocity count in last 1 hour")
    transactions_last_24h: int = Field(..., ge=0, description="Velocity count in last 24 hours")
    failed_attempts: int = Field(..., ge=0, description="Consecutive failed authentication attempts")
    account_age_days: int = Field(..., ge=0, description="Age of customer account in days")
    receiver_transaction_count: int = Field(..., ge=0, description="Total transactions completed by receiver")
    amount_deviation: float = Field(..., ge=0, description="Ratio of amount to customer's historical average")


class TransactionCreate(TransactionFeatures):
    transaction_id: str
    customer_id: Optional[str] = None
    timestamp: Optional[str] = None
    transaction_type: Optional[str] = "PAYMENT"
    channel: Optional[str] = "MOBILE_APP"
    receiver_id: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    avg_transaction_amount: Optional[float] = 0.0


class TransactionResponse(BaseModel):
    transaction_id: str
    customer_id: Optional[str]
    amount: float
    timestamp: Optional[str]
    hour: int
    day_of_week: int
    transaction_type: Optional[str]
    channel: Optional[str]
    receiver_id: Optional[str]
    is_new_receiver: int
    device_id: Optional[str]
    is_new_device: int
    location: Optional[str]
    location_changed: int
    transactions_last_1h: int
    transactions_last_24h: int
    failed_attempts: int
    account_age_days: int
    receiver_transaction_count: int
    avg_transaction_amount: float
    amount_deviation: float
    is_fraud: int
    demo_risk_score: Optional[float] = None
    risk_level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    transactions: List[TransactionResponse]


# ==========================================
# PREDICTION & SHAP SCHEMAS
# ==========================================

class PredictRequest(BaseModel):
    transaction_id: Optional[str] = None
    features: Optional[TransactionFeatures] = None


class SHAPFactor(BaseModel):
    feature: str
    shap_value: float
    feature_value: Any
    impact: Literal["RISK_INCREASING", "RISK_REDUCING"]
    importance_rank: int
    explanation: str


class PredictResponse(BaseModel):
    transaction_id: str
    risk_probability: float
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    recommended_action: Literal["CONTINUE", "ADDITIONAL_REVIEW", "HUMAN_REVIEW"]
    model_version: str
    shap_factors: List[SHAPFactor]
    governance_note: str = "AI prediction only. Autonomous fund blocking is prohibited. Consequential decisions require human review."


# ==========================================
# INVESTIGATION & GEMINI SCHEMAS
# ==========================================

class InvestigateRequest(BaseModel):
    transaction_id: str


class RiskContext(BaseModel):
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class InvestigationResponse(BaseModel):
    transaction_id: str
    summary: str
    risk_context: RiskContext
    risk_signals: Optional[List[str]] = Field(default_factory=list)
    key_findings: Optional[List[str]] = Field(default_factory=list)
    behavioral_deviations: Optional[List[str]] = Field(default_factory=list)
    investigation_questions: Optional[List[str]] = Field(default_factory=list)
    evidence_to_review: Optional[List[str]] = Field(default_factory=list)
    recommended_action: Literal["CONTINUE", "ADDITIONAL_REVIEW", "HUMAN_REVIEW"]
    confidence_note: Optional[str] = None
    human_review_required: Optional[bool] = True
    customer_baseline: Optional[Dict[str, Any]] = None
    behavioral_comparison: Optional[Dict[str, Any]] = None
    ato_intelligence: Optional[Dict[str, Any]] = None
    scam_intelligence: Optional[Dict[str, Any]] = None
    risk_story: Optional[Dict[str, Any]] = None
    network_graph: Optional[Dict[str, Any]] = None
    is_ai_generated: bool = True
    notice: str = "Generated by AI Investigation Assistant from model evidence. Not ground truth confirmation."


# ==========================================
# CHAT SCHEMAS
# ==========================================

class ChatRequest(BaseModel):
    transaction_id: str
    message: str


class ChatResponse(BaseModel):
    transaction_id: str
    reply: str
    risk_context: RiskContext
    evidence_sources: List[str]


# ==========================================
# FEEDBACK SCHEMAS
# ==========================================

class FeedbackCreate(BaseModel):
    transaction_id: str
    decision: Literal["SUSPICIOUS", "LEGITIMATE", "NEEDS_REVIEW"]
    comment: Optional[str] = None
    reason: Optional[str] = None
    predicted_risk: Optional[float] = None
    predicted_level: Optional[str] = None
    analyst_id: Optional[str] = "analyst_1"


class FeedbackResponse(BaseModel):
    id: int
    transaction_id: str
    decision: str
    comment: Optional[str]
    reason: Optional[str]
    predicted_risk: Optional[float] = None
    predicted_level: Optional[str] = None
    analyst_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackStatsResponse(BaseModel):
    total_reviewed: int
    confirmed_suspicious: int
    marked_legitimate: int
    needs_investigation: int
    suspicious_rate_pct: float
    recent_feedbacks: List[FeedbackResponse]


# ==========================================
# SCAM INTELLIGENCE SCHEMAS
# ==========================================

class ScamPatternDetail(BaseModel):
    pattern_code: str
    pattern_name: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    description: str
    matched_signals: List[str]
    recommendation: str


class ScamIntelligenceResponse(BaseModel):
    transaction_id: str
    patterns_detected: List[ScamPatternDetail]
    highest_severity: str
    status: str
    signals_summary: List[str]
    investigation_guidance: str


# ==========================================
# RISK STORY & TIMELINE SCHEMAS
# ==========================================

class RiskTimelineItem(BaseModel):
    time: str
    event_type: str
    description: str
    severity: Literal["NORMAL", "INFO", "WARNING", "CRITICAL"]
    amount: Optional[float] = None
    icon: Optional[str] = None


class RiskStoryResponse(BaseModel):
    transaction_id: str
    customer_id: str
    headline: str
    risk_score: float
    risk_level: str
    timeline_events: List[RiskTimelineItem]
    narrative_summary: str


# ==========================================
# WHAT-IF SIMULATION SCHEMAS
# ==========================================

class WhatIfRequest(BaseModel):
    transaction_id: Optional[str] = None
    base_features: Optional[Dict[str, Any]] = None
    modified_features: Dict[str, Any]


class WhatIfFactorChange(BaseModel):
    feature: str
    original_value: Any
    modified_value: Any
    direction: str


class WhatIfResponse(BaseModel):
    original_risk_score: float
    original_risk_level: str
    simulated_risk_score: float
    simulated_risk_level: str
    score_delta: float
    risk_level_changed: bool
    changed_features: Dict[str, Any]
    top_changed_factors: List[WhatIfFactorChange]
    disclaimer: str = "Simulation only — not a production transaction decision."


# ==========================================
# CASE MANAGEMENT SCHEMAS
# ==========================================

class CaseCreate(BaseModel):
    transaction_id: str
    priority: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = "HIGH"
    assigned_analyst: Optional[str] = "lead_analyst"
    analyst_notes: Optional[str] = None


class CaseUpdate(BaseModel):
    status: Optional[Literal["OPEN", "UNDER_REVIEW", "NEEDS_MORE_INFORMATION", "RESOLVED"]] = None
    priority: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None
    assigned_analyst: Optional[str] = None
    analyst_notes: Optional[str] = None


class CaseDecisionRequest(BaseModel):
    decision: Literal["CONFIRM_SUSPICIOUS", "MARK_LEGITIMATE", "NEEDS_MORE_INVESTIGATION"]
    analyst_notes: Optional[str] = None
    analyst_id: Optional[str] = "lead_analyst"


class CaseEventResponse(BaseModel):
    id: int
    event_type: str
    actor: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CaseResponse(BaseModel):
    case_id: str
    transaction_id: str
    customer_id: Optional[str] = None
    risk_score: float
    risk_level: str
    priority: str
    assigned_analyst: Optional[str] = None
    status: str
    evidence: Optional[Dict[str, Any]] = None
    analyst_notes: Optional[str] = None
    decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    events: Optional[List[CaseEventResponse]] = None
    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    total: int
    cases: List[CaseResponse]


# ==========================================
# MODEL MONITORING & DATA DRIFT SCHEMAS
# ==========================================

class FeatureDriftItem(BaseModel):
    feature: str
    drift_score: float
    drift_level: Literal["LOW", "MEDIUM", "HIGH"]
    reference_mean: float
    current_mean: float
    distribution_shift: str


class ModelDriftResponse(BaseModel):
    model_version: str
    evaluated_transactions_count: int
    reference_transactions_count: int
    overall_drift_status: Literal["LOW", "MEDIUM", "HIGH", "INSUFFICIENT_DATA"]
    features_drift: List[FeatureDriftItem]
    status_message: str


class ModelHealthResponse(BaseModel):
    model_name: str
    version: str
    algorithm: str
    status: str
    training_samples: int
    test_samples: int
    evaluation_metrics: Dict[str, Any]
    feature_importance: List[Dict[str, Any]]
    hyperparameters: Dict[str, Any]
    trained_features: List[str]


# ==========================================
# CUSTOMER BEHAVIOR PROFILE SCHEMAS
# ==========================================

class CustomerBehaviorResponse(BaseModel):
    customer_id: str
    account_age_days: int
    normal_avg_amount: float
    normal_transaction_count: int
    primary_location: Optional[str] = None
    registered_device_count: int
    typical_hours: str
    typical_daily_frequency: float
    recent_transactions: List[TransactionResponse]


# ==========================================
# CHANNEL INTELLIGENCE SCHEMA
# ==========================================

class ChannelStat(BaseModel):
    channel: str
    transaction_count: int
    total_amount_bdt: float
    average_amount_bdt: float
    high_risk_count: int
    high_risk_percentage: float


# ==========================================
# DASHBOARD SCHEMAS
# ==========================================

class RiskBreakdown(BaseModel):
    count: int
    percentage: float


class BusinessImpactSimulation(BaseModel):
    high_risk_detected: int
    human_reviews_required: int
    potentially_suspicious_amount: float
    total_monitored_amount: float
    review_volume_reduction_pct: float
    automated_continue_pct: float
    disclaimer: str = "Prototype Simulation / Synthetic Dataset Evaluation. Not real upay production values."


class TopRiskSignalStat(BaseModel):
    signal_name: str
    count: int
    percentage: float


class DashboardStatsResponse(BaseModel):
    total_transactions: int
    low_risk: RiskBreakdown
    medium_risk: RiskBreakdown
    high_risk: RiskBreakdown
    human_reviews_count: int
    confirmed_suspicious_count: int
    false_positive_reviews_count: int
    open_cases_count: Optional[int] = 0
    potential_scam_count: Optional[int] = 0
    potential_ato_count: Optional[int] = 0
    model_metrics: Dict[str, Any]
    business_impact: BusinessImpactSimulation
    recent_high_risk: List[TransactionResponse]
    hourly_distribution: Dict[str, int]
    top_risk_signals: List[TopRiskSignalStat]
    channel_stats: Optional[List[ChannelStat]] = Field(default_factory=list)
    feedback_stats: FeedbackStatsResponse
