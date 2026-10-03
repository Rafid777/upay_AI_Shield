"""
upay AI Shield - Investigation Service
Orchestrates transaction context, customer baselines, behavioral deviations,
ATO intelligence, XGBoost predictions, SHAP explainability, and Gemini AI assistant.
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import Transaction, Customer, RiskPrediction, Investigation
from backend.services.model_service import model_service
from backend.services.shap_service import shap_service
from backend.services.gemini_service import gemini_service
from backend.services.behavioral_service import behavioral_service
from backend.services.ato_service import ato_service
from backend.services.network_service import network_service
from backend.services.scam_service import scam_service
from backend.services.timeline_service import timeline_service
from backend.services.risk_fusion_service import risk_fusion
from src.data_pipeline import MODEL_FEATURES

logger = logging.getLogger(__name__)


class InvestigationService:

    @staticmethod
    def get_or_run_prediction(db: Session, transaction: Transaction) -> Dict[str, Any]:
        """Ensures a risk prediction and SHAP factors exist for the transaction."""
        db_pred = db.query(RiskPrediction).filter(RiskPrediction.transaction_id == transaction.transaction_id).first()
        
        feature_dict = {f: getattr(transaction, f, 0.0) for f in MODEL_FEATURES}

        if db_pred and db_pred.shap_factors:
            df_features = model_service.predict(feature_dict)["features_df"]
            return {
                "risk_probability": db_pred.risk_probability,
                "risk_score": db_pred.risk_score,
                "risk_level": db_pred.risk_level,
                "recommended_action": db_pred.recommended_action,
                "model_version": db_pred.model_version,
                "shap_factors": db_pred.shap_factors,
                "features_df": df_features
            }

        pred_res = model_service.predict(feature_dict)
        shap_factors = shap_service.explain(pred_res["features_df"], top_k=6)
        pred_res["shap_factors"] = shap_factors

        new_pred = RiskPrediction(
            transaction_id=transaction.transaction_id,
            model_version=pred_res["model_version"],
            risk_probability=pred_res["risk_probability"],
            risk_score=pred_res["risk_score"],
            risk_level=pred_res["risk_level"],
            recommended_action=pred_res["recommended_action"],
            shap_factors=shap_factors
        )
        db.add(new_pred)
        db.commit()

        return pred_res

    @staticmethod
    def investigate_transaction(db: Session, transaction_id: str) -> Dict[str, Any]:
        """
        Comprehensive investigation pipeline:
        Transaction Facts + Baseline + Deviations + ATO Signals + Scam Patterns + Risk Story + SHAP + Gemini AI Brief.
        """
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not tx:
            raise ValueError(f"Transaction '{transaction_id}' not found.")

        # Compute empirical customer baseline and deviations
        cust_id = tx.customer_id or "CUST_DEFAULT"
        baseline = behavioral_service.get_customer_baseline(db, cust_id)

        tx_dict = {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "amount": tx.amount,
            "timestamp": tx.timestamp,
            "channel": tx.channel,
            "transaction_type": tx.transaction_type,
            "hour": tx.hour,
            "receiver_id": tx.receiver_id,
            "device_id": tx.device_id,
            "location": tx.location,
            "is_new_receiver": tx.is_new_receiver,
            "is_new_device": tx.is_new_device,
            "location_changed": tx.location_changed,
            "transactions_last_1h": tx.transactions_last_1h,
            "transactions_last_24h": tx.transactions_last_24h,
            "failed_attempts": tx.failed_attempts,
            "amount_deviation": tx.amount_deviation
        }

        deviations = behavioral_service.compute_behavioral_deviation(baseline, tx_dict)
        ato_signals = ato_service.evaluate_ato_signals(tx_dict)
        scam_patterns = scam_service.analyze_scam_patterns(tx_dict, baseline)
        pred_data = InvestigationService.get_or_run_prediction(db, tx)
        risk_story = timeline_service.generate_risk_story(db, transaction_id, pred_data["risk_score"], pred_data["risk_level"])
        entity_network = network_service.get_transaction_entity_network(db, transaction_id)

        # Run Hybrid Risk Fusion
        fusion_data = risk_fusion.fuse_risk_assessment(
            transaction_data=tx_dict,
            customer_baseline=baseline,
            network_data=entity_network
        )
        shap_detailed = shap_service.explain_detailed(tx_dict)

        # Check existing investigation in DB
        existing_inv = db.query(Investigation).filter(Investigation.transaction_id == transaction_id).first()
        if existing_inv and existing_inv.summary and existing_inv.ato_indicators:
            return {
                "transaction_id": tx.transaction_id,
                "summary": existing_inv.summary,
                "risk_context": existing_inv.risk_context,
                "risk_signals": existing_inv.key_findings or [],
                "key_findings": existing_inv.key_findings or [],
                "behavioral_deviations": existing_inv.behavioral_deviations or deviations.get("deviations_list", []),
                "ato_indicators": [s["label"] for s in ato_signals.get("detected_signals", [])],
                "scam_patterns": [p["pattern_name"] for p in scam_patterns.get("patterns_detected", [])],
                "network_observations": [i.get("description", i.get("pattern", "Connected entity")) for i in entity_network.get("insights", [])],
                "investigation_questions": existing_inv.investigation_questions or existing_inv.evidence_to_review or [],
                "evidence_to_review": existing_inv.evidence_to_review or existing_inv.investigation_questions or [],
                "recommended_action": existing_inv.recommended_action,
                "confidence_note": "Evaluated with XGBoost + Isolation Forest + SHAP TreeExplainer and Gemini 2.5 Flash.",
                "human_review_required": pred_data["risk_score"] >= 50.0,
                "customer_baseline": baseline,
                "behavioral_comparison": deviations.get("comparison", {}),
                "ato_intelligence": ato_signals,
                "scam_intelligence": scam_patterns,
                "risk_story": risk_story,
                "network_graph": entity_network,
                "risk_fusion": fusion_data,
                "component_scores": fusion_data.get("component_scores", {}),
                "shap_detailed": shap_detailed,
                "top_risk_increasing": shap_detailed.get("top_risk_increasing", [])[:5],
                "top_risk_reducing": shap_detailed.get("top_risk_reducing", [])[:3],
                "is_ai_generated": True,
                "notice": "Retrieved from investigation repository."
            }

        # Generate fresh Gemini investigation
        investigation_res = gemini_service.generate_investigation(
            transaction_data=tx_dict,
            prediction_result=pred_data,
            shap_factors=pred_data["shap_factors"],
            customer_baseline=baseline,
            behavioral_deviations=deviations,
            ato_signals=ato_signals,
            scam_patterns=scam_patterns,
            risk_story=risk_story,
            network_graph=entity_network
        )

        # Attach auxiliary analytics
        investigation_res["customer_baseline"] = baseline
        investigation_res["behavioral_comparison"] = deviations.get("comparison", {})
        investigation_res["ato_intelligence"] = ato_signals
        investigation_res["scam_intelligence"] = scam_patterns
        investigation_res["risk_story"] = risk_story
        investigation_res["network_graph"] = entity_network
        investigation_res["risk_fusion"] = fusion_data
        investigation_res["component_scores"] = fusion_data.get("component_scores", {})
        investigation_res["shap_detailed"] = shap_detailed
        investigation_res["top_risk_increasing"] = shap_detailed.get("top_risk_increasing", [])[:5]
        investigation_res["top_risk_reducing"] = shap_detailed.get("top_risk_reducing", [])[:3]

        # Save to DB
        inv_record = Investigation(
            transaction_id=tx.transaction_id,
            summary=investigation_res.get("summary", ""),
            risk_context=investigation_res.get("risk_context", {}),
            key_findings=investigation_res.get("risk_signals", investigation_res.get("key_findings", [])),
            evidence_to_review=investigation_res.get("investigation_questions", investigation_res.get("evidence_to_review", [])),
            behavioral_deviations=investigation_res.get("behavioral_deviations", deviations.get("deviations_list", [])),
            ato_indicators=ato_signals,
            investigation_questions=investigation_res.get("investigation_questions", []),
            recommended_action=investigation_res.get("recommended_action", "HUMAN_REVIEW"),
            raw_response=investigation_res
        )
        db.add(inv_record)
        db.commit()

        return investigation_res

    @staticmethod
    def chat_with_assistant(db: Session, transaction_id: str, message: str) -> Dict[str, Any]:
        """Provides transaction-aware conversational Q&A for analysts."""
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not tx:
            raise ValueError(f"Transaction '{transaction_id}' not found.")

        # Ensure investigation and baselines exist
        inv_data = InvestigationService.investigate_transaction(db, transaction_id)
        pred_data = InvestigationService.get_or_run_prediction(db, tx)
        baseline = behavioral_service.get_customer_baseline(db, tx.customer_id or "CUST_DEFAULT")
        ato_signals = ato_service.evaluate_ato_signals({
            "is_new_device": tx.is_new_device,
            "location_changed": tx.location_changed,
            "is_new_receiver": tx.is_new_receiver,
            "failed_attempts": tx.failed_attempts,
            "hour": tx.hour,
            "amount_deviation": tx.amount_deviation,
            "transactions_last_1h": tx.transactions_last_1h
        })

        tx_dict = {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "amount": tx.amount,
            "amount_deviation": tx.amount_deviation,
            "is_new_device": tx.is_new_device,
            "is_new_receiver": tx.is_new_receiver,
            "location_changed": tx.location_changed,
            "failed_attempts": tx.failed_attempts,
            "hour": tx.hour,
            "channel": tx.channel,
            "transactions_last_1h": tx.transactions_last_1h
        }

        return gemini_service.answer_chat_query(
            transaction_id=transaction_id,
            user_query=message,
            investigation_data=inv_data,
            transaction_data=tx_dict,
            shap_factors=pred_data["shap_factors"],
            baseline_data=baseline,
            ato_signals=ato_signals
        )


investigation_service = InvestigationService()
