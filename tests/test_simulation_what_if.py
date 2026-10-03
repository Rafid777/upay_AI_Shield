"""
Tests for Live Risk Simulation and What-If Counterfactual API routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulate_live_transaction():
    payload = {
        "amount": 18500.0,
        "transaction_type": "SEND_MONEY",
        "channel": "APP",
        "hour": 2,
        "is_new_device": 1,
        "is_new_receiver": 1,
        "location_changed": 1,
        "transactions_last_1h": 8,
        "transactions_last_24h": 22,
        "failed_attempts": 3,
        "account_age_days": 45,
        "receiver_transaction_count": 1,
        "amount_deviation": 14.8
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert data["risk_score"] > 50.0  # High risk signals
    assert "risk_level" in data
    assert "recommended_action" in data
    assert len(data["top_risk_factors"]) > 0
    assert len(data["shap_explanation"]) > 0
    assert "ato_indicators" in data
    assert "potential_scam_patterns" in data
    assert "Simulation only" in data["disclaimer"]


def test_what_if_counterfactual():
    payload = {
        "base_features": {
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
        },
        "modified_features": {
            "is_new_device": 0,
            "location_changed": 0,
            "is_new_receiver": 0
        }
    }
    response = client.post("/api/v1/what-if", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "original_risk_score" in data
    assert "simulated_risk_score" in data
    assert "score_delta" in data
    # Removing new device, location change, and new receiver should reduce risk
    assert data["simulated_risk_score"] <= data["original_risk_score"]
    assert "changed_features" in data
    assert len(data["top_changed_factors"]) > 0
    assert "Simulation only" in data["disclaimer"]


def test_what_if_from_transaction_id():
    tx_res = client.get("/api/v1/transactions?limit=1&risk_level=HIGH")
    tx_id = tx_res.json()["transactions"][0]["transaction_id"]

    payload = {
        "transaction_id": tx_id,
        "modified_features": {
            "is_new_device": 0,
            "location_changed": 0
        }
    }
    response = client.post("/api/v1/what-if", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "original_risk_score" in data
    assert "simulated_risk_score" in data
    assert "score_delta" in data
