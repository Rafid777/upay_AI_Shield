# Data Quality & Integrity Audit Report — upay AI Shield V3
**Audit Date:** 2026-10-03 09:18:03 UTC
**Target Datasets:** `upay_ai_shield_20000_transactions.csv`, `upay_ai_shield_5000_customers.csv`

---

## 1. Executive Summary
- **Transaction Records Audited:** 20,000
- **Customer Profiles Audited:** 5,000
- **Overall Data Health Status:** **PASSED (100% Valid, Zero Missing Values)**
- **Identifier Leakage Check:** **ZERO LEAKAGE DETECTED**
- **Class Balance:** 1,575 positive fraud labels (7.88%), 18,425 negative labels (92.12%)

---

## 2. Completeness & Missing Values Analysis

| Dataset | Column | Data Type | Null Count | Missing % | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Transactions | `transaction_id` | `str` | 0 | 0.00% | PASSED |
| Transactions | `customer_id` | `str` | 0 | 0.00% | PASSED |
| Transactions | `amount` | `float64` | 0 | 0.00% | PASSED |
| Transactions | `timestamp` | `str` | 0 | 0.00% | PASSED |
| Transactions | `hour` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `day_of_week` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `transaction_type` | `str` | 0 | 0.00% | PASSED |
| Transactions | `channel` | `str` | 0 | 0.00% | PASSED |
| Transactions | `receiver_id` | `str` | 0 | 0.00% | PASSED |
| Transactions | `is_new_receiver` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `device_id` | `str` | 0 | 0.00% | PASSED |
| Transactions | `is_new_device` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `location` | `str` | 0 | 0.00% | PASSED |
| Transactions | `location_changed` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `transactions_last_1h` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `transactions_last_24h` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `failed_attempts` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `account_age_days` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `receiver_transaction_count` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `avg_transaction_amount` | `float64` | 0 | 0.00% | PASSED |
| Transactions | `amount_deviation` | `float64` | 0 | 0.00% | PASSED |
| Transactions | `is_fraud` | `int64` | 0 | 0.00% | PASSED |
| Transactions | `demo_risk_score` | `float64` | 0 | 0.00% | PASSED |
| Transactions | `risk_level` | `str` | 0 | 0.00% | PASSED |
| Customers | `customer_id` | `str` | 0 | 0.00% | PASSED |
| Customers | `account_age_days` | `int64` | 0 | 0.00% | PASSED |
| Customers | `normal_avg_amount` | `float64` | 0 | 0.00% | PASSED |
| Customers | `normal_transaction_count` | `int64` | 0 | 0.00% | PASSED |
| Customers | `primary_location` | `str` | 0 | 0.00% | PASSED |
| Customers | `registered_device_count` | `int64` | 0 | 0.00% | PASSED |
| Customers | `account_created_date` | `str` | 0 | 0.00% | PASSED |

---

## 3. Uniqueness & Deduplication Audit

- **Duplicate Transaction IDs:** 0 (Uniqueness: 100.0%)
- **Duplicate Customer IDs:** 0 (Uniqueness: 100.0%)

---

## 4. Range, Value Realism & Monetary Integrity (BDT ৳)

- **Non-Positive Amounts (<= 0):** 0 (Integrity: 100% Positive)
- **Minimum Amount:** ৳50.00
- **Median Amount:** ৳1,633.38
- **Mean Amount:** ৳3,238.88
- **Maximum Amount:** ৳101,621.64
- **Invalid Hour Values (< 0 or > 23):** 0
- **Invalid Day of Week Values (< 0 or > 6):** 0

---

## 5. Statistical Outlier & Anomaly Distribution

- **95th Percentile Amount:** ৳11,346.24
- **99th Percentile Amount:** ৳32,254.07
- **99.9th Percentile Outliers:** ৳67,083.08 (Preserved for high-value fraud simulation)

---

## 6. Identifier Leakage & Target Integrity Audit

Model training features must strictly exclude entity identifiers (`transaction_id`, `customer_id`, `device_id`, `receiver_id`) and post-event labels (`demo_risk_score`, `risk_level`):

| Feature Candidate | Allowed in ML Model? | Reason | Audit Status |
| :--- | :--- | :--- | :--- |
| `transaction_id` | **NO** | Primary entity key | Strictly Excluded (PASSED) |
| `customer_id` | **NO** | High-cardinality identity token | Strictly Excluded (PASSED) |
| `receiver_id` | **NO** | Counterparty identity token | Strictly Excluded (PASSED) |
| `device_id` | **NO** | Hardware fingerprint string | Strictly Excluded (PASSED) |
| `demo_risk_score` | **NO** | Derived target proxy | Strictly Excluded (PASSED) |
| `risk_level` | **NO** | Derived tier proxy | Strictly Excluded (PASSED) |
| `is_fraud` | **NO (Target Only)** | Ground truth label | Partitioned as Target Y (PASSED) |

---

## 7. Compliance & Synthetic Benchmark Notice

> `is_fraud` is a synthetic demonstration label generated for research and prototype validation. It does not represent real-world fraud ground truth, nor does this system access any live customer PII or production banking database.