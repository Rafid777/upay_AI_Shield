"""
Integration tests for FastAPI endpoints, request validations, and feedback loop.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "governance" in data
    assert data["governance"]["autonomous_blocking_allowed"] is False


def test_dashboard_stats_endpoint():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] >= 20000
    assert "high_risk" in data
    assert "medium_risk" in data
    assert "low_risk" in data
    assert len(data["recent_high_risk"]) > 0


def test_transactions_listing():
    response = client.get("/api/v1/transactions?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["transactions"]) == 10


def test_single_transaction_valid():
    response = client.get("/api/v1/transactions/TX100001")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TX100001"
    assert "amount" in data


def test_single_transaction_not_found():
    response = client.get("/api/v1/transactions/NON_EXISTENT_9999")
    assert response.status_code == 404


def test_predict_existing_transaction():
    response = client.post("/api/v1/predict", json={"transaction_id": "TX100001"})
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "shap_factors" in data
    assert len(data["shap_factors"]) > 0


def test_predict_custom_payload():
    payload = {
        "features": {
            "amount": 5000.0,
            "hour": 14,
            "day_of_week": 2,
            "is_new_receiver": 0,
            "is_new_device": 0,
            "location_changed": 0,
            "transactions_last_1h": 1,
            "transactions_last_24h": 4,
            "failed_attempts": 0,
            "account_age_days": 500,
            "receiver_transaction_count": 20,
            "amount_deviation": 1.2
        }
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(data["shap_factors"]) == 6


def test_predict_invalid_payload():
    # Empty payload
    response = client.post("/api/v1/predict", json={})
    assert response.status_code == 400


def test_investigate_endpoint():
    response = client.post("/api/v1/investigate", json={"transaction_id": "TX100001"})
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TX100001"
    assert "summary" in data
    assert "key_findings" in data
    assert "evidence_to_review" in data
    assert "recommended_action" in data


def test_chat_endpoint():
    response = client.post("/api/v1/chat", json={
        "transaction_id": "TX100001",
        "message": "Why was this transaction evaluated at this risk level?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TX100001"
    assert len(data["reply"]) > 10


def test_feedback_endpoint():
    payload = {
        "transaction_id": "TX100001",
        "decision": "SUSPICIOUS",
        "comment": "Unusual burst activity verified with user.",
        "analyst_id": "analyst_tester"
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_id"] == "TX100001"
    assert data["decision"] == "SUSPICIOUS"
    assert data["comment"] == "Unusual burst activity verified with user."


def test_feedback_invalid_transaction():
    payload = {
        "transaction_id": "INVALID_TX_999",
        "decision": "LEGITIMATE",
        "comment": "Test"
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 404


def test_feedback_stats_endpoint():
    response = client.get("/api/v1/feedback/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_reviewed" in data
    assert "confirmed_suspicious" in data


def test_network_patterns_endpoint():
    response = client.get("/api/v1/network/patterns")
    assert response.status_code == 200
    data = response.json()
    assert "high_fan_in_beneficiaries" in data
    assert "cross_account_shared_devices" in data


def test_network_graph_endpoint():
    response = client.get("/api/v1/network/graph/TX100001")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 4

