"""
upay AI Shield V3 - Feature Engineering Pipeline
Provides reusable feature transformations, derivations, and normalization
for supervised ML (XGBoost) and unsupervised anomaly detection (Isolation Forest).
Strictly eliminates identifier leakage (transaction_id, customer_id, device_id, receiver_id).
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np


# Core 12 features required by the trained XGBoost Risk Classifier in exact order
XGB_FEATURE_ORDER: List[str] = [
    "amount",
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
]

# Behavioral features used for Unsupervised Anomaly Detection (Isolation Forest)
ANOMALY_FEATURE_ORDER: List[str] = [
    "amount",
    "hour",
    "amount_deviation",
    "transactions_last_1h",
    "transactions_last_24h",
    "failed_attempts",
    "amount_zscore",
    "hour_deviation",
    "velocity_ratio",
    "failed_attempt_rate",
]


class FeatureEngineeringPipeline:
    """
    Transforms raw payment telemetry and customer historical baseline data into
    engineered feature representations for model inference and anomaly scoring.
    """

    @staticmethod
    def engineer_features(
        raw_tx: Dict[str, Any],
        customer_profile: Optional[Dict[str, Any]] = None,
        network_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Derives all behavioral, telemetry, and contextual signals while stripping identifiers.
        """
        amount = float(raw_tx.get("amount", 0.0))
        hour = int(raw_tx.get("hour", 12))
        day_of_week = int(raw_tx.get("day_of_week", 0))
        is_new_receiver = int(raw_tx.get("is_new_receiver", 0))
        is_new_device = int(raw_tx.get("is_new_device", 0))
        location_changed = int(raw_tx.get("location_changed", 0))
        tx_1h = int(raw_tx.get("transactions_last_1h", 1))
        tx_24h = int(raw_tx.get("transactions_last_24h", 1))
        failed_attempts = int(raw_tx.get("failed_attempts", 0))
        account_age_days = int(raw_tx.get("account_age_days", 365))
        receiver_tx_count = int(raw_tx.get("receiver_transaction_count", 0))

        # Baseline resolution
        cust_profile = customer_profile or {}
        cust_avg_amount = float(
            cust_profile.get("avg_transaction_amount", raw_tx.get("avg_transaction_amount", 1000.0)) or 1000.0
        )
        cust_std_amount = float(cust_profile.get("std_transaction_amount", cust_avg_amount * 0.4) or 400.0)
        cust_avg_velocity = float(cust_profile.get("baseline_velocity_per_hour", 1.0) or 1.0)
        cust_daily_tx = float(cust_profile.get("avg_daily_transactions", 3.0) or 3.0)
        cust_daily_amount = float(cust_profile.get("avg_daily_amount", cust_avg_amount * cust_daily_tx) or (cust_avg_amount * 3.0))

        # Amount deviation
        raw_dev = raw_tx.get("amount_deviation")
        if raw_dev is not None:
            amount_deviation = float(raw_dev)
        else:
            amount_deviation = round(amount / max(cust_avg_amount, 1.0), 2)

        # Derived Feature 1: amount_zscore
        amount_zscore = round((amount - cust_avg_amount) / max(cust_std_amount, 10.0), 4)

        # Derived Feature 2: hour_deviation (distance outside typical diurnal window 08:00 - 22:00)
        if 8 <= hour <= 22:
            hour_deviation = 0.0
        elif hour < 8:
            hour_deviation = float(8 - hour)
        else:
            hour_deviation = float(hour - 22)

        # Derived Feature 3: velocity_ratio (1-hour count vs customer normal velocity)
        velocity_ratio = round(float(tx_1h) / max(cust_avg_velocity, 0.5), 2)

        # Derived Feature 4: receiver_novelty (1 if new receiver, 0 otherwise)
        receiver_novelty = is_new_receiver

        # Derived Feature 5: device_novelty (1 if new device, 0 otherwise)
        device_novelty = is_new_device

        # Derived Feature 6: location_novelty (1 if changed, 0 otherwise)
        location_novelty = location_changed

        # Derived Feature 7: failed_attempt_rate (failed attempts normalized)
        failed_attempt_rate = round(float(failed_attempts) / float(failed_attempts + 1), 4)

        # Derived Network Features
        net = network_stats or {}
        receiver_cust_count = int(net.get("receiver_customer_count", max(receiver_tx_count, 1)))
        device_cust_count = int(net.get("device_customer_count", 1))

        return {
            # Core base features
            "amount": amount,
            "hour": hour,
            "day_of_week": day_of_week,
            "transaction_type": str(raw_tx.get("transaction_type", "SEND_MONEY")),
            "channel": str(raw_tx.get("channel", "APP")),
            "is_new_receiver": is_new_receiver,
            "is_new_device": is_new_device,
            "location_changed": location_changed,
            "transactions_last_1h": tx_1h,
            "transactions_last_24h": tx_24h,
            "failed_attempts": failed_attempts,
            "account_age_days": account_age_days,
            "receiver_transaction_count": receiver_tx_count,
            "average_transaction_amount": cust_avg_amount,
            "amount_deviation": amount_deviation,
            # Meaningful derived features (Section 4)
            "amount_zscore": amount_zscore,
            "hour_deviation": hour_deviation,
            "velocity_ratio": velocity_ratio,
            "receiver_novelty": receiver_novelty,
            "device_novelty": device_novelty,
            "location_novelty": location_novelty,
            "failed_attempt_rate": failed_attempt_rate,
            "customer_daily_transaction_count": cust_daily_tx,
            "customer_daily_amount": cust_daily_amount,
            "receiver_customer_count": receiver_cust_count,
            "device_customer_count": device_cust_count,
        }

    @staticmethod
    def extract_xgb_vector(features: Dict[str, Any]) -> List[float]:
        """Extracts the exact 12-dimensional vector required by the XGBoost classifier."""
        return [float(features.get(col, 0.0)) for col in XGB_FEATURE_ORDER]

    @staticmethod
    def extract_anomaly_vector(features: Dict[str, Any]) -> List[float]:
        """Extracts the behavioral vector used by the Isolation Forest model."""
        return [float(features.get(col, 0.0)) for col in ANOMALY_FEATURE_ORDER]


feature_pipeline = FeatureEngineeringPipeline()
