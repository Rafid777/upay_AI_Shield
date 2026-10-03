"""
upay AI Shield - Backend Configuration
Loads settings from environment variables and provides centralized configuration.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "upay AI Shield"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security / Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./upay_ai_shield.db")
    
    # Model Artifacts
    MODEL_PATH: str = os.getenv("MODEL_PATH", "ml/models/risk_model.pkl")
    METADATA_PATH: str = os.getenv("METADATA_PATH", "ml/models/model_metadata.json")
    FEATURE_SCHEMA_PATH: str = os.getenv("FEATURE_SCHEMA_PATH", "ml/models/feature_schema.json")
    
    # Host & Port
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    model_config = {"case_sensitive": True}


settings = Settings()
