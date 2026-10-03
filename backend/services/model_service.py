"""
upay AI Shield - Model Service
Manages XGBoost model inference, risk scoring, categorization, and governance rules.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from backend.config import settings
from src.data_pipeline import MODEL_FEATURES

logger = logging.getLogger(__name__)


class ModelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        self.model_path = settings.MODEL_PATH
        self.metadata_path = settings.METADATA_PATH
        self.feature_names = MODEL_FEATURES

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}. Train the model first.")

        logger.info(f"Loading risk model from {self.model_path}...")
        self.model = joblib.load(self.model_path)

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "model_version": "upay-ai-shield-v1.0.0",
                "framework": "xgboost"
            }
        logger.info(f"Model service initialized: {self.metadata.get('model_name', 'XGBoost Risk Model')}")

    def get_model(self):
        return self.model

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

    def predict(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs XGBoost inference on input feature dictionary.
        Returns:
            {
               "risk_probability": float (0.0 to 1.0),
               "risk_score": float (0.0 to 100.0),
               "risk_level": "LOW" | "MEDIUM" | "HIGH",
               "recommended_action": "CONTINUE" | "ADDITIONAL_REVIEW" | "HUMAN_REVIEW",
               "model_version": str
            }
        """
        # Ensure ordered dataframe matching training features
        row = {}
        for feature in self.feature_names:
            val = feature_data.get(feature, 0.0)
            row[feature] = [float(val) if val is not None else 0.0]

        df_features = pd.DataFrame(row)

        # Predict probability of high risk
        proba = float(self.model.predict_proba(df_features)[0, 1])
        risk_score = round(proba * 100.0, 2)

        # Determine risk level and governance action
        if risk_score >= 80.0:
            risk_level = "HIGH"
            action = "HUMAN_REVIEW"
        elif risk_score >= 50.0:
            risk_level = "MEDIUM"
            action = "ADDITIONAL_REVIEW"
        else:
            risk_level = "LOW"
            action = "CONTINUE"

        return {
            "risk_probability": round(proba, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommended_action": action,
            "model_version": self.metadata.get("model_version", "v1.0.0"),
            "features_df": df_features
        }

    def predict_risk(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience alias for predict."""
        return self.predict(feature_data)


model_service = ModelService()
