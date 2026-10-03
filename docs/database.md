# Database Schema & Data Models — upay AI Shield

## 1. Overview
The database layer is managed via **SQLAlchemy 2.0 ORM** and is designed to support **PostgreSQL** in production with an automatic fallback to **SQLite** for standalone development.

All tables incorporate explicit indexing on frequently queried columns and automatic audit timestamps (`created_at`, `updated_at`).

---

## 2. Table Schemas & Indexes

### `customers`
Stores historical baseline profiles for customer behavioral comparison.
- `customer_id` (String(64), Primary Key, Indexed)
- `account_age_days` (Integer)
- `normal_avg_amount` (Float)
- `normal_transaction_count` (Integer)
- `primary_location` (String(128))
- `registered_device_count` (Integer)
- `account_created_date` (String(32))
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

### `transactions`
Contains all monitored digital payment records.
- `transaction_id` (String(64), Primary Key, Indexed)
- `customer_id` (String(64), Foreign Key -> customers.customer_id, Indexed)
- `amount` (Float)
- `timestamp` (String(64), Indexed)
- `hour` (Integer)
- `day_of_week` (Integer)
- `transaction_type` (String(64))
- `channel` (String(64))
- `receiver_id` (String(64), Indexed)
- `is_new_receiver` (Integer)
- `device_id` (String(64), Indexed)
- `is_new_device` (Integer)
- `location` (String(128))
- `location_changed` (Integer)
- `transactions_last_1h` (Integer)
- `transactions_last_24h` (Integer)
- `failed_attempts` (Integer)
- `account_age_days` (Integer)
- `receiver_transaction_count` (Integer)
- `avg_transaction_amount` (Float)
- `amount_deviation` (Float)
- `is_fraud` (Integer, Indexed) — *Synthetic Benchmark Label*
- `demo_risk_score` (Float)
- `risk_level` (String(32), Indexed)
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

### `risk_predictions`
Stores model inferences and SHAP factor attribution snapshots.
- `id` (Integer, Primary Key, Auto Increment)
- `transaction_id` (String(64), Foreign Key -> transactions.transaction_id, Indexed)
- `model_version` (String(64))
- `risk_probability` (Float)
- `risk_score` (Float)
- `risk_level` (String(32))
- `recommended_action` (String(64))
- `shap_factors` (JSON)
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

### `investigations`
Caches Gemini AI investigation briefs and findings.
- `id` (Integer, Primary Key, Auto Increment)
- `transaction_id` (String(64), Foreign Key -> transactions.transaction_id, Indexed)
- `summary` (Text)
- `risk_context` (JSON)
- `key_findings` (JSON)
- `evidence_to_review` (JSON)
- `recommended_action` (String(64))
- `raw_response` (JSON)
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

### `analyst_feedback`
Audit log of human-in-the-loop determinations.
- `id` (Integer, Primary Key, Auto Increment)
- `transaction_id` (String(64), Foreign Key -> transactions.transaction_id, Indexed)
- `decision` (String(32), Indexed) — `SUSPICIOUS`, `LEGITIMATE`, or `NEEDS_REVIEW`
- `comment` (Text)
- `analyst_id` (String(64), Indexed)
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

### `model_versions`
Audit registry of deployed models, training dates, and evaluation metrics.
- `id` (Integer, Primary Key, Auto Increment)
- `model_name` (String(128))
- `version` (String(64), Unique, Indexed)
- `algorithm` (String(64))
- `metrics` (JSON)
- `hyperparameters` (JSON)
- `created_at` (DateTime, Default: UTC Now)
- `updated_at` (DateTime, Default: UTC Now)

---

## 3. Performance Optimization & Indexing Strategy
To guarantee sub-5ms query response times under high transaction volume:
- `ix_transactions_customer_id`: Accelerates customer 30-day baseline lookups.
- `ix_transactions_receiver_id`: Enables fast fan-in network aggregation.
- `ix_transactions_device_id`: Powers rapid device sharing detection across multiple customers.
- `ix_transactions_risk_level`: Facilitates instant risk-filtered pagination.
- `ix_analyst_feedback_decision`: Drives real-time dashboard feedback KPI calculation.
