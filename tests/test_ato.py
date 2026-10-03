"""
Unit tests for Account Takeover (ATO) Intelligence Service.
"""

import pytest
from backend.services.ato_service import ato_service


def test_ato_benign_session():
    tx_data = {
        "is_new_device": 0,
        "location_changed": 0,
        "is_new_receiver": 0,
        "failed_attempts": 0,
        "hour": 14,
        "amount_deviation": 1.0,
        "transactions_last_1h": 1
    }
    result = ato_service.evaluate_ato_signals(tx_data)
    assert result["severity"] == "NONE"
    assert result["signal_count"] == 0
    assert result["ato_score"] == 0


def test_ato_critical_session():
    # Severe ATO combination: new device + location shift + off-hours + failed auth + amount surge + burst velocity
    tx_data = {
        "is_new_device": 1,
        "location_changed": 1,
        "is_new_receiver": 1,
        "failed_attempts": 4,
        "hour": 2,
        "amount_deviation": 9.5,
        "transactions_last_1h": 8
    }
    result = ato_service.evaluate_ato_signals(tx_data)
    assert result["severity"] in ["HIGH", "CRITICAL"]
    assert result["signal_count"] >= 5
    assert result["ato_score"] >= 60
    assert "Potential account takeover indicators detected" in result["headline"]
