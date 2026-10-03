"""
Tests for Analyst Case Management API routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_case_lifecycle():
    # 1. Get a high risk transaction without an existing case
    tx_res = client.get("/api/v1/transactions?limit=50&risk_level=HIGH")
    cases_res = client.get("/api/v1/cases?limit=100")
    existing_case_txs = {c["transaction_id"] for c in cases_res.json().get("cases", [])}
    
    tx_id = None
    for t in tx_res.json()["transactions"]:
        if t["transaction_id"] not in existing_case_txs:
            tx_id = t["transaction_id"]
            break
    if not tx_id:
        tx_id = "TX115672"

    # 2. Create case
    case_payload = {
        "transaction_id": tx_id,
        "priority": "HIGH",
        "assigned_analyst": "analyst_shafi",
        "analyst_notes": "Triggered by high-velocity new device burst."
    }
    create_res = client.post("/api/v1/cases", json=case_payload)
    assert create_res.status_code in [200, 201]
    case_data = create_res.json()
    case_id = case_data["case_id"]
    assert case_data["transaction_id"] == tx_id
    assert case_data["status"] == "OPEN"

    # 3. Retrieve single case
    get_res = client.get(f"/api/v1/cases/{case_id}")
    assert get_res.status_code == 200
    assert get_res.json()["case_id"] == case_id
    assert len(get_res.json().get("events", [])) >= 1

    # 4. List cases
    list_res = client.get("/api/v1/cases?status=OPEN")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 5. Patch case (move to UNDER_REVIEW)
    patch_res = client.patch(f"/api/v1/cases/{case_id}", json={
        "status": "UNDER_REVIEW",
        "analyst_notes": "Customer contact initiated via registered phone number."
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "UNDER_REVIEW"

    # 6. Record human decision
    decision_res = client.post(f"/api/v1/cases/{case_id}/decision", json={
        "decision": "CONFIRM_SUSPICIOUS",
        "analyst_notes": "Customer reported unapproved SIM swap and device loss.",
        "analyst_id": "analyst_shafi"
    })
    assert decision_res.status_code == 200
    assert decision_res.json()["decision"] == "CONFIRM_SUSPICIOUS"
    assert decision_res.json()["status"] == "RESOLVED"
