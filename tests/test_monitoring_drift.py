"""
Tests for Model Monitoring, Data Drift, and Retraining Export routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_model_health_endpoint():
    response = client.get("/api/v1/model/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] != ""
    assert data["algorithm"] == "XGBClassifier"
    assert data["training_samples"] == 16000
    assert data["test_samples"] == 4000
    assert "evaluation_metrics" in data
    assert "precision" in data["evaluation_metrics"]
    assert "recall" in data["evaluation_metrics"]
    assert "f1_score" in data["evaluation_metrics"]
    assert "roc_auc" in data["evaluation_metrics"]
    assert len(data["feature_importance"]) == 12
    assert len(data["trained_features"]) == 12


def test_data_drift_endpoint():
    response = client.get("/api/v1/model/drift")
    assert response.status_code == 200
    data = response.json()
    assert "overall_drift_status" in data
    assert data["overall_drift_status"] in ["LOW", "MEDIUM", "HIGH", "INSUFFICIENT_DATA"]
    assert "features_drift" in data
    assert "status_message" in data


def test_retraining_dataset_export():
    response = client.post("/api/v1/feedback/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    content = response.text
    assert "transaction_id" in content
    assert "amount_bdt" in content
    assert "analyst_decision" in content
