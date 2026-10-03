"""
upay AI Shield - Model Monitoring & Governance Routes
Provides endpoints for Model Health & Evaluation Metrics, and Statistical Data Drift Monitoring.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import ModelHealthResponse, ModelDriftResponse
from backend.services.model_service import model_service
from backend.services.drift_service import DataDriftService
from src.data_pipeline import MODEL_FEATURES

router = APIRouter(prefix="/model", tags=["Model Monitoring & Governance"])
drift_service = DataDriftService()


@router.get("/health", response_model=ModelHealthResponse)
def get_model_health():
    """
    Returns empirical model performance metrics, training configuration, hyperparameters,
    and feature importance extracted directly from the trained XGBoost model.
    """
    meta = model_service.get_metadata()
    model = model_service.get_model()

    # Extract actual feature importances
    feature_importance: List[Dict[str, Any]] = []
    if hasattr(model, "feature_importances_"):
        raw_importances = model.feature_importances_
        for feat, imp in zip(MODEL_FEATURES, raw_importances):
            feature_importance.append({
                "feature": feat,
                "importance": round(float(imp), 4),
                "feature_name": feat.replace("_", " ").title()
            })
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)

    eval_metrics = meta.get("evaluation_metrics", {})

    return ModelHealthResponse(
        model_name=meta.get("model_name", "upay AI Shield XGBoost Risk Classifier"),
        version=meta.get("model_version", "upay-ai-shield-v1.0.0"),
        algorithm=meta.get("algorithm", "XGBClassifier"),
        status="ACTIVE_PRODUCTION",
        training_samples=meta.get("num_training_rows", 16000),
        test_samples=meta.get("num_test_rows", 4000),
        evaluation_metrics=eval_metrics,
        feature_importance=feature_importance,
        hyperparameters=meta.get("hyperparameters", {}),
        trained_features=meta.get("features", MODEL_FEATURES)
    )


@router.get("/drift", response_model=ModelDriftResponse)
def get_data_drift(db: Session = Depends(get_db)):
    """
    Computes statistical data drift using Normalized Absolute Mean Shift (NAMS)
    comparing reference training baseline against recent transactions.
    """
    result = drift_service.evaluate_drift(db=db, sample_limit=1000)
    return result


@router.get("/thresholds")
def get_threshold_analysis():
    """
    Evaluates XGBoost model precision, recall, F1, FPR, and FNR across multiple
    decision thresholds (0.30, 0.50, 0.70, 0.80) using holdout test data.
    Clearly states this is for model analysis only.
    """
    import os
    import pandas as pd
    import numpy as np

    test_path = "data/processed/test.csv"
    if not os.path.exists(test_path):
        return {
            "error": "Holdout test dataset not found",
            "thresholds": []
        }

    df = pd.read_csv(test_path)
    X_test = df[MODEL_FEATURES]
    y_true = df["is_fraud"].values

    model = model_service.get_model()
    y_probs = model.predict_proba(X_test)[:, 1]

    threshold_values = [0.30, 0.50, 0.70, 0.80]
    metrics_list = []

    for t in threshold_values:
        y_pred = (y_probs >= t).astype(int)
        tp = int(np.sum((y_pred == 1) & (y_true == 1)))
        fp = int(np.sum((y_pred == 1) & (y_true == 0)))
        fn = int(np.sum((y_pred == 0) & (y_true == 1)))
        tn = int(np.sum((y_pred == 0) & (y_true == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0

        metrics_list.append({
            "threshold": t,
            "threshold_label": f"{int(t * 100)}%",
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "confusion_matrix": {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn
            }
        })

    return {
        "model_name": "upay AI Shield XGBoost Risk Classifier",
        "evaluation_samples": len(df),
        "positive_cases": int(np.sum(y_true == 1)),
        "negative_cases": int(np.sum(y_true == 0)),
        "threshold_metrics": metrics_list,
        "disclaimer": "Threshold analysis is provided for model exploration and trade-off visibility only. No single threshold is universally optimal across all payment channels."
    }
