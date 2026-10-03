"""
upay AI Shield V3 - Unsupervised Anomaly Detection Training Script
Trains an Isolation Forest model on normal financial behavior (is_fraud == 0)
to detect subtle out-of-distribution patterns without relying on synthetic fraud labels.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest

import sys
sys.path.insert(0, os.path.abspath("."))

from backend.services.feature_engineering import feature_pipeline, ANOMALY_FEATURE_ORDER


DATA_PATH = "data/raw/upay_ai_shield_20000_transactions.csv"
MODEL_DIR = "ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "anomaly_metadata.json")


def train_anomaly_model():
    print(f"[1/4] Loading transaction dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    total_tx = len(df)

    # Filter to normal behavioral data where appropriate
    normal_df = df[df["is_fraud"] == 0].copy()
    normal_count = len(normal_df)
    print(f"Total transactions: {total_tx}, Normal transactions used for fitting: {normal_count}")

    print("[2/4] Engineering behavioral anomaly feature vectors...")
    records = normal_df.to_dict(orient="records")
    feature_rows = []
    for r in records:
        f = feature_pipeline.engineer_features(r)
        vec = feature_pipeline.extract_anomaly_vector(f)
        feature_rows.append(vec)

    X_train = np.array(feature_rows)
    print(f"Training feature matrix shape: {X_train.shape}")

    print("[3/4] Fitting Isolation Forest model...")
    # Contamination set to 0.03 representing expected rare anomalous outlier rate
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train)

    # Compute baseline decision function percentiles for calibration
    raw_scores = iso_forest.decision_function(X_train)
    min_score = float(np.min(raw_scores))
    p10_score = float(np.percentile(raw_scores, 10))
    p50_score = float(np.percentile(raw_scores, 50))
    max_score = float(np.max(raw_scores))

    print(f"Calibration percentiles: min={min_score:.4f}, p10={p10_score:.4f}, p50={p50_score:.4f}, max={max_score:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"[4/4] Saving model to {MODEL_PATH}...")
    joblib.dump(iso_forest, MODEL_PATH)

    metadata = {
        "model_name": "upay AI Shield Isolation Forest Anomaly Detector",
        "algorithm": "IsolationForest",
        "version": "v3.0.0-unsupervised",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "training_samples": normal_count,
        "features": ANOMALY_FEATURE_ORDER,
        "n_estimators": 150,
        "contamination": 0.03,
        "calibration": {
            "min_score": min_score,
            "p10_score": p10_score,
            "p50_score": p50_score,
            "max_score": max_score,
        },
        "description": "Unsupervised outlier detector fitted exclusively on normal behavioral patterns to flag structural deviations without label reliance."
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved metadata to {METADATA_PATH}")
    print("Isolation Forest training complete!")


if __name__ == "__main__":
    train_anomaly_model()
