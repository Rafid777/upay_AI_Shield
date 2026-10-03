"""
Tests for Scam Pattern Intelligence Engine and API routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.scam_service import scam_service

client = TestClient(app)


def test_scam_pattern_detection_high_value():
    tx = {
        "transaction_id": "TX_TEST_1",
        "amount": 25000.0,
        "amount_deviation": 12.0,
        "is_new_receiver": 1,
        "is_new_device": 1,
        "transactions_last_1h": 6,
        "hour": 2,
        "failed_attempts": 3,
        "location_changed": 1
    }
    baseline = {"average_amount": 1200.0, "typical_hours": "09:00-21:00"}
    
    res = scam_service.analyze_scam_patterns(tx, baseline)
    assert len(res["patterns_detected"]) >= 4
    assert res["highest_severity"] in ["HIGH", "CRITICAL"]
    pattern_codes = [p["pattern_code"] for p in res["patterns_detected"]]
    assert "UNUSUAL_HIGH_VALUE_TRANSFER" in pattern_codes
    assert "NEW_RECEIVER_TRANSFER" in pattern_codes
    assert "SUSPICIOUS_TIME_ACTIVITY" in pattern_codes
    assert "NEW_DEVICE_TRANSFER" in pattern_codes


def test_scam_intelligence_api_endpoint():
    # Use existing transaction from database
    response = client.get("/api/v1/transactions?limit=1&risk_level=HIGH")
    assert response.status_code == 200
    tx_id = response.json()["transactions"][0]["transaction_id"]

    res = client.get(f"/api/v1/transactions/{tx_id}/scam-intelligence")
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_id"] == tx_id
    assert "patterns_detected" in data
    assert "highest_severity" in data
    assert "status" in data
    assert "investigation_guidance" in data


def test_scam_intelligence_invalid_tx():
    res = client.get("/api/v1/transactions/TX_NONEXISTENT_999/scam-intelligence")
    assert res.status_code == 404
