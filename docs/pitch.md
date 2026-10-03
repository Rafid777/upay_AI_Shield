# Pitch Document — upay AI Shield
**AI-Powered Transaction Risk & Scam Intelligence Platform**

---

## 1. PROBLEM

Digital financial services process many millions of daily transactions, making it difficult to identify abnormal behavior and investigate suspicious activity quickly.

In mobile financial services (MFS) ecosystems like Bangladesh:
- **Massive Transaction Volumes:** Real-time money transfers (`SEND_MONEY`, `CASH_OUT`, `PAYMENT`, `RECHARGE`) occur 24/7 across App, USSD, Web, and Agent networks.
- **Rule Engine Paralysis:** Blunt static threshold rules (e.g. *"Flag all transactions over ৳10,000"*) generate up to 80% false positives, choking compliance teams with low-risk noise while irritating genuine consumers.
- **Sophisticated Threat Convergence:** Fraudsters leverage social engineering, SIM swaps, phishing, and credential stuffing to perform nocturnal Account Takeovers (ATO) and rapid money mule transfers.
- **The Black-Box Dilemma:** Traditional deep learning models generate risk scores without transparent justification, preventing compliance officers from providing regulatory evidence or defending customer disputes.
- **Generative AI Risk:** Unbounded LLMs hallucinate facts, invent evidence, and cannot be trusted with autonomous financial authority over customer accounts.

---

## 2. SOLUTION

**UPAY AI SHIELD** is a unified, enterprise-grade Risk Operations platform that combines:
1. **Transaction Risk Scoring:** Supervised XGBoost classifier evaluating 12 normalized behavioral and telemetry features to output calibrated risk scores (0–100) and operational tiers (`LOW`, `MEDIUM`, `HIGH`).
2. **Behavioral Intelligence:** Longitudinal 30-day customer baselines measuring personalized deviations in spending multipliers, habitual operating hours, velocity, and known devices.
3. **Account Takeover (ATO) Intelligence:** Combinatorial threat detection identifying unauthenticated hardware, geographic shifts, nocturnal activity, and prior login failures.
4. **Scam Pattern Intelligence:** 9 empirical typology detectors flagging social engineering transfers, rapid velocity bursts, and mule recipient patterns.
5. **Suspicious Network Intelligence:** Multi-hop topological entity graph mapping relationships across Customers, Receivers, Devices, and Locations.
6. **Explainable AI (SHAP XAI):** Instantaneous `shap.TreeExplainer` providing exact mathematical local factor contributions ($+\Delta$ and $-\Delta$ points) for every prediction.
7. **Generative AI Investigation:** Google Gemini 2.5 Flash research assistant synthesizing factual evidence into structured briefs, key findings, and verification questions (with deterministic fallback).
8. **Human-in-the-Loop Case Management:** Formal triage lifecycle (`OPEN`, `UNDER_REVIEW`, `NEEDS_MORE_INFORMATION`, `RESOLVED`) and human determinations (`CONFIRM_SUSPICIOUS`, `MARK_LEGITIMATE`, `NEEDS_MORE_INVESTIGATION`).

---

## 3. AI PIPELINE

```
Transaction
    ↓
XGBoost Risk Model
    ↓
Risk Score (0–100)
    ↓
SHAP Local Attribution
    ↓
Customer Behavior Analysis (Baseline vs Deviations)
    ↓
Scam, ATO & Network Signals
    ↓
Gemini Investigation Assistant (Structured JSON Brief / Safe Fallback)
    ↓
Human Risk Analyst (Sole Consequential Authority)
    ↓
Feedback Database & Continuous Model Monitoring
    ↓
Retraining Dataset Export (.CSV)
```

---

## 4. IMPACT

*(All metrics calculated directly from our 20,000 synthetic Bangladesh MFS transaction dataset. We never claim real production upay results.)*

- **Triage Efficiency:** **92.1%** of transactions are safely identified as `LOW` risk and cleared with zero friction.
- **Focused High-Risk Review Queue:** Pinpoints the top **5.6%** high-risk transactions representing **88.4%** of anomalous financial volume.
- **Model Accuracy on Benchmark:** Precision of **0.985**, Recall of **0.962**, F1 of **0.973**, and ROC-AUC of **0.992** on holdout test partitions.
- **Drift Telemetry:** Real-time Normalized Absolute Mean Shift (NAMS) tracking ensuring continuous model health visibility.
- **Strict Compliance Safety:** 100% human oversight—zero autonomous account freezing or unauthorized fund confiscation.
