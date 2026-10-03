"""
upay AI Shield - Database Connection & Session Management
Supports PostgreSQL (production) with automatic fallback to SQLite for local development.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL

# Attempt database connection
try:
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL or other relational DB
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info(f"Connected to database engine: {engine.url.drivername}")
except Exception as e:
    logger.warning(f"Could not connect to configured DATABASE_URL ({db_url}): {e}. Falling back to SQLite.")
    db_url = "sqlite:///./upay_ai_shield.db"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables."""
    import backend.models  # Ensure models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
