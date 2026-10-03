"""
upay AI Shield - Data Pipeline
Validates, preprocesses, and prepares transaction data for model training.

Target: is_fraud (SYNTHETIC LABEL - Not real-world ground truth)
Features:
  - amount
  - hour
  - day_of_week
  - is_new_receiver
  - is_new_device
  - location_changed
  - transactions_last_1h
  - transactions_last_24h
  - failed_attempts
  - account_age_days
  - receiver_transaction_count
  - amount_deviation
"""

import os
import json
import logging
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Canonical model feature list
MODEL_FEATURES: List[str] = [
    "amount",
    "hour",
    "day_of_week",
    "is_new_receiver",
    "is_new_device",
    "location_changed",
    "transactions_last_1h",
    "transactions_last_24h",
    "failed_attempts",
    "account_age_days",
    "receiver_transaction_count",
    "amount_deviation"
]

TARGET_COLUMN: str = "is_fraud"

# Forbidden columns to prevent target leakage and ID memorization
EXCLUDED_COLUMNS: List[str] = [
    "transaction_id",
    "customer_id",
    "device_id",
    "receiver_id",
    "demo_risk_score",
    "risk_level"
]


class DataPipeline:
    """
    Robust, reusable data pipeline for upay AI Shield.
    Validates schemas, cleans data, checks distributions, and prevents data leakage.
    """

    def __init__(self, raw_data_path: str = "data/raw/upay_ai_shield_20000_transactions.csv"):
        self.raw_data_path = raw_data_path
        self.feature_names = MODEL_FEATURES
        self.target_name = TARGET_COLUMN

    def load_data(self) -> pd.DataFrame:
        """Loads transaction dataset from file."""
        if not os.path.exists(self.raw_data_path):
            fallback = "upay_ai_shield_20000_transactions.csv"
            if os.path.exists(fallback):
                self.raw_data_path = fallback
            else:
                raise FileNotFoundError(f"Dataset not found at {self.raw_data_path}")

        logger.info(f"Loading raw dataset from {self.raw_data_path}...")
        df = pd.read_csv(self.raw_data_path)
        logger.info(f"Successfully loaded dataset with shape: {df.shape}")
        return df

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates schema, null values, duplicates, and numeric value boundaries.
        Returns a validation report.
        """
        logger.info("Running schema and data validation checks...")
        report = {}

        # 1. Missing columns
        missing_features = [f for f in self.feature_names if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing required model features in dataset: {missing_features}")

        if self.target_name not in df.columns:
            raise ValueError(f"Missing target column '{self.target_name}' in dataset")

        # 2. Missing values
        null_counts = df[self.feature_names + [self.target_name]].isnull().sum().to_dict()
        total_nulls = sum(null_counts.values())
        report["missing_values"] = null_counts
        report["total_missing"] = total_nulls

        # 3. Duplicate checks
        duplicates = int(df.duplicated(subset=["transaction_id"] if "transaction_id" in df.columns else None).sum())
        report["duplicate_transactions"] = duplicates

        # 4. Target distribution (Synthetic Label)
        target_counts = df[self.target_name].value_counts().to_dict()
        target_pct = df[self.target_name].value_counts(normalize=True).to_dict()
        report["target_distribution"] = {
            "synthetic_label_notice": "is_fraud is a synthetic benchmark label, not real-world ground truth",
            "counts": {str(k): int(v) for k, v in target_counts.items()},
            "percentages": {str(k): round(float(v) * 100, 2) for k, v in target_pct.items()}
        }

        # 5. Invalid numeric checks
        numeric_anomalies = {}
        for col in self.feature_names:
            inf_count = int(np.isinf(df[col]).sum())
            neg_count = int((df[col] < 0).sum())
            if inf_count > 0 or neg_count > 0:
                numeric_anomalies[col] = {"infinite_count": inf_count, "negative_count": neg_count}

        report["numeric_anomalies"] = numeric_anomalies
        logger.info(f"Validation completed successfully. Target distribution: {report['target_distribution']['percentages']}")
        return report

    def preprocess(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        """
        Cleans data, casts types, and isolates features from metadata.
        Returns:
            X: Cleaned feature matrix (only the 12 approved features)
            y: Target series (synthetic is_fraud)
            metadata: Identifier and timestamp fields for auditing/database tracking
        """
        # Ensure proper numeric datatypes
        X = df[self.feature_names].copy()
        for col in self.feature_names:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0)

        y = df[self.target_name].astype(int)

        metadata_cols = [c for c in ["transaction_id", "customer_id", "timestamp", "channel",
                                     "transaction_type", "receiver_id", "device_id", "location"] if c in df.columns]
        metadata = df[metadata_cols].copy()

        return X, y, metadata

    def prepare_train_test_split(
        self,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame, pd.DataFrame]:
        """
        Performs 80/20 stratified train-test split.
        Returns:
            X_train, X_test, y_train, y_test, meta_train, meta_test
        """
        df = self.load_data()
        validation_report = self.validate_data(df)
        X, y, meta = self.preprocess(df)

        logger.info(f"Splitting {len(df)} records into train ({1-test_size:.0%}) and test ({test_size:.0%}) with stratification...")
        X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
            X, y, meta,
            test_size=test_size,
            stratify=y,
            random_state=random_state
        )

        logger.info(f"Train set: {len(X_train)} samples | Test set: {len(X_test)} samples")
        return X_train, X_test, y_train, y_test, meta_train, meta_test

    def run_and_save(self, output_dir: str = "data/processed") -> Dict[str, Any]:
        """Executes full pipeline and persists processed datasets."""
        os.makedirs(output_dir, exist_ok=True)
        df = self.load_data()
        validation_report = self.validate_data(df)

        X_train, X_test, y_train, y_test, meta_train, meta_test = self.prepare_train_test_split()

        # Combine for persistent CSVs with metadata
        train_df = pd.concat([meta_train.reset_index(drop=True), X_train.reset_index(drop=True), y_train.reset_index(drop=True)], axis=1)
        test_df = pd.concat([meta_test.reset_index(drop=True), X_test.reset_index(drop=True), y_test.reset_index(drop=True)], axis=1)

        train_path = os.path.join(output_dir, "train.csv")
        test_path = os.path.join(output_dir, "test.csv")
        summary_path = os.path.join(output_dir, "data_summary.json")

        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)

        summary = {
            "dataset_info": {
                "total_rows": len(df),
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                "features": self.feature_names,
                "target": self.target_name,
                "label_type": "SYNTHETIC_BENCHMARK"
            },
            "validation": validation_report
        }

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Processed datasets successfully saved to {output_dir}")
        return summary


if __name__ == "__main__":
    pipeline = DataPipeline()
    summary = pipeline.run_and_save()
    print("Pipeline run completed successfully.")
    print("Summary:", json.dumps(summary["dataset_info"], indent=2))
