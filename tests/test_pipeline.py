"""
Unit tests for data loading, validation, preprocessing, and leakage prevention.
"""

import pytest
import pandas as pd
from src.data_pipeline import DataPipeline, MODEL_FEATURES, TARGET_COLUMN, EXCLUDED_COLUMNS


def test_data_loading():
    pipeline = DataPipeline()
    df = pipeline.load_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 20000
    assert TARGET_COLUMN in df.columns


def test_data_validation():
    pipeline = DataPipeline()
    df = pipeline.load_data()
    report = pipeline.validate_data(df)
    assert report["total_missing"] == 0
    assert "target_distribution" in report
    assert "counts" in report["target_distribution"]


def test_leakage_prevention():
    pipeline = DataPipeline()
    df = pipeline.load_data()
    X, y, meta = pipeline.preprocess(df)

    # Ensure none of the excluded columns are in feature matrix X
    for col in EXCLUDED_COLUMNS:
        assert col not in X.columns, f"Leakage detected: {col} found in features!"

    # Ensure exactly 12 approved features exist
    assert list(X.columns) == MODEL_FEATURES
    assert len(X) == len(y)


def test_train_test_split():
    pipeline = DataPipeline()
    X_train, X_test, y_train, y_test, _, _ = pipeline.prepare_train_test_split(test_size=0.2, random_state=42)
    assert len(X_train) == 16000
    assert len(X_test) == 4000
    # Stratified target ratio should be consistent
    assert abs(y_train.mean() - y_test.mean()) < 0.01
