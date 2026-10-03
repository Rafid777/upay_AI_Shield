# Model Monitoring & Data Drift — upay AI Shield
**Model Performance Telemetry, Statistical Drift Tracking & Retraining Dataset Export**

---

## 1. Overview & Operational Need

Machine learning models deployed in financial environments face dynamic adversary adaptation, seasonality, and shifting customer habits.

**upay AI Shield** integrates continuous operational monitoring across three pillars:
1. **Model Health & Performance Benchmarks**: Evaluating historical training/test precision, recall, F1, and ROC-AUC.
2. **Data Drift Telemetry**: Detecting statistical distribution shift in production transactions relative to the baseline training population.
3. **Active Learning Feedback & Retraining Pipeline**: Accumulating human-verified cases for structured retraining dataset export.

---

## 2. Model Health & Evaluation Benchmarks

The core predictive engine is an optimized **XGBoost Classifier** (`ml/models/risk_model.pkl`) trained on 20,000 synthetic Bangladesh MFS transactions:

### Baseline Metrics (4,000 Holdout Test Samples)
- **Model Name**: `upay AI Shield XGBoost Risk Classifier`
- **Model Version**: `v1.2.0-bdt-mfs`
- **Algorithm**: `XGBClassifier (Extreme Gradient Boosting)`
- **ROC-AUC**: `0.992`
- **Precision**: `0.985`
- **Recall**: `0.962`
- **F1 Score**: `0.973`
- **False Positive Rate (FPR)**: `0.008` (Low customer friction)
- **False Negative Rate (FNR)**: `0.038` (High fraud interception)

### Top Global Feature Importances
1. `amount_deviation`: Historical amount surge multiplier (Weight: 0.342)
2. `transactions_last_1h`: Short-term hourly transaction burst (Weight: 0.187)
3. `is_new_device`: Unrecognized hardware/browser fingerprint (Weight: 0.145)
4. `failed_attempts`: Pre-transaction login failure count (Weight: 0.118)
5. `is_new_receiver`: First-time beneficiary flag (Weight: 0.089)
6. `hour`: Nocturnal activity window (Weight: 0.063)

---

## 3. Data Drift Monitoring Methodology

### Statistical Framework: Normalized Absolute Mean Shift (NAMS)
To detect covariate shift without incurring prohibitive computational latency, the monitoring engine compares the recent transaction window (default: trailing 500 transactions) against the reference training population across eight critical features:

$$\text{NAMS}_j = \frac{|\mu_{\text{recent}, j} - \mu_{\text{reference}, j}|}{\sigma_{\text{reference}, j} + \epsilon}$$

### Drift Classification Thresholds
- **`LOW` Drift** ($\text{NAMS} < 0.15$): Feature distribution is stable and closely aligns with training data.
- **`MEDIUM` Drift** ($0.15 \le \text{NAMS} < 0.35$): Noticeable shift detected; analyst monitoring advised.
- **`HIGH` Drift** ($\text{NAMS} \ge 0.35$): Significant distribution divergence; model retraining or recalibration recommended.

### Sample Size Guardrail
> If fewer than 30 production transactions are available in the evaluation window, the engine returns:
> `"Insufficient data for reliable drift estimation"`
> This prevents false drift alarms caused by micro-sample noise.

---

## 4. Retraining Dataset Export

In strict adherence to financial risk best practices, **the platform never autonomously retrains a live production model from a single analyst click**.

Instead, verified analyst determinations are curated into a standard retraining format via:
`POST /api/v1/feedback/export`

### CSV Export Schema
The exported CSV file contains:
- `transaction_id`: Transaction identifier
- `customer_id`: Customer identifier
- `amount_bdt`: Transaction amount in BDT
- `channel`: Channel used (`APP`, `USSD`, `WEB`)
- `transaction_type`: Type (`SEND_MONEY`, `CASH_OUT`, etc.)
- `hour`, `day_of_week`: Temporal attributes
- `is_new_receiver`, `is_new_device`, `location_changed`: Telemetry flags
- `transactions_last_1h`, `transactions_last_24h`, `failed_attempts`: Velocity metrics
- `account_age_days`, `receiver_transaction_count`, `amount_deviation`: Behavioral features
- `predicted_risk_score`, `predicted_risk_level`: Original model output
- `analyst_decision`: Human ground truth (`CONFIRM_SUSPICIOUS`, `MARK_LEGITIMATE`)
- `analyst_reason`: Ground-truth explanation notes
- `analyst_id`: Reviewer handle
- `review_timestamp`: Verification timestamp

---

## 5. API Reference

- `GET /api/v1/model/health`: Retrieves benchmark metrics, hyperparameters, and feature weights.
- `GET /api/v1/model/drift`: Calculates statistical NAMS drift across recent transactions.
- `GET /api/v1/feedback/stats`: Summarizes total human reviews, suspicious rates, and review breakdown.
- `POST /api/v1/feedback/export`: Streams complete human-verified dataset as a downloadable CSV.
