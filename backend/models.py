"""
upay AI Shield - SQLAlchemy ORM Models
Defines relational schemas for customers, transactions, predictions, investigations, feedback, and model versions.
Features explicit indexing, audit timestamps, and relational integrity.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    account_age_days = Column(Integer, nullable=False, default=0)
    normal_avg_amount = Column(Float, nullable=False, default=0.0)
    normal_transaction_count = Column(Integer, nullable=False, default=0)
    primary_location = Column(String(128), nullable=True)
    registered_device_count = Column(Integer, nullable=False, default=1)
    account_created_date = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transactions = relationship("Transaction", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=True, index=True)
    amount = Column(Float, nullable=False, index=True)
    timestamp = Column(String(64), nullable=True, index=True)
    hour = Column(Integer, nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)
    transaction_type = Column(String(64), nullable=True)
    channel = Column(String(64), nullable=True)
    receiver_id = Column(String(64), nullable=True, index=True)
    is_new_receiver = Column(Integer, nullable=False, default=0)
    device_id = Column(String(64), nullable=True, index=True)
    is_new_device = Column(Integer, nullable=False, default=0)
    location = Column(String(128), nullable=True)
    location_changed = Column(Integer, nullable=False, default=0)
    transactions_last_1h = Column(Integer, nullable=False, default=0)
    transactions_last_24h = Column(Integer, nullable=False, default=0)
    failed_attempts = Column(Integer, nullable=False, default=0)
    account_age_days = Column(Integer, nullable=False, default=0)
    receiver_transaction_count = Column(Integer, nullable=False, default=0)
    avg_transaction_amount = Column(Float, nullable=False, default=0.0)
    amount_deviation = Column(Float, nullable=False, default=0.0, index=True)
    is_fraud = Column(Integer, nullable=False, default=0, index=True)  # Synthetic Benchmark Label
    demo_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)

    customer = relationship("Customer", back_populates="transactions")
    predictions = relationship("RiskPrediction", back_populates="transaction", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="transaction", cascade="all, delete-orphan")
    feedbacks = relationship("AnalystFeedback", back_populates="transaction", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="transaction", cascade="all, delete-orphan")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    model_version = Column(String(64), nullable=False)
    risk_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(32), nullable=False, index=True)  # LOW, MEDIUM, HIGH
    recommended_action = Column(String(64), nullable=False)  # CONTINUE, ADDITIONAL_REVIEW, HUMAN_REVIEW
    shap_factors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="predictions")


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    risk_context = Column(JSON, nullable=True)
    key_findings = Column(JSON, nullable=True)
    evidence_to_review = Column(JSON, nullable=True)
    behavioral_deviations = Column(JSON, nullable=True)
    ato_indicators = Column(JSON, nullable=True)
    investigation_questions = Column(JSON, nullable=True)
    recommended_action = Column(String(64), nullable=False)
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="investigations")


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    predicted_risk = Column(Float, nullable=True)
    predicted_level = Column(String(32), nullable=True)
    decision = Column(String(32), nullable=False, index=True)  # SUSPICIOUS, LEGITIMATE, NEEDS_REVIEW
    comment = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    analyst_id = Column(String(64), nullable=True, default="analyst_default")
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="feedbacks")


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=True, index=True)
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(32), nullable=False, index=True)  # LOW, MEDIUM, HIGH
    priority = Column(String(32), nullable=False, default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    assigned_analyst = Column(String(64), nullable=True, default="lead_analyst")
    status = Column(String(32), nullable=False, default="OPEN", index=True)  # OPEN, UNDER_REVIEW, NEEDS_MORE_INFORMATION, RESOLVED
    evidence = Column(JSON, nullable=True)
    analyst_notes = Column(Text, nullable=True)
    decision = Column(String(32), nullable=True, index=True)  # CONFIRM_SUSPICIOUS, MARK_LEGITIMATE, NEEDS_MORE_INVESTIGATION
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="cases")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # CREATED, STATUS_CHANGED, NOTE_ADDED, DECISION_RECORDED
    actor = Column(String(64), nullable=False, default="analyst")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    case = relationship("Case", back_populates="events")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(128), nullable=False)
    version = Column(String(64), nullable=False, unique=True)
    algorithm = Column(String(64), nullable=False)
    metrics = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
