"""
upay AI Shield - What-If Risk Simulator Service
Allows fraud analysts to counterfactually modify telemetry signals (e.g. toggle New Device, Location, Amount)
and evaluate the real-time XGBoost probability delta.

IMPORTANT:
Does NOT fabricate or hardcode point deltas. All simulated scores are derived
from direct model.predict_proba inference on the modified feature vector.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import Transaction
from backend.services.model_service import model_service
from backend.services.shap_service import shap_service


class WhatIfSimulatorService:
    def simulate_what_if(
        self,
        db: Optional[Session],
        transaction_id: Optional[str],
        base_features: Optional[Dict[str, Any]],
        modified_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. Resolve base features
        resolved_base = {}
        if transaction_id and db:
            tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
            if tx:
                resolved_base = {
                    "amount": float(tx.amount),
                    "hour": int(tx.hour),
                    "day_of_week": int(tx.day_of_week),
                    "is_new_receiver": int(tx.is_new_receiver),
                    "is_new_device": int(tx.is_new_device),
                    "location_changed": int(tx.location_changed),
                    "transactions_last_1h": int(tx.transactions_last_1h),
                    "transactions_last_24h": int(tx.transactions_last_24h),
                    "failed_attempts": int(tx.failed_attempts),
                    "account_age_days": int(tx.account_age_days),
                    "receiver_transaction_count": int(tx.receiver_transaction_count),
                    "amount_deviation": float(tx.amount_deviation)
                }

        if not resolved_base and base_features:
            resolved_base = dict(base_features)

        if not resolved_base:
            # Fallback to standard baseline profile
            resolved_base = {
                "amount": 18500.0,
                "hour": 2,
                "day_of_week": 4,
                "is_new_receiver": 1,
                "is_new_device": 1,
                "location_changed": 1,
                "transactions_last_1h": 8,
                "transactions_last_24h": 22,
                "failed_attempts": 3,
                "account_age_days": 45,
                "receiver_transaction_count": 1,
                "amount_deviation": 14.8
            }

        # 2. Run original prediction
        orig_pred = model_service.predict_risk(resolved_base)
        orig_score = float(orig_pred["risk_score"])
        orig_level = str(orig_pred["risk_level"])
        orig_shap = shap_service.explain_prediction(resolved_base)

        # 3. Construct modified features
        sim_features = dict(resolved_base)
        changed_details = {}

        for k, v in modified_features.items():
            if k in sim_features and sim_features[k] != v:
                changed_details[k] = {
                    "original": sim_features[k],
                    "simulated": v
                }
                sim_features[k] = v

        # 4. Run simulated prediction on modified vector
        sim_pred = model_service.predict_risk(sim_features)
        sim_score = float(sim_pred["risk_score"])
        sim_level = str(sim_pred["risk_level"])
        sim_shap = shap_service.explain_prediction(sim_features)

        score_delta = round(sim_score - orig_score, 1)

        # 5. Calculate top changed risk factors
        orig_shap_dict = {f["feature"]: f["shap_value"] for f in orig_shap}
        sim_shap_dict = {f["feature"]: f["shap_value"] for f in sim_shap}

        factor_changes = []
        for feat, diff in changed_details.items():
            o_shap = orig_shap_dict.get(feat, 0.0)
            s_shap = sim_shap_dict.get(feat, 0.0)
            direction = "RISK_REDUCED" if s_shap < o_shap else "RISK_ELEVATED"
            factor_changes.append({
                "feature": feat,
                "original_value": diff["original"],
                "modified_value": diff["simulated"],
                "direction": direction
            })

        return {
            "original_risk_score": orig_score,
            "original_risk_level": orig_level,
            "simulated_risk_score": sim_score,
            "simulated_risk_level": sim_level,
            "score_delta": score_delta,
            "risk_level_changed": orig_level != sim_level,
            "changed_features": changed_details,
            "top_changed_factors": factor_changes,
            "disclaimer": "Simulation only — not a production transaction decision."
        }


what_if_service = WhatIfSimulatorService()
