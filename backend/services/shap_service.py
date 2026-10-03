"""
upay AI Shield - SHAP Explainability Service
Computes transaction-level SHAP values and translates them into interpretable risk factors.
"""

import logging
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import shap
from backend.services.model_service import model_service
from src.data_pipeline import MODEL_FEATURES

logger = logging.getLogger(__name__)


FEATURE_DESCRIPTIONS = {
    "amount": "Transaction amount in monetary units",
    "hour": "Time of transaction occurrence",
    "day_of_week": "Day of the week of transaction",
    "is_new_receiver": "Transaction recipient status",
    "is_new_device": "Device identification status",
    "location_changed": "Geographic location deviation",
    "transactions_last_1h": "Short-term transaction velocity (1 hour)",
    "transactions_last_24h": "Daily transaction velocity (24 hours)",
    "failed_attempts": "Authentication security attempts",
    "account_age_days": "Maturity of the customer account",
    "receiver_transaction_count": "Historical transaction volume of the receiver",
    "amount_deviation": "Relative deviation from customer's average spending"
}


class SHAPService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SHAPService, cls).__new__(cls)
            cls._instance._init_explainer()
        return cls._instance

    def _init_explainer(self):
        logger.info("Initializing SHAP TreeExplainer on risk model...")
        model = model_service.get_model()
        self.explainer = shap.TreeExplainer(model)
        self.feature_names = MODEL_FEATURES
        logger.info("SHAP TreeExplainer initialized successfully.")

    def explain(self, features_df: pd.DataFrame, top_k: int = 6) -> List[Dict[str, Any]]:
        """
        Calculates exact SHAP values for a given transaction features row.
        Returns a sorted list of top risk factors.
        """
        shap_values = self.explainer(features_df)
        values = shap_values.values[0]  # Array of shap values for row

        factors = []
        for idx, feature in enumerate(self.feature_names):
            val = float(values[idx])
            raw_val = features_df[feature].iloc[0]
            impact = "RISK_INCREASING" if val > 0 else "RISK_REDUCING"
            explanation = self._generate_factor_explanation(feature, raw_val, val)

            factors.append({
                "feature": feature,
                "shap_value": round(val, 4),
                "feature_value": round(float(raw_val), 2) if isinstance(raw_val, (int, float, np.number)) else str(raw_val),
                "impact": impact,
                "abs_importance": abs(val),
                "explanation": explanation
            })

        # Sort by absolute SHAP importance descending
        factors.sort(key=lambda x: x["abs_importance"], reverse=True)

        # Assign importance rank and pick top factors
        result = []
        for rank, f in enumerate(factors[:top_k], start=1):
            f["importance_rank"] = rank
            del f["abs_importance"]
            result.append(f)

        return result

    def _generate_factor_explanation(self, feature: str, value: Any, shap_val: float) -> str:
        """Generates dynamic, human-interpretable risk explanation."""
        direction = "elevates" if shap_val > 0 else "moderates"

        if feature == "amount_deviation":
            if value > 3.0:
                return f"High amount deviation ({value:.1f}x normal baseline) significantly elevates transaction risk."
            elif value <= 1.0:
                return f"Amount is consistent with customer's typical spending patterns (deviation: {value:.1f}x)."
            return f"Moderate deviation from baseline ({value:.1f}x)."

        elif feature == "is_new_device":
            if value == 1:
                return "Initiated from a newly detected or unregistered device identifier."
            return "Initiated from a recognized and registered customer device."

        elif feature == "is_new_receiver":
            if value == 1:
                return "Funds sent to a previously unseen recipient account."
            return "Recipient has prior transaction history with customer."

        elif feature == "location_changed":
            if value == 1:
                return "Transaction location differs significantly from the customer's typical geographic baseline."
            return "Transaction originated from the customer's standard geographical region."

        elif feature == "transactions_last_1h":
            if value >= 5:
                return f"High short-term velocity ({int(value)} transactions in the past hour), indicating burst activity."
            return f"Normal velocity in the last hour ({int(value)} transactions)."

        elif feature == "failed_attempts":
            if value > 0:
                return f"Preceded by {int(value)} failed authentication or verification attempts."
            return "No preceding failed authentication attempts recorded."

        elif feature == "receiver_transaction_count":
            if value < 5:
                return f"Recipient account has minimal prior network history ({int(value)} prior transactions)."
            return f"Recipient has established network history ({int(value)} past transactions)."

        elif feature == "account_age_days":
            if value < 60:
                return f"New account opened only {int(value)} days ago."
            return f"Mature account with {int(value)} days of operating tenure."

        elif feature == "amount":
            return f"Transaction amount of ৳{value:,.2f} {direction} risk profile."

        elif feature == "hour":
            return f"Transaction scheduled at {int(value):02d}:00 hours."

        return f"{FEATURE_DESCRIPTIONS.get(feature, feature)} ({value}) {direction} risk score."

    def explain_prediction(self, feature_data: Dict[str, Any], top_k: int = 6) -> List[Dict[str, Any]]:
        """Wraps explain for raw dictionary feature payloads."""
        row = {}
        for feature in self.feature_names:
            val = feature_data.get(feature, 0.0)
            row[feature] = [float(val) if val is not None else 0.0]
        df_features = pd.DataFrame(row)
        return self.explain(df_features, top_k=top_k)

    def explain_detailed(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decomposes prediction into explicit Risk Increasing (+SHAP)
        and Risk Reducing (-SHAP) factor groups with exact numerical attributions.
        """
        row = {}
        for feature in self.feature_names:
            val = feature_data.get(feature, 0.0)
            row[feature] = [float(val) if val is not None else 0.0]
        df_features = pd.DataFrame(row)

        shap_values = self.explainer(df_features)
        values = shap_values.values[0]

        increasing = []
        reducing = []

        for idx, feature in enumerate(self.feature_names):
            val = float(values[idx])
            raw_val = df_features[feature].iloc[0]
            expl = self._generate_factor_explanation(feature, raw_val, val)
            item = {
                "feature": feature,
                "label": feature.replace("_", " ").title(),
                "shap_value": round(val, 4),
                "points_delta": f"{'+' if val >= 0 else ''}{round(val * 10.0, 1)} pts",
                "feature_value": round(float(raw_val), 2) if isinstance(raw_val, (int, float, np.number)) else str(raw_val),
                "explanation": expl
            }

            if val > 0:
                increasing.append(item)
            elif val < 0:
                reducing.append(item)

        increasing.sort(key=lambda x: x["shap_value"], reverse=True)
        reducing.sort(key=lambda x: x["shap_value"])  # most negative first

        return {
            "top_risk_increasing": increasing,
            "top_risk_reducing": reducing,
            "base_value": round(float(self.explainer.expected_value), 4) if hasattr(self.explainer, "expected_value") else 0.0
        }


shap_service = SHAPService()
