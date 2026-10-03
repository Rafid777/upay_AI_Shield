"""
Unit tests for Gemini AI Investigation Assistant and safe fallback mechanisms.
"""

import pytest
from backend.services.gemini_service import gemini_service, GeminiInvestigationService


def test_gemini_service_initialization():
    assert gemini_service is not None
    assert gemini_service.model_name == "gemini-2.5-flash"


def test_safe_fallback_generation():
    service = GeminiInvestigationService()
    
    # Simulate a transaction
    tx_data = {
        "transaction_id": "TX_TEST_999",
        "amount": 18500.0,
        "amount_deviation": 7.5,
        "is_new_device": 1,
        "is_new_receiver": 1,
        "location_changed": 1,
        "transactions_last_1h": 6
    }
    pred_data = {
        "risk_probability": 0.92,
        "risk_score": 92.0,
        "risk_level": "HIGH",
        "recommended_action": "HUMAN_REVIEW"
    }
    shap_factors = [
        {
            "feature": "amount_deviation",
            "shap_value": 2.15,
            "feature_value": 7.5,
            "impact": "RISK_INCREASING",
            "explanation": "High amount deviation (7.5x normal baseline) elevates risk."
        },
        {
            "feature": "is_new_device",
            "shap_value": 1.45,
            "feature_value": 1,
            "impact": "RISK_INCREASING",
            "explanation": "Initiated from a newly detected device."
        }
    ]

    fallback = service._generate_safe_fallback(
        tx_id="TX_TEST_999",
        risk_score=92.0,
        risk_level="HIGH",
        action="HUMAN_REVIEW",
        shap_factors=shap_factors,
        tx_data=tx_data
    )

    assert fallback["transaction_id"] == "TX_TEST_999"
    assert fallback["risk_context"]["risk_score"] == 92.0
    assert fallback["risk_context"]["risk_level"] == "HIGH"
    assert len(fallback["key_findings"]) >= 2
    assert len(fallback["evidence_to_review"]) >= 2
    assert fallback["recommended_action"] == "HUMAN_REVIEW"
    assert "human analyst" in fallback["summary"].lower()
    assert any("৳" in q for q in fallback["investigation_questions"])


def test_fallback_chat_reply():
    service = GeminiInvestigationService()
    tx_data = {"transaction_id": "TX_TEST_999", "amount_deviation": 8.0}
    shap_factors = [{
        "feature": "amount_deviation",
        "shap_value": 3.2,
        "feature_value": 8.0,
        "impact": "RISK_INCREASING",
        "explanation": "High deviation from historical average."
    }]

    reply = service._generate_fallback_chat_reply(
        query="Why was this transaction flagged?",
        tx_data=tx_data,
        shap_factors=shap_factors,
        risk_score=89.5,
        risk_level="HIGH"
    )

    assert "89.5" in reply or "HIGH" in reply
    assert "deviation" in reply.lower()
