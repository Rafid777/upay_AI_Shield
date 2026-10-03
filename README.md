<<<<<<< HEAD
# upay AI Shield
### AI-Powered Transaction Risk & Scam Intelligence Platform
**Track:** Trust & Risk Intelligence | **Domain:** Mobile Financial Services (MFS) & Fintech (Bangladesh Context)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.142+-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.4+-eb6100.svg)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-TreeExplainer-green.svg)](https://shap.readthedocs.io/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-8b5cf6.svg)](https://deepmind.google/technologies/gemini/)
[![Tests: 44 Passed](https://img.shields.io/badge/Tests-44%20Passed-brightgreen.svg)](tests/)
[![Currency: BDT ৳](https://img.shields.io/badge/Currency-BDT%20(%E0%A7%B3)-gold.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Project Overview & Problem Statement

Digital financial services process many millions of transactions daily across Send Money, Cash Out, and Merchant Payments. In rapid mobile money environments like Bangladesh, financial institutions face an acute dilemma: static rule engines trigger massive false positives that frustrate genuine users, while traditional "black-box" machine learning models are rejected by risk officers due to zero explainability and regulatory non-compliance.

**upay AI Shield** delivers an enterprise-grade Risk Operations platform uniting:
1. **Calibrated Machine Learning:** An enterprise-calibrated **XGBoost classifier** evaluating 12 normalized behavioral and telemetry features to produce calibrated 0–100 Risk Scores.
2. **Mathematical Explainability (SHAP XAI):** Instantaneous **SHAP TreeExplainer** deconstructing every prediction into exact local factor contributions ($+\Delta$ and $-\Delta$ points).
3. **Customer Behavioral Profiling:** 30-day personal baseline comparison (typical amounts, habitual hours, known devices, velocity) and dynamic deviation multipliers.
4. **Scam Pattern Intelligence:** 9 empirical typology detectors flagging social engineering transfers, rapid velocity bursts, and mule recipient patterns.
5. **Account Takeover (ATO) Intelligence:** Compound threat detection identifying unauthenticated hardware, geographic shifts, nocturnal activity, and prior login failures.
6. **Suspicious Network Intelligence:** Multi-hop topological entity graph mapping relationships across Customers, Receivers, Devices, and Locations.
7. **What-If Risk Simulator:** Counterfactual analysis allowing analysts to adjust signals and observe real model re-predictions and point deltas.
8. **Grounded Gemini AI Assistant:** Google Gemini 2.5 Flash research assistant synthesizing factual evidence into structured briefs, key findings, and verification questions (with deterministic fallback).
9. **Analyst Case Management & Audit Trail:** Full case lifecycle (`OPEN` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `NEEDS_MORE_INFORMATION` $\rightarrow$ `RESOLVED`) and human determinations (`CONFIRM_SUSPICIOUS`, `MARK_LEGITIMATE`, `NEEDS_MORE_INVESTIGATION`).
10. **Model Monitoring & Data Drift Tracking:** Benchmark model health metrics, statistical Normalized Absolute Mean Shift (NAMS) drift detection, and active learning retraining dataset export (.CSV).
11. **Strict Safety Policy:** The system **never** automatically freezes accounts or seizes funds. All consequential actions require human analyst authorization.

---

## 2. Synthetic Dataset Notice

This prototype utilizes synthetic benchmark datasets tailored to Bangladesh MFS characteristics:
- `upay_ai_shield_20000_transactions.csv` (20,000 transactions with realistic BDT distribution)
- `upay_ai_shield_5000_customers.csv` (5,000 customer baselines)
- `upay_ai_shield_20000_risk_predictions.csv` (20,000 baseline risk scores)

> **IMPORTANT DISCLAIMER:**  
> The target variable `is_fraud` is a **synthetic benchmark label** generated for research and demonstration purposes. It does not represent real-world ground truth, nor does this system connect to any real upay production financial infrastructure.

---

## 3. End-to-End System Architecture

```
Transaction
    ↓
XGBoost Risk Model (0 - 100 Risk Score)
    ↓
Customer Behavior Baseline Comparison
    ↓
Scam Pattern Intelligence (9 Empirical Typologies)
    ↓
Account Takeover (ATO) Combinatorial Signals
    ↓
Network Entity Graph Analysis (Customer, Receiver, Device, Location)
    ↓
SHAP Explainability (Local Feature Attribution)
    ↓
Gemini 2.5 Flash Structured Brief (or Safe Deterministic Fallback)
    ↓
Analyst Case Management (OPEN → UNDER_REVIEW → RESOLVED)
    ↓
Human Reviewer Decision & Feedback Loop
    ↓
Model Monitoring, Data Drift Tracking & Retraining Dataset Export (.CSV)
```

---

## 4. Key Capabilities & Features

### 🛡️ Real-Time Transaction Risk Scoring
- Converts calibrated model probability to a standard **0–100 Risk Score**:
  - **LOW (0–49.9):** `CONTINUE` / Standard Monitoring.
  - **MEDIUM (50.0–79.9):** `ADDITIONAL_REVIEW` / Secondary verification.
  - **HIGH (80.0–100.0):** `HUMAN_REVIEW` / Mandatory human analyst investigation.

### 🔍 Mathematical SHAP Explainability
- Computes exact local Shapley values ($\phi_i$) for every single prediction.
- Distinguishes positive risk-increasing factors from negative mitigating factors.
- Never fabricates or hardcodes feature impacts.

### 👤 Customer Behavioral Baselines & Deviations
- Computes 30-day baseline per customer: typical amounts, active hours, known devices, known receivers, and velocity.
- Directly contrasts baseline vs. current transaction in the investigation drawer.

### 🚨 Scam Pattern & ATO Intelligence
- Detects 9 empirical scam typologies: Unusual High-Value, First-Time Recipient, Rapid Velocity, New Device, Off-Hours, Failed Attempts, Location Change, High Velocity, and Multi-Signal Convergence.
- Calibrates threat severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) using cautious, non-prejudicial language (*"Potential scam pattern detected"*).

### 🕸️ Entity Network & Suspicious Cluster Explorer
- Surfaces multi-account relationships: Customer $\rightarrow$ Receiver, Customer $\rightarrow$ Device, Customer $\rightarrow$ Location.
- Automatically flags high fan-in accounts (single receiver taking funds from many unique customers) and shared hardware fingerprints.

### 🧪 Live Simulator & What-If Counterfactual Analysis
- Evaluate custom transaction payloads against the live XGBoost model.
- Modify one or more features (e.g., toggle New Device or Location Change) to re-predict and view real score deltas.

### 📋 Analyst Case Management Workspace
- Full case ledger with priority, assigned analyst, and lifecycle state.
- 10-section investigation workspace drawer providing unified telemetry, SHAP, ATO, scam patterns, network entities, and Gemini narrative briefs.
- Formal human determination submission synced to the audit database.

### 📊 Model Monitoring & Data Drift
- Model Health: Precision (`0.985`), Recall (`0.962`), F1 (`0.973`), ROC-AUC (`0.992`).
- Data Drift: Normalized Absolute Mean Shift (NAMS) tracking against reference training distributions with `LOW`, `MEDIUM`, and `HIGH` indicators.
- Retraining Export: Download analyst-verified feedback as a ready-to-train CSV.

---

## 5. Directory Structure

```
├── .env                              # Environment variables (API keys, DB config)
├── .env.example                      # Template environment file
├── requirements.txt                  # Python dependencies
├── validate_dataset.py               # Automated data validation script
├── README.md                         # Main Documentation
│
├── data/
│   ├── raw/                          # Raw synthetic datasets (20k tx, 5k cust)
│   └── processed/                    # Train/test stratified splits & summary
│
├── ml/
│   ├── train.py                      # XGBoost training & evaluation pipeline
│   └── models/
│       ├── risk_model.pkl            # Serialized XGBoost model
│       ├── model_metadata.json       # Version, metrics & thresholds
│       └── feature_schema.json       # Feature statistical distributions
│
├── outputs/                          # Evaluation plots & metrics
│   ├── confusion_matrix.png
│   ├── roc_curve.png
│   ├── feature_importance.png
│   ├── class_distribution.png
│   └── metrics.json
│
├── backend/
│   ├── config.py                     # Central configuration loader
│   ├── database.py                   # SQLAlchemy engine (PostgreSQL/SQLite)
│   ├── models.py                     # Database ORM models with audit timestamps & indexes
│   ├── main.py                       # FastAPI application & static mounting
│   ├── routes/                       # Modular API routers
│   │   ├── prediction.py             # POST /api/v1/predict
│   │   ├── transactions.py           # GET  /api/v1/transactions
│   │   ├── investigation.py          # POST /api/v1/investigate
│   │   ├── chat.py                   # POST /api/v1/chat
│   │   ├── dashboard.py              # GET  /api/v1/dashboard/stats
│   │   ├── feedback.py               # POST /api/v1/feedback, /export & GET /stats
│   │   ├── network.py                # GET  /api/v1/network/patterns & /graph/{id}
│   │   ├── cases.py                  # Case management endpoints (CRUD + decisions)
│   │   ├── customers.py              # Customer behavior profile & network endpoints
│   │   ├── scam.py                   # Scam pattern intelligence endpoint
│   │   ├── timeline.py               # Risk story chronological timeline endpoint
│   │   ├── simulation.py             # Live simulator & What-If analysis endpoints
│   │   └── monitoring.py             # Model health & data drift endpoints
│   ├── services/                     # Business logic
│   │   ├── model_service.py          # Inference & scoring
│   │   ├── shap_service.py           # TreeExplainer & feature ranking
│   │   ├── behavioral_service.py     # Baselines & deviation computation
│   │   ├── ato_service.py            # Account takeover pattern detector
│   │   ├── scam_service.py           # 9 empirical scam typologies detector
│   │   ├── timeline_service.py       # Risk story chronological event generator
│   │   ├── case_service.py           # Enterprise case management & event auditing
│   │   ├── network_service.py        # Entity relationship graph generator
│   │   ├── gemini_service.py         # Google GenAI integration & safe fallback
│   │   └── investigation_service.py  # Master orchestrator
│   └── schemas/                      # Pydantic v2 schemas
│
├── frontend/                         # Analyst Dashboard Web Application
│   ├── index.html                    # 10-view Single Page Application shell
│   ├── css/style.css                 # Dark financial-risk operations styling
│   └── js/app.js                     # Interactive client logic & live demo mode
│
├── tests/                            # Automated test suite (44 tests, 100% pass)
│   ├── test_pipeline.py
│   ├── test_model.py
│   ├── test_behavioral.py
│   ├── test_ato.py
│   ├── test_api.py
│   ├── test_gemini.py
│   ├── test_case_management.py
│   ├── test_customer_behavior.py
│   ├── test_scam_intelligence.py
│   ├── test_simulation_what_if.py
│   └── test_monitoring_drift.py
│
└── docs/                             # Technical deep-dive documentation
    ├── architecture.md               # End-to-end architecture & components
    ├── api.md                        # Complete REST API specification
    ├── ml_pipeline.md                # XGBoost training & SHAP attribution details
    ├── database.md                   # Relational schema, indexes & audit fields
    ├── scam_intelligence.md          # 9 empirical scam typologies & signal engine
    ├── network_intelligence.md       # Entity graph schema & topological indicators
    ├── behavior_profile.md           # 30-day baseline profiling & deviation math
    ├── case_management.md            # Enterprise case lifecycle & audit events
    ├── model_monitoring.md           # Model health, NAMS drift & retraining export
    ├── responsible_ai.md             # Privacy, explainability, safety & bias
    ├── demo_script.md                # 3–5 minute Hackathon Presentation Demo Script
    └── pitch.md                      # Hackathon pitch document (Problem, Solution, Impact)
```

---

## 6. Installation & Quickstart

### Prerequisites
- Python 3.11+
- Git

### 1. Set Up Environment
```bash
# Clone repository
git clone <repo-url>
cd "ai train"

# Create and activate virtual environment (optional)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./upay_ai_shield.db
```

### 3. Run Automated Validation & Pipeline
```bash
# Validate synthetic datasets
python validate_dataset.py

# Train calibrated XGBoost model
python ml/train.py

# Seed database with 20,000 transactions and 5,000 customer baselines
python src/seed_db.py
```

### 4. Run Complete Test Suite
```bash
python -m pytest -v
```
*(All 44 unit & integration tests pass with 100% success rate across ML, SHAP, API, ATO, Behavioral, Scam, Simulation, What-If, Case Management, and Data Drift).*

### 5. Launch the Platform
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:8000/`**  
👉 Interactive Swagger Docs: **`http://127.0.0.1:8000/docs`**

---

## 7. 1-Click Demo Mode

The platform features a built-in **1-Click Demo Bar** directly in the top navigation:
- **🟢 Demo: Low Risk (Normal)** (`TX100001`): Routine diurnal transaction, score ~0.0/100, zero ATO indicators, standard monitoring.
- **🟡 Demo: Medium Risk** (`TX101058`): Mild amount surge, score ~65.0/100, secondary verification suggested.
- **🔴 Demo: High Risk (ATO)** (`TX103934`): Critical account takeover simulation with 19x amount deviation, unrecognized hardware fingerprint, nocturnal hour, score 98.5/100, triggering mandatory human analyst investigation.

---

## 8. Responsible AI & Governance Policy

- **No Autonomous Freezing:** The AI model is strictly an anomaly detection and decision-support tool. It **never** autonomously freezes accounts or seizes funds.
- **Explainability by Design:** No risk score is presented without its underlying SHAP feature breakdown.
- **Fail-Safe Operation:** If external AI services encounter downtime or quota exhaustion, the system transitions to a deterministic fallback preserving core operations without hallucination.
- **Human Oversight:** The platform enforces human accountability for all consequential actions.
- **Safe Terminology:** Network clusters are framed cautiously (*"Potential suspicious network"*), never declaring individuals as confirmed criminals without due process.
=======
# upay_AI_Shield
>>>>>>> 06553046714e32f387e4a50c98b1f92b05158086
