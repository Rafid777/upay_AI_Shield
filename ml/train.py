"""
upay AI Shield - XGBoost Training & Model Evaluation
Trains risk classifier with class imbalance handling, computes comprehensive metrics,
generates evaluation visualizations, and serializes model artifacts.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix
)
from xgboost import XGBClassifier

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data_pipeline import DataPipeline, MODEL_FEATURES, TARGET_COLUMN

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def train_and_evaluate(
    model_output_dir: str = "ml/models",
    figures_output_dir: str = "outputs"
) -> dict:
    os.makedirs(model_output_dir, exist_ok=True)
    os.makedirs(figures_output_dir, exist_ok=True)

    pipeline = DataPipeline()
    X_train, X_test, y_train, y_test, meta_train, meta_test = pipeline.prepare_train_test_split(
        test_size=0.2, random_state=42
    )

    # Calculate class imbalance weighting
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / max(pos_count, 1)
    logger.info(f"Class imbalance: {neg_count} negatives vs {pos_count} positives. scale_pos_weight={scale_pos_weight:.2f}")

    # Initialize XGBoost with calibrated hyperparameters
    model = XGBClassifier(
        n_estimators=250,
        learning_rate=0.04,
        max_depth=5,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="auc",
        use_label_encoder=False
    )

    logger.info("Training XGBoost risk classifier...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Predictions and Probabilities
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    # Compute actual metrics
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_pred_proba))

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "test_samples": len(y_test),
        "positive_test_cases": int(y_test.sum())
    }

    logger.info("Evaluation Metrics:")
    for k, v in metrics.items():
        if k != "confusion_matrix":
            logger.info(f"  {k}: {v}")
    logger.info(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # Generate Figures
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Confusion Matrix Plot
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap="Blues", alpha=0.85)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(x=j, y=i, s=str(cm[i, j]), va="center", ha="center", size="xx-large", weight="bold")
    plt.title("Confusion Matrix (Synthetic Benchmark)", pad=20, weight="bold")
    fig.colorbar(cax)
    plt.xlabel("Predicted Label (0: Legitimate, 1: High Risk)", labelpad=10)
    plt.ylabel("Actual Synthetic Label", labelpad=10)
    plt.xticks([0, 1], ["Legitimate", "High Risk"])
    plt.yticks([0, 1], ["Legitimate", "High Risk"])
    plt.tight_layout()
    plt.savefig(os.path.join(figures_output_dir, "confusion_matrix.png"), dpi=200)
    plt.close()

    # 2. ROC Curve Plot
    fpr_curve, tpr_curve, _ = roc_curve(y_test, y_pred_proba)
    plt.figure(figsize=(7, 5))
    plt.plot(fpr_curve, tpr_curve, color="#2563eb", lw=2.5, label=f"XGBoost ROC (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="#94a3b8", lw=1.5, linestyle="--", label="Random Classifier")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate (1 - Specificity)")
    plt.ylabel("True Positive Rate (Sensitivity / Recall)")
    plt.title("Receiver Operating Characteristic (ROC) Curve", weight="bold")
    plt.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_output_dir, "roc_curve.png"), dpi=200)
    plt.close()

    # 3. Feature Importance Plot
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    sorted_features = [MODEL_FEATURES[i] for i in indices]
    sorted_importances = importances[indices]

    plt.figure(figsize=(9, 5.5))
    bars = plt.barh(range(len(sorted_features)), sorted_importances[::-1], color="#0284c7", align="center")
    plt.yticks(range(len(sorted_features)), sorted_features[::-1])
    plt.xlabel("XGBoost Relative Feature Importance")
    plt.title("Key Risk Drivers in Transaction Behavior", weight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(figures_output_dir, "feature_importance.png"), dpi=200)
    plt.close()

    # 4. Class Distribution Plot
    plt.figure(figsize=(6, 4.5))
    classes = ["Legitimate (0)", "Synthetic Flag (1)"]
    counts = [neg_count, pos_count]
    plt.bar(classes, counts, color=["#10b981", "#ef4444"], width=0.45)
    for idx, count in enumerate(counts):
        pct = count / (neg_count + pos_count) * 100
        plt.text(idx, count + 200, f"{count:,}\n({pct:.1f}%)", ha="center", weight="bold")
    plt.title("Dataset Class Distribution (20,000 Transactions)", weight="bold")
    plt.ylabel("Transaction Count")
    plt.ylim(0, max(counts) * 1.15)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_output_dir, "class_distribution.png"), dpi=200)
    plt.close()

    # Save outputs/metrics.json
    metrics_path = os.path.join(figures_output_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # Save ml/models/risk_model.pkl
    model_path = os.path.join(model_output_dir, "risk_model.pkl")
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Generate Feature Schema (ranges, means, std)
    feature_stats = {}
    for col in MODEL_FEATURES:
        feature_stats[col] = {
            "type": str(X_train[col].dtype),
            "min": float(X_train[col].min()),
            "max": float(X_train[col].max()),
            "mean": round(float(X_train[col].mean()), 4),
            "std": round(float(X_train[col].std()), 4)
        }

    schema_path = os.path.join(model_output_dir, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump({
            "features": MODEL_FEATURES,
            "feature_count": len(MODEL_FEATURES),
            "target": TARGET_COLUMN,
            "statistics": feature_stats
        }, f, indent=2)

    # Generate Model Metadata
    model_version = "upay-ai-shield-v1.0.0"
    training_date = datetime.now(timezone.utc).isoformat()
    metadata = {
        "model_name": "upay AI Shield XGBoost Risk Classifier",
        "model_version": model_version,
        "algorithm": "XGBClassifier",
        "training_date": training_date,
        "framework": "xgboost",
        "num_training_rows": len(X_train),
        "num_test_rows": len(X_test),
        "features": MODEL_FEATURES,
        "feature_count": len(MODEL_FEATURES),
        "target": TARGET_COLUMN,
        "evaluation_metrics": metrics,
        "hyperparameters": {
            "n_estimators": 250,
            "learning_rate": 0.04,
            "max_depth": 5,
            "scale_pos_weight": round(scale_pos_weight, 2),
            "random_state": 42
        },
        "risk_thresholds": {
            "low": {"min": 0, "max": 49.99, "action": "CONTINUE"},
            "medium": {"min": 50.0, "max": 79.99, "action": "ADDITIONAL_REVIEW"},
            "high": {"min": 80.0, "max": 100.0, "action": "HUMAN_REVIEW"}
        },
        "governance_note": "The AI model produces risk probability scores. Autonomous blocking/freezing is forbidden; high risk transactions are routed to human analysts."
    }

    metadata_path = os.path.join(model_output_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training and evaluation successfully completed!")
    return metadata


if __name__ == "__main__":
    train_and_evaluate()
