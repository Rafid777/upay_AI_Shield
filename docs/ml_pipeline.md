# Machine Learning & SHAP Pipeline — upay AI Shield

## 1. Dataset & Problem Formulation
- **Primary Source:** Synthetic dataset consisting of 20,000 transactions and 5,000 customer baseline profiles.
- **Target Variable:** `is_fraud` (SYNTHETIC BENCHMARK LABEL).
- **Class Balance:**
  - Legitimate (0): 18,425 records (92.125%)
  - Synthetic Flag (1): 1,575 records (7.875%)
  - Imbalance Ratio: ~11.7 to 1

---

## 2. Feature Engineering & Strict Leakage Prevention
To ensure that the model learns actual behavioral patterns rather than memorizing random IDs or benchmark demo fields, strict feature isolation is enforced:

### Strictly Excluded (Non-Predictive / Leakage Risk):
- `transaction_id`: Random identifier token.
- `customer_id`: Entity identifier (causes customer memorization rather than generalized behavioral learning).
- `device_id`: Device hardware token.
- `receiver_id`: Counterparty identifier token.
- `demo_risk_score`: Benchmark score present in synthetic dataset.
- `risk_level`: Label directly derived from demo score.

### 12 Model Features:
1. `amount`: Monetary value of the transaction.
2. `hour`: Hour of transaction initiation (0–23).
3. `day_of_week`: Day of the week (0–6).
4. `is_new_receiver`: Binary indicator (1 if recipient is previously unseen by customer).
5. `is_new_device`: Binary indicator (1 if device hardware fingerprint is unrecognized).
6. `location_changed`: Binary indicator (1 if transaction location deviates from customer's home region).
7. `transactions_last_1h`: Short-term transaction velocity.
8. `transactions_last_24h`: Daily transaction velocity.
9. `failed_attempts`: Count of preceding consecutive authentication failures.
10. `account_age_days`: Customer account maturity.
11. `receiver_transaction_count`: Historical transaction count of the recipient account.
12. `amount_deviation`: Ratio of current transaction amount to the customer's typical transaction baseline.

---

## 3. Training & Hyperparameter Tuning
- **Algorithm:** `XGBClassifier` (Extreme Gradient Boosting)
- **Class Weighting:** `scale_pos_weight = 11.698` (derived from negative/positive training count ratio to penalize false negatives)
- **Split:** 80% Train (16,000 samples) / 20% Test (4,000 samples) with stratification.
- **Hyperparameters:**
  - `n_estimators`: 250
  - `learning_rate`: 0.04
  - `max_depth`: 5
  - `subsample`: 0.85
  - `colsample_bytree`: 0.85
  - `eval_metric`: `"logloss"`
  - `random_state`: 42

---

## 4. Evaluation Metrics (Test Set Evaluation)
Evaluated on the held-out 4,000-sample test set:
- **Precision:** 1.0 (100.0%)
- **Recall:** 1.0 (100.0%)
- **F1-Score:** 1.0 (100.0%)
- **ROC-AUC:** 1.0 (100.0%)
- **False Positive Rate (FPR):** 0.0%
- **False Negative Rate (FNR):** 0.0%
- **Confusion Matrix:**
  - True Negatives (TN): 3,685
  - False Positives (FP): 0
  - False Negatives (FN): 0
  - True Positives (TP): 315

*(Note: Perfect separation on synthetic benchmark data reflects the clean mathematical separation embedded in the synthetic generator; real production deployments will exhibit noise and require ongoing threshold calibration).*

---

## 5. SHAP (SHapley Additive exPlanations)
- **Explainer:** `shap.TreeExplainer` applied directly to the trained XGBoost tree ensemble.
- **Transaction-Level Attribution:** Every prediction computes individual feature SHAP values $\phi_i$.
- **Interpretation Translation:** Each numerical SHAP attribution is translated into domain-specific, plain-English context for human fraud investigators.
  - Positive Shapley values ($\phi_i > 0$) indicate factors elevating transaction risk.
  - Negative Shapley values ($\phi_i < 0$) indicate stabilizing, legitimate historical patterns.

---

## 6. Persisted Artifacts
- Model File: `ml/models/risk_model.pkl`
- Metadata: `ml/models/model_metadata.json`
- Feature Schema: `ml/models/feature_schema.json`
- Visualizations:
  - `outputs/confusion_matrix.png`
  - `outputs/roc_curve.png`
  - `outputs/feature_importance.png`
  - `outputs/class_distribution.png`
  - `outputs/metrics.json`
