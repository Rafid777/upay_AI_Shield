"""
Unit tests for XGBoost inference, risk scoring categories, and SHAP explainability.
"""

import pytest
import pandas as pd
from backend.services.model_service import model_service
from backend.services.shap_service import shap_service


def test_model_loaded():
    model = model_service.get_model()
    assert model is not None
    meta = model_service.get_metadata()
    assert "model_version" in meta
    assert len(meta.get("features", [])) == 12


def test_low_risk_prediction():
    # Normal benign baseline
    features = {
        "amount": 250.0,
        "hour": 14,
        "day_of_week": 2,
        "is_new_receiver": 0,
        "is_new_device": 0,
        "location_changed": 0,
        "transactions_last_1h": 1,
        "transactions_last_24h": 3,
        "failed_attempts": 0,
        "account_age_days": 1200,
        "receiver_transaction_count": 45,
        "amount_deviation": 0.8
    }
    result = model_service.predict(features)
    assert result["risk_score"] < 50.0
    assert result["risk_level"] == "LOW"
    assert result["recommended_action"] == "CONTINUE"


def test_high_risk_prediction():
    # Severe anomaly pattern
    features = {
        "amount": 28500.0,
        "hour": 3,
        "day_of_week": 6,
        "is_new_receiver": 1,
        "is_new_device": 1,
        "location_changed": 1,
        "transactions_last_1h": 9,
        "transactions_last_24h": 38,
        "failed_attempts": 4,
        "account_age_days": 25,
        "receiver_transaction_count": 0,
        "amount_deviation": 12.5
    }
    result = model_service.predict(features)
    assert result["risk_score"] >= 80.0
    assert result["risk_level"] == "HIGH"
    assert result["recommended_action"] == "HUMAN_REVIEW"


def test_shap_explanation():
    features = {
        "amount": 15000.0,
        "hour": 2,
        "day_of_week": 5,
        "is_new_receiver": 1,
        "is_new_device": 1,
        "location_changed": 1,
        "transactions_last_1h": 6,
        "transactions_last_24h": 22,
        "failed_attempts": 3,
        "account_age_days": 40,
        "receiver_transaction_count": 1,
        "amount_deviation": 8.0
    }
    pred_res = model_service.predict(features)
    factors = shap_service.explain(pred_res["features_df"], top_k=6)

    assert len(factors) == 6
    for f in factors:
        assert "feature" in f
        assert "shap_value" in f
        assert "impact" in f
        assert f["impact"] in ["RISK_INCREASING", "RISK_REDUCING"]
        assert "explanation" in f
        assert len(f["explanation"]) > 5
