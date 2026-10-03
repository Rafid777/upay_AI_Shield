"""
upay AI Shield - Database Seeder
Seeds SQLite/PostgreSQL database with the 5,000 customers, 20,000 transactions,
and model version registry.
"""

import os
import sys
import json
import logging
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.database import SessionLocal, init_db, engine
from backend.models import Customer, Transaction, ModelVersion, RiskPrediction

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def seed_database():
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        tx_count = db.query(Transaction).count()
        if tx_count >= 20000:
            logger.info(f"Database already contains {tx_count} transactions. Skipping seeding.")
            return

        logger.info("Starting database seeding...")

        # 1. Seed Model Version
        metadata_path = "ml/models/model_metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                meta = json.load(f)
            
            existing_ver = db.query(ModelVersion).filter(ModelVersion.version == meta.get("model_version")).first()
            if not existing_ver:
                mv = ModelVersion(
                    model_name=meta.get("model_name", "upay AI Shield Risk Model"),
                    version=meta.get("model_version", "v1.0.0"),
                    algorithm=meta.get("algorithm", "XGBoost"),
                    metrics=meta.get("evaluation_metrics", {}),
                    hyperparameters=meta.get("hyperparameters", {})
                )
                db.add(mv)
                db.commit()
                logger.info(f"Registered model version {meta.get('model_version')}")

        # 2. Seed Customers (5,000)
        cust_csv = "data/raw/upay_ai_shield_5000_customers.csv"
        if not os.path.exists(cust_csv):
            cust_csv = "upay_ai_shield_5000_customers.csv"

        if os.path.exists(cust_csv):
            logger.info(f"Reading customers from {cust_csv}...")
            cust_df = pd.read_csv(cust_csv)
            cust_records = []
            for _, row in cust_df.iterrows():
                cust_records.append(Customer(
                    customer_id=str(row["customer_id"]),
                    account_age_days=int(row["account_age_days"]),
                    normal_avg_amount=float(row["normal_avg_amount"]),
                    normal_transaction_count=int(row["normal_transaction_count"]),
                    primary_location=str(row.get("primary_location", "")),
                    registered_device_count=int(row.get("registered_device_count", 1)),
                    account_created_date=str(row.get("account_created_date", ""))
                ))
            
            # Bulk insert in chunks
            chunk_size = 1000
            for i in range(0, len(cust_records), chunk_size):
                db.bulk_save_objects(cust_records[i:i + chunk_size])
                db.commit()
            logger.info(f"Successfully seeded {len(cust_records)} customers.")

        # 3. Seed Transactions (20,000)
        tx_csv = "data/raw/upay_ai_shield_20000_transactions.csv"
        if not os.path.exists(tx_csv):
            tx_csv = "upay_ai_shield_20000_transactions.csv"

        if os.path.exists(tx_csv):
            logger.info(f"Reading transactions from {tx_csv}...")
            tx_df = pd.read_csv(tx_csv)
            tx_records = []
            for _, row in tx_df.iterrows():
                tx_records.append(Transaction(
                    transaction_id=str(row["transaction_id"]),
                    customer_id=str(row.get("customer_id", "")),
                    amount=float(row["amount"]),
                    timestamp=str(row.get("timestamp", "")),
                    hour=int(row["hour"]),
                    day_of_week=int(row["day_of_week"]),
                    transaction_type=str(row.get("transaction_type", "PAYMENT")),
                    channel=str(row.get("channel", "MOBILE_APP")),
                    receiver_id=str(row.get("receiver_id", "")),
                    is_new_receiver=int(row.get("is_new_receiver", 0)),
                    device_id=str(row.get("device_id", "")),
                    is_new_device=int(row.get("is_new_device", 0)),
                    location=str(row.get("location", "")),
                    location_changed=int(row.get("location_changed", 0)),
                    transactions_last_1h=int(row.get("transactions_last_1h", 0)),
                    transactions_last_24h=int(row.get("transactions_last_24h", 0)),
                    failed_attempts=int(row.get("failed_attempts", 0)),
                    account_age_days=int(row.get("account_age_days", 0)),
                    receiver_transaction_count=int(row.get("receiver_transaction_count", 0)),
                    avg_transaction_amount=float(row.get("avg_transaction_amount", 0.0)),
                    amount_deviation=float(row.get("amount_deviation", 0.0)),
                    is_fraud=int(row.get("is_fraud", 0)),
                    demo_risk_score=float(row.get("demo_risk_score", 0.0)),
                    risk_level=str(row.get("risk_level", "LOW"))
                ))

            for i in range(0, len(tx_records), 2000):
                db.bulk_save_objects(tx_records[i:i + 2000])
                db.commit()
                logger.info(f"Inserted {min(i + 2000, len(tx_records))}/{len(tx_records)} transactions...")

            logger.info("All 20,000 transactions successfully seeded.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
