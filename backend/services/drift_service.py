"""
upay AI Shield - Data Drift Monitoring Service
Performs empirical statistical drift comparison between reference training distributions
and recent production transaction streams.

Methodology:
- Reference Baseline: Derived from the 16,000 stratified training set (persisted in feature_schema.json).
- Current Stream: Computed dynamically from recent database transactions.
- Statistical Distance Metric: Normalized Absolute Mean Shift (NAMS) = |μ_current - μ_ref| / σ_ref.
- Thresholds:
    * Score < 0.25: LOW DRIFT (Nominal covariate shift within standard sampling variance)
    * 0.25 <= Score < 0.60: MEDIUM DRIFT (Moderate shift; schedule model inspection)
    * Score >= 0.60: HIGH DRIFT (Significant distribution divergence; trigger retraining alert)
"""

import json
import os
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Transaction

logger = logging.getLogger(__name__)

FEATURE_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models", "feature_schema.json")
MODEL_METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models", "model_metadata.json")


class DataDriftService:
    def __init__(self):
        self.reference_schema = self._load_reference_schema()
        self.model_version = self._load_model_version()

    def _load_reference_schema(self) -> Dict[str, Any]:
        if os.path.exists(FEATURE_SCHEMA_PATH):
            try:
                with open(FEATURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading feature schema: {e}")
        return {}

    def _load_model_version(self) -> str:
        if os.path.exists(MODEL_METADATA_PATH):
            try:
                with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    return meta.get("model_version", "upay-ai-shield-v1.0.0")
            except Exception:
                pass
        return "upay-ai-shield-v1.0.0"

    def evaluate_drift(self, db: Session, sample_limit: int = 1000) -> Dict[str, Any]:
        # 1. Fetch recent transactions
        recent_txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(sample_limit).all()
        count = len(recent_txs)

        if count < 20:
            return {
                "model_version": self.model_version,
                "evaluated_transactions_count": count,
                "reference_transactions_count": 16000,
                "overall_drift_status": "INSUFFICIENT_DATA",
                "features_drift": [],
                "status_message": "Insufficient data for reliable drift estimation (minimum 20 recent transactions required)."
            }

        features_to_monitor = [
            "amount",
            "hour",
            "transactions_last_1h",
            "transactions_last_24h",
            "failed_attempts",
            "amount_deviation",
            "is_new_device",
            "is_new_receiver",
            "location_changed"
        ]

        feature_drifts = []
        high_drift_count = 0
        med_drift_count = 0

        for feat in features_to_monitor:
            ref_stat = self.reference_schema.get(feat, {})
            ref_mean = float(ref_stat.get("mean", 1.0))
            ref_std = float(ref_stat.get("std", 1.0))
            if ref_std <= 0:
                ref_std = 1.0

            # Compute current sample mean
            vals = [float(getattr(tx, feat, 0.0) or 0.0) for tx in recent_txs]
            curr_mean = sum(vals) / len(vals)

            # Normalized Mean Shift (Wasserstein proxy)
            drift_score = round(abs(curr_mean - ref_mean) / ref_std, 4)

            if drift_score >= 0.60:
                drift_level = "HIGH"
                high_drift_count += 1
            elif drift_score >= 0.25:
                drift_level = "MEDIUM"
                med_drift_count += 1
            else:
                drift_level = "LOW"

            pct_shift = ((curr_mean - ref_mean) / max(abs(ref_mean), 1e-4)) * 100
            sign = "+" if pct_shift >= 0 else ""
            desc = f"Sample mean {curr_mean:,.2f} vs ref {ref_mean:,.2f} ({sign}{pct_shift:.1f}% shift)"

            feature_drifts.append({
                "feature": feat,
                "drift_score": drift_score,
                "drift_level": drift_level,
                "reference_mean": round(ref_mean, 2),
                "current_mean": round(curr_mean, 2),
                "distribution_shift": desc
            })

        # Overall Status
        if high_drift_count >= 2:
            overall_status = "HIGH"
            msg = f"High feature drift detected across {high_drift_count} features. Recommend queueing retraining dataset."
        elif high_drift_count >= 1 or med_drift_count >= 3:
            overall_status = "MEDIUM"
            msg = f"Moderate distribution shift detected across {med_drift_count + high_drift_count} features. Continuous monitoring advised."
        else:
            overall_status = "LOW"
            msg = "Nominal distribution alignment with reference training baseline. No significant covariate drift detected."

        return {
            "model_version": self.model_version,
            "evaluated_transactions_count": count,
            "reference_transactions_count": 16000,
            "overall_drift_status": overall_status,
            "features_drift": feature_drifts,
            "status_message": msg
        }


drift_service = DataDriftService()
