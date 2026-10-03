"""
upay AI Shield V3 - Unsupervised Anomaly Detection Service
Utilizes an Isolation Forest trained on normal customer behavior
to calculate continuous anomaly scores and identify unusual behavioral dimensions.
Strictly avoids labeling anomalies as 'fraud'; uses cautious compliance terminology.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import joblib
import numpy as np

from backend.services.feature_engineering import feature_pipeline, ANOMALY_FEATURE_ORDER

logger = logging.getLogger("upay_shield.anomaly")

MODEL_PATH = "ml/models/anomaly_model.pkl"
METADATA_PATH = "ml/models/anomaly_metadata.json"


class AnomalyDetectionService:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.metadata = {}
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded Isolation Forest from {self.model_path}")
            else:
                logger.warning(f"Isolation Forest model not found at {self.model_path}. Anomaly engine will use heuristic fallback.")

            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load anomaly model: {e}")
            self.model = None

    def score_transaction(
        self,
        raw_tx: Dict[str, Any],
        customer_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a transaction and returns anomaly_score (0-1), anomaly_level,
        and explanations of which behavioral dimensions deviate.
        """
        engineered = feature_pipeline.engineer_features(raw_tx, customer_profile)
        vec = feature_pipeline.extract_anomaly_vector(engineered)

        if self.model is not None:
            try:
                X = np.array([vec])
                # decision_function: lower means more anomalous (negative for outliers)
                raw_decision = float(self.model.decision_function(X)[0])
                # Map raw_decision (-0.08 to +0.17) to a normalized anomaly score 0.0 to 1.0
                # Inlier (~0.12) -> anomaly_score ~ 0.08; Outlier (-0.06) -> anomaly_score ~ 0.92
                anomaly_score = float(np.clip(1.0 - (raw_decision + 0.08) / 0.25, 0.0, 1.0))
            except Exception as e:
                logger.error(f"Isolation forest inference failed: {e}")
                anomaly_score = self._heuristic_score(engineered)
        else:
            anomaly_score = self._heuristic_score(engineered)

        anomaly_score = round(anomaly_score, 4)

        # Categorize level
        if anomaly_score >= 0.70:
            anomaly_level = "HIGH"
            status_desc = "Unusual Behavior Detected — Structural Behavioral Anomaly"
        elif anomaly_score >= 0.40:
            anomaly_level = "MEDIUM"
            status_desc = "Moderate Behavioral Deviation — Requires Investigation"
        else:
            anomaly_level = "LOW"
            status_desc = "Normal Behavioral Range"

        # Diagnose specific anomalous features
        anomalous_features = self._explain_anomalous_features(engineered)

        return {
            "anomaly_score": anomaly_score,
            "anomaly_level": anomaly_level,
            "status": status_desc,
            "anomalous_features": anomalous_features,
            "raw_features": {
                "amount_zscore": engineered.get("amount_zscore", 0.0),
                "hour_deviation": engineered.get("hour_deviation", 0.0),
                "velocity_ratio": engineered.get("velocity_ratio", 1.0),
                "failed_attempts": engineered.get("failed_attempts", 0),
                "amount_deviation": engineered.get("amount_deviation", 1.0),
            }
        }

    def _heuristic_score(self, feat: Dict[str, Any]) -> float:
        dev = float(feat.get("amount_deviation", 1.0))
        vel = float(feat.get("transactions_last_1h", 1))
        fails = int(feat.get("failed_attempts", 0))
        hour_dev = float(feat.get("hour_deviation", 0.0))

        score = 0.05
        if dev >= 5.0:
            score += 0.35
        elif dev >= 2.5:
            score += 0.15

        if vel >= 6:
            score += 0.30
        elif vel >= 3:
            score += 0.15

        if fails >= 3:
            score += 0.20
        if hour_dev >= 4:
            score += 0.15

        return min(round(score, 4), 1.0)

    def _explain_anomalous_features(self, feat: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []
        dev = float(feat.get("amount_deviation", 1.0))
        zscore = float(feat.get("amount_zscore", 0.0))
        if dev >= 3.0 or zscore >= 2.5:
            anomalies.append({
                "feature": "amount",
                "label": "Extreme Amount Surge",
                "detail": f"Amount is {dev:.1f}x historical baseline average (Z-score: {zscore:.2f}).",
                "severity": "HIGH" if dev >= 6.0 else "MEDIUM"
            })

        hour = int(feat.get("hour", 12))
        hour_dev = float(feat.get("hour_deviation", 0.0))
        if hour_dev >= 3.0 or 0 <= hour <= 5:
            anomalies.append({
                "feature": "hour",
                "label": "Off-Hours Activity Window",
                "detail": f"Submitted at {hour:02d}:00, outside customer's habitual operating schedule.",
                "severity": "MEDIUM"
            })

        tx_1h = int(feat.get("transactions_last_1h", 1))
        vel_ratio = float(feat.get("velocity_ratio", 1.0))
        if tx_1h >= 4 or vel_ratio >= 3.0:
            anomalies.append({
                "feature": "transactions_last_1h",
                "label": "Hourly Velocity Burst",
                "detail": f"{tx_1h} transactions in the trailing 60 minutes ({vel_ratio:.1f}x baseline).",
                "severity": "HIGH" if tx_1h >= 8 else "MEDIUM"
            })

        fails = int(feat.get("failed_attempts", 0))
        if fails >= 2:
            anomalies.append({
                "feature": "failed_attempts",
                "label": "Pre-Authentication Failures",
                "detail": f"{fails} failed authentication attempts recorded prior to this session.",
                "severity": "HIGH" if fails >= 4 else "MEDIUM"
            })

        if int(feat.get("is_new_device", 0)) == 1:
            anomalies.append({
                "feature": "is_new_device",
                "label": "Unregistered Device Fingerprint",
                "detail": "Hardware/browser fingerprint has never been previously linked to this account.",
                "severity": "HIGH"
            })

        if int(feat.get("location_changed", 0)) == 1:
            anomalies.append({
                "feature": "location_changed",
                "label": "Geographic Origin Shift",
                "detail": "Originating location differs from customer's habitual geographic cluster.",
                "severity": "LOW"
            })

        return anomalies


anomaly_service = AnomalyDetectionService()
