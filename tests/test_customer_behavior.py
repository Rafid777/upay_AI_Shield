"""
Tests for Customer Behavior Profiles and Timeline Risk Story routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_customer_behavior_profile():
    # Fetch a real customer from transactions
    tx_res = client.get("/api/v1/transactions?limit=1")
    tx = tx_res.json()["transactions"][0]
    cust_id = tx["customer_id"]

    response = client.get(f"/api/v1/customers/{cust_id}/behavior")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == cust_id
    assert "normal_behavior" in data
    assert "average_amount" in data["normal_behavior"]
    assert "average_amount_display" in data["normal_behavior"]
    assert "typical_hours" in data["normal_behavior"]
    assert "known_devices_count" in data["normal_behavior"]
    assert "known_receivers_count" in data["normal_behavior"]
    assert len(data["recent_transactions"]) > 0


def test_customer_network_endpoint():
    tx_res = client.get("/api/v1/transactions?limit=1")
    tx = tx_res.json()["transactions"][0]
    cust_id = tx["customer_id"]

    response = client.get(f"/api/v1/customers/{cust_id}/network")
    assert response.status_code == 200
    data = response.json()
    assert "customer_id" in data
    assert "nodes" in data
    assert "edges" in data
    assert "network_risk_indicators" in data
    assert len(data["nodes"]) >= 1


def test_risk_story_timeline():
    tx_res = client.get("/api/v1/transactions?limit=1&risk_level=HIGH")
    tx_id = tx_res.json()["transactions"][0]["transaction_id"]

    response = client.get(f"/api/v1/transactions/{tx_id}/risk-story")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == tx_id
    assert "timeline_events" in data
    assert len(data["timeline_events"]) >= 3
    assert "headline" in data
    assert "narrative_summary" in data
