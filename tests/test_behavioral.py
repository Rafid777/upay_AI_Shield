"""
Unit tests for Behavioral Intelligence and Network Graph Services.
"""

import pytest
from backend.database import SessionLocal
from backend.services.behavioral_service import behavioral_service
from backend.services.network_service import network_service


def test_customer_baseline():
    db = SessionLocal()
    try:
        baseline = behavioral_service.get_customer_baseline(db, "CUST02042")
        assert baseline["customer_id"] == "CUST02042"
        assert baseline["average_amount"] > 0
        assert baseline["known_devices_count"] >= 1
    finally:
        db.close()


def test_behavioral_deviation_computation():
    baseline = {
        "customer_id": "CUST_TEST",
        "average_amount": 1000.0,
        "typical_hours": "09:00–21:00",
        "known_devices_count": 2,
        "primary_location": "Dhaka",
        "typical_daily_frequency": 3.0
    }
    tx_data = {
        "amount": 18500.0,
        "amount_deviation": 18.5,
        "is_new_device": 1,
        "is_new_receiver": 1,
        "location_changed": 1,
        "hour": 2,
        "transactions_last_1h": 7,
        "transactions_last_24h": 22
    }
    dev = behavioral_service.compute_behavioral_deviation(baseline, tx_data)
    assert dev["has_significant_deviations"] is True
    assert len(dev["deviations_list"]) >= 4
    assert dev["comparison"]["new_device"] == "YES"
    assert dev["comparison"]["new_receiver"] == "YES"
    assert dev["comparison"]["location_changed"] == "YES"
    assert "৳" in dev["comparison"]["normal_avg_amount"]
    assert "৳" in dev["comparison"]["current_amount"]


def test_network_entity_graph():
    db = SessionLocal()
    try:
        graph = network_service.get_transaction_entity_network(db, "TX103934")
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 4
        assert len(graph["edges"]) >= 3
    finally:
        db.close()
