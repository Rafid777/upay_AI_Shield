# API Reference — upay AI Shield
**Interactive REST API Specification**

Base URL: `http://127.0.0.1:8000/api/v1`  
Interactive Swagger UI: `http://127.0.0.1:8000/docs`  
ReDoc UI: `http://127.0.0.1:8000/redoc`

---

## 1. System Health & Governance
### `GET /api/v1/health`
Returns system operational state, active model version, and governance parameters.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "upay AI Shield",
  "version": "1.0.0",
  "environment": "development",
  "model": {
    "name": "upay AI Shield XGBoost Risk Classifier",
    "version": "upay-ai-shield-v1.0.0",
    "algorithm": "XGBClassifier"
  },
  "governance": {
    "autonomous_blocking_allowed": false,
    "human_in_the_loop_required": true
  }
}
```

---

## 2. Dashboard Analytics & Impact Simulation
### `GET /api/v1/dashboard/stats`
Retrieves aggregated telemetry, 7 KPI cards, risk distribution breakdown, model evaluation metrics, simulated business impact, top empirical risk signals, and recent high-risk alerts.

**Response (200 OK):**
```json
{
  "total_transactions": 20000,
  "low_risk": { "count": 18421, "percentage": 92.11 },
  "medium_risk": { "count": 463, "percentage": 2.31 },
  "high_risk": { "count": 1116, "percentage": 5.58 },
  "human_reviews_total": 4,
  "confirmed_suspicious": 3,
  "marked_legitimate": 1,
  "needs_investigation": 0,
  "model_metrics": {
    "accuracy": 1.0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0,
    "roc_auc": 1.0,
    "false_positive_rate": 0.0,
    "false_negative_rate": 0.0
  },
  "business_impact": {
    "total_volume_protected_bdt": 27900000.0,
    "manual_review_reduction_pct": 92.11,
    "high_risk_flagged_count": 1116,
    "est_loss_prevented_bdt": 24650000.0
  },
  "top_risk_signals": [
    { "signal": "High Amount Deviation", "count": 1116, "pct": 100.0 },
    { "signal": "Unrecognized Device Hardware", "count": 1089, "pct": 97.58 },
    { "signal": "Recipient Unseen by Customer", "count": 1042, "pct": 93.37 }
  ],
  "recent_high_risk": [ ... ],
  "hourly_distribution": { "00:00": 222, ... }
}
```

---

## 3. Transactions Ledger
### `GET /api/v1/transactions`
Retrieves paginated transactions with optional risk level, search query, and minimum amount filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number (1-indexed)
- `limit` (int, default: 25, max: 100): Items per page
- `risk_level` (string, optional): Filter by `LOW`, `MEDIUM`, or `HIGH`
- `search` (string, optional): Matches transaction ID, customer ID, or receiver ID
- `min_amount` (float, optional): Filter transactions with amount $\ge$ min_amount

### `GET /api/v1/transactions/{transaction_id}`
Retrieves complete record details for a specific transaction ID.

---

## 4. Risk Prediction & SHAP Explainability
### `POST /api/v1/predict`
Calculates risk probability, standard 0–100 risk score, governance action, and top SHAP feature contributions.

**Request Payload (by Transaction ID):**
```json
{
  "transaction_id": "TX103934"
}
```

**Request Payload (Custom Telemetry Simulation):**
```json
{
  "features": {
    "amount": 14500.0,
    "hour": 3,
    "day_of_week": 6,
    "is_new_receiver": 1,
    "is_new_device": 1,
    "location_changed": 1,
    "transactions_last_1h": 8,
    "transactions_last_24h": 25,
    "failed_attempts": 3,
    "account_age_days": 35,
    "receiver_transaction_count": 0,
    "amount_deviation": 8.5
  }
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "TX103934",
  "risk_probability": 0.9999,
  "risk_score": 99.99,
  "risk_level": "HIGH",
  "recommended_action": "HUMAN_REVIEW",
  "model_version": "upay-ai-shield-v1.0.0",
  "shap_factors": [
    {
      "feature": "transactions_last_1h",
      "shap_value": 7.7891,
      "feature_value": 11.0,
      "impact": "RISK_INCREASING",
      "importance_rank": 1,
      "explanation": "High short-term velocity (11 transactions in the past hour), indicating burst activity."
    }
  ]
}
```

---

## 5. Comprehensive AI Investigation
### `POST /api/v1/investigate`
Synthesizes factual telemetry, model risk score, SHAP attributions, customer 30-day baseline comparison, account takeover indicators, and network graph context into an investigative brief.

**Request Payload:**
```json
{
  "transaction_id": "TX103934"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "TX103934",
  "summary": "Transaction TX103934 flagged with XGBoost risk score of 99.9/100 (HIGH). Multiple compound account takeover signals detected.",
  "risk_context": {
    "risk_score": 99.9,
    "risk_level": "HIGH",
    "recommended_action": "HUMAN_REVIEW"
  },
  "shap_factors": [ ... ],
  "behavioral_comparison": {
    "customer_id": "CUST1008",
    "baseline": {
      "avg_amount": 1192.5,
      "transactions_per_hour": 0.4,
      "registered_devices": 2,
      "primary_location": "Dhaka North"
    },
    "current_transaction": {
      "amount": 23000.0,
      "hour": 3,
      "is_new_device": 1,
      "location_changed": 1,
      "transactions_last_1h": 11
    },
    "deviations": {
      "amount_ratio": 19.29,
      "velocity_ratio": 27.5,
      "is_unrecognized_device": true,
      "is_location_discrepancy": true,
      "is_off_hours": true
    }
  },
  "ato_signals": {
    "detected_signals": [ ... ],
    "signal_count": 5,
    "severity": "CRITICAL",
    "recommendation": "Potential account takeover indicators detected. Hold processing and initiate out-of-band contact."
  },
  "investigation_questions": [
    "Verify customer authorization for transaction amount of ৳23,000.00.",
    "Confirm if session originated from an authorized customer device hardware ID."
  ],
  "human_review_required": true,
  "is_ai_generated": true
}
```

---

## 6. Conversational AI Assistant
### `POST /api/v1/chat`
Answers contextual investigation inquiries from fraud analysts grounded strictly in observed telemetry and SHAP evidence.

**Request Payload:**
```json
{
  "transaction_id": "TX103934",
  "message": "Could this indicate account takeover?"
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "TX103934",
  "reply": "Yes, potential account takeover indicators are present: the transaction originated from an unrecognized hardware device at 03:14 AM (off-hours), combined with a 19.3x amount deviation and 11 transactions in the past hour. Human analyst verification is advised.",
  "is_ai_generated": true
}
```

---

## 7. Network & Entity Graph Intelligence
### `GET /api/v1/network/patterns`
Retrieves detected entity network clusters across the dataset, highlighting high fan-in accounts and shared hardware fingerprints.

**Response (200 OK):**
```json
{
  "high_fanin_receivers": [
    {
      "receiver_id": "RCV5012",
      "unique_senders": 42,
      "total_volume": 485000.0,
      "avg_risk_score": 84.2,
      "assessment": "Suspicious network pattern: high customer fan-in"
    }
  ],
  "shared_devices": [
    {
      "device_id": "DEV9901",
      "unique_customers": 8,
      "transaction_count": 31,
      "assessment": "Potential coordinated activity: device sharing across multiple customers"
    }
  ]
}
```

### `GET /api/v1/network/graph/{transaction_id}`
Returns the localized sub-graph node/edge relationships (Customer $\rightarrow$ Transaction $\rightarrow$ Receiver / Device / Location) for visual graph rendering.

---

## 8. Human Analyst Feedback Loop
### `POST /api/v1/feedback`
Records analyst decisions into the database for compliance, auditability, and model retraining.

**Request Payload:**
```json
{
  "transaction_id": "TX103934",
  "decision": "SUSPICIOUS",
  "comment": "Unrecognized hardware with high amount deviation verified via customer outreach.",
  "analyst_id": "analyst_lead_01"
}
```
**Allowed Decisions:** `SUSPICIOUS` | `LEGITIMATE` | `NEEDS_REVIEW`

### `GET /api/v1/feedback/stats`
Returns aggregated analyst review metrics across all recorded feedback.

### `POST /api/v1/feedback/export`
Exports human-verified transaction feedback records as a downloadable retraining CSV dataset.

---

## 9. Customer Behavior & Network Intelligence
### `GET /api/v1/customers/{customer_id}/behavior`
Returns 30-day personal baseline (average amount, typical hours, known devices, known receivers, velocity) and calculated behavioral deviations for a given customer.

### `GET /api/v1/customers/{customer_id}/network`
Returns multi-hop graph topology (nodes and edges), connected customer counts, shared receivers/devices/locations, aggregate BDT transfer volume, and network risk indicators.

---

## 10. Scam & Risk Story Intelligence
### `GET /api/v1/transactions/{transaction_id}/scam-intelligence`
Evaluates transaction against 9 empirical scam typologies and returns structured detection signals, highest severity, status, and analyst investigation guidance.

### `GET /api/v1/transactions/{transaction_id}/risk-story`
Generates chronological transaction timeline narrative reconstructing the anomalous session event-by-event with icons, timestamps, amounts, and executive summary.

---

## 11. Live & What-If Simulation
### `POST /api/v1/simulate`
Runs custom transaction features through live XGBoost model, returning continuous risk score (0–100), risk tier, recommended action, top SHAP factors, and behavioral deviations.

### `POST /api/v1/what-if`
Performs counterfactual risk simulation by comparing original transaction features with modified features. Runs modified features through live model inference and returns original score, simulated score, score delta points, and changed factor attributions.

---

## 12. Analyst Case Management
### `POST /api/v1/cases`
Creates a formal investigation case with priority, assigned analyst, initial evidence snapshot, and status `OPEN`.

### `GET /api/v1/cases`
Lists paginated cases with optional `status` (`OPEN`, `UNDER_REVIEW`, `NEEDS_MORE_INFORMATION`, `RESOLVED`) and `priority` filters.

### `GET /api/v1/cases/{case_id}`
Retrieves detailed case record including full chronological audit event log from `case_events`.

### `PATCH /api/v1/cases/{case_id}`
Updates case status, priority, assigned analyst, or analyst notes, automatically logging audit event.

### `POST /api/v1/cases/{case_id}/decision`
Records formal human analyst determination (`CONFIRM_SUSPICIOUS`, `MARK_LEGITIMATE`, `NEEDS_MORE_INVESTIGATION`), transitions case to `RESOLVED`, and syncs ground-truth to `analyst_feedback`.

---

## 13. Model Monitoring & Data Drift
### `GET /api/v1/model/health`
Returns live model operational health: algorithm, version, sample counts, precision, recall, F1, ROC-AUC, FPR, FNR, global feature weights, and hyperparameters.

### `GET /api/v1/model/drift`
Computes Normalized Absolute Mean Shift (NAMS) drift across evaluated features against reference training distribution, returning `LOW`, `MEDIUM`, or `HIGH` drift indicators.

