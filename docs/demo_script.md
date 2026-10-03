# Hackathon Presentation Demo Script — upay AI Shield
**Track:** AI-Powered Financial Risk & Scam Intelligence  
**Duration:** 3–5 Minutes  
**Demonstration URL:** `http://127.0.0.1:8000/`

---

## 1. Introduction: The Problem & Solution (0:00 – 0:45)
- **Problem:** *"In Bangladesh's rapidly growing MFS ecosystem (processing millions of daily transactions across Send Money, Cash Out, and Merchant Payments), financial institutions face an acute operational challenge: static threshold rules trigger overwhelming false positives that frustrate genuine users, while traditional black-box ML models are rejected by risk officers due to zero explainability and regulatory non-compliance."*
- **Solution:** *"Introducing **upay AI Shield** — an end-to-end Risk & Scam Intelligence platform combining calibrated XGBoost scoring, exact SHAP local feature attributions, empirical behavioral baselines, network graph topology, and Google Gemini generative investigation under a strict Human-in-the-Loop governance policy."*
- **Core Principle:** *"The AI never autonomously freezes accounts or confiscates funds. It provides transparent, mathematically grounded evidence so human fraud analysts make faster, fairer, and fully auditable decisions."*

---

## 2. Risk Operations Dashboard Tour (0:45 – 1:30)
- **Navigate to:** `Risk Dashboard` (`http://127.0.0.1:8000/`)
- **Key Highlights:**
  - **8 Live KPI Cards:** Total Transactions (20,000 synthetic BDT records), High Risk (1,116), Medium Risk (463), Low Risk (18,421), Open Cases, Human Reviews, Potential Scam Patterns, and Potential ATO Cases.
  - **Currency Realism (৳ / BDT):** Point out Bangladesh Taka (`৳`) formatting throughout all monetary values.
  - **Channel Intelligence Table:** Breakdown across `APP`, `USSD`, `WEB`, and `AGENT` showing transaction counts, aggregate volume (`৳46.9M` on App), average ticket sizes, and high-risk percentages (`~5.6%`).
  - **Top Risk Signals:** Empirical distributions of prior failed logins, new recipients, and amount surges.

---

## 3. End-to-End Investigation Walkthrough (1:30 – 3:30)

### Step 1: 1-Click High-Risk Demo Scenario (`TX103934`)
- Click the top navigation shortcut: **"High (ATO)"** (`TX103934`).
- The **10-Section Investigation Workspace Drawer** smoothly slides open.

### Step 2: Risk Score & SHAP Breakdown
- **Risk Score:** `98.5/100` (`HIGH`).
- **SHAP Breakdown:** Exact positive risk-increasing factor points:
  - `Behavior Anomaly (+26 pts)`
  - `New Device (+21 pts)`
  - `New Receiver (+18 pts)`
  - `Amount Deviation (+15 pts)`
  - `Location Change (+11 pts)`
  - `Prior Failed Logins (+4 pts)`
- Explain: *"Every score contribution is computed via shap.TreeExplainer directly on the XGBoost trees—zero hardcoded numbers."*

### Step 3: Customer Behavior Profile & Deviations
- Show the **Behavior Baseline Comparison**:
  - Baseline: Average `৳1,476.27`, typical hours `08:00 AM – 10:00 PM`, 1 known device, 4 known receivers.
  - Current: `৳31,495.48` (19.0x surge), `00:42 AM` nocturnal submission, unauthenticated device `DEV01037`, new counterparty `REC00630`.

### Step 4: Scam Pattern & Account Takeover (ATO) Indicators
- Point out the active **Scam Pattern Badges**: `UNUSUAL_HIGH_VALUE_TRANSFER`, `NEW_DEVICE_TRANSFER`, `SUSPICIOUS_TIME_ACTIVITY`.
- Point out the **ATO Signals**: `Unregistered Device`, `Nocturnal Off-Hours`, `First-Time Beneficiary`, and `Geographic Shift`.

### Step 5: Risk Story / Chronological Timeline
- Scroll to **"Why is this transaction unusual?"**:
  - `09:12 PM` — Normal diurnal transaction (`৳850.00`).
  - `00:07 AM` — First-time hardware fingerprint `DEV01037` authenticated.
  - `00:09 AM` — Unknown recipient `REC00630` added.
  - `00:11 AM` — Geographic shift detected (Chattogram session).
  - `00:42 AM` — High-value transfer executed (`৳31,495.48`).
  - `00:43 AM` — High velocity burst detected (`13 tx/hr`).

### Step 6: Gemini Generative AI Assistant
- Highlight Gemini's structured investigation brief: Executive Summary, Key Findings, and Analyst Verification Checklist.
- Show safety fallback: Even when external LLM quotas are exhausted, our deterministic fallback renders the exact structured schema from live model evidence with zero hallucination.

### Step 7: Case Management & Analyst Determination
- Click **"Create Formal Case"** — converts transaction into tracked case `CASE-1005` in `OPEN` status.
- Select formal decision: **"Confirm Suspicious"**.
- Enter rationale: *"Customer contacted; confirmed stolen handset and unapproved midnight transfer."*
- Click **"Submit Analyst Decision"** — updates case to `RESOLVED`, logs audit event in `case_events`, and syncs ground-truth to `analyst_feedback`.

---

## 4. Live Risk Simulator & What-If Analysis (3:30 – 4:15)
- Click **"Live Risk Simulator"** in the sidebar:
  - Input custom BDT amount, transaction type, channel, hour, and switches.
  - Click **"Analyze Transaction"** — runs live through the XGBoost model.
- Switch to the **"What-If Risk Simulator"** sub-tab:
  - Demonstrate counterfactual reasoning: toggle `New Device: NO` and `Location Changed: NO`.
  - Click **"Run What-If Analysis"**.
  - Show the live model re-prediction: Original `98.5` vs Simulated `72.1` with a real delta of `-26.4 points`.
  - Emphasize: *"No hardcoded point deductions; the simulated score is generated by a fresh inference through the XGBoost model."*

---

## 5. Model Monitoring, Data Drift & Feedback Loop (4:15 – 5:00)
- Click **"Model Monitoring"** in the sidebar:
  - **Model Health:** Precision (`0.985`), Recall (`0.962`), F1 (`0.973`), ROC-AUC (`0.992`).
  - **Data Drift Telemetry:** Real-time Normalized Absolute Mean Shift (NAMS) across production features with `LOW`, `MEDIUM`, `HIGH` indicators.
  - **Active Learning Feedback:** Real counters of reviewed cases (`11 reviewed`, `11 confirmed suspicious`).
  - Click **"Export Retraining Dataset (.CSV)"** — downloads the clean, verified retraining dataset.
- Conclude: *"upay AI Shield delivers predictive precision, explainable transparency, and actionable intelligence—with the human analyst firmly in control."*
