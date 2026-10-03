# Responsible AI & Ethical Governance Framework — upay AI Shield

## 1. Executive Commitment
**upay AI Shield** is built from the ground up on principles of safety, transparency, accountability, and fairness. In the financial sector, where algorithmic decisions can severely impact individuals' livelihoods and access to funds, automated black-box decisions or unconstrained AI agents pose unacceptable risks.

Our architecture enforces strict boundaries between:
1. **Statistical Risk Scoring (XGBoost)**
2. **Mathematical Local Attribution (SHAP TreeExplainer)**
3. **Generative Synthesis & Investigation Assistance (Gemini 2.5 Flash)**
4. **Human Reviewer Judgment (The Fraud Analyst)**

---

## 2. Core Pillars of Responsible AI

### 2.1 Human Oversight & Non-Autonomous Decision Policy
- **Absolute Rule:** The system **NEVER** autonomously freezes, blocks, cancels, or alters a consequential financial transaction.
- **Role of the Machine Learning Model:** The model acts exclusively as a prioritized triage filter. It outputs a continuous probability $[0.0, 1.0]$ and assigns a standardized operational level (`LOW`, `MEDIUM`, `HIGH`).
- **Role of the Analyst:** Every `HIGH` risk transaction triggers a mandatory `HUMAN_REVIEW` alert. The analyst inspects the transaction, reviews customer history, checks SHAP attributions, and decides whether to approve, flag, or request out-of-band verification.
- **Audit Logging:** Every human determination (`SUSPICIOUS`, `LEGITIMATE`, `NEEDS_REVIEW`) is permanently timestamped and stored alongside the analyst's ID and rationale in the relational database.

### 2.2 Explainable AI (XAI) by Design
- **No Black Boxes:** Traditional ensemble trees often suffer from opacity. upay AI Shield directly integrates `shap.TreeExplainer` into the inference pipeline.
- **Local Feature Attributions:** For every evaluated transaction, exact Shapley values ($\phi_i$) quantify whether a factor pushed the score toward risk ($+\phi$) or toward legitimacy ($-\phi$).
- **Plain-English Context:** Attributions are converted into accessible, natural-language explanations (e.g., *"Transaction amount is 8.5x higher than customer's 30-day baseline"*).
- **Global Transparency:** Analysts and compliance officers can inspect global feature importance and summary plots directly within the platform.

### 2.3 Grounded Generative AI & Anti-Hallucination Guardrails
- **Investigation Assistant, Not Decision Maker:** Google Gemini 2.5 Flash is strictly used as an investigative research assistant. It is **never** used as a direct risk classifier.
- **Strict Evidence Grounding:** Gemini operates under system instructions strictly prohibiting:
  - Declaring fraud confirmed without empirical proof.
  - Inventing details not present in the supplied telemetry or customer profile.
  - Making definitive legal accusations against individuals or entities.
- **Deterministic Safe Fallback:** In the event of API limits, network interruptions, or timeout events, the system immediately engages a deterministic fallback engine that synthesizes the actual XGBoost and SHAP evidence into the structured response contract without hallucination.

### 2.4 Data Privacy & Security
- **100% Synthetic Benchmark Data:** All 20,000 transactions and 5,000 customer profiles used in this project are synthetic. No real customer PII, real account numbers, or proprietary bank logs are accessed or stored.
- **No Client-Side Secrets:** `GEMINI_API_KEY` and database credentials are kept exclusively on the backend and read from environment variables (`.env`). The frontend communicates only through authenticated REST endpoints.
- **Leakage Prevention:** Identifiers (`customer_id`, `receiver_id`, `device_id`, `transaction_id`) are strictly excluded from model feature sets to prevent target leakage and overfitting to specific entity tokens.

### 2.5 Network & Relationship Intelligence Language
- When displaying entity clusters (e.g., high fan-in accounts, shared hardware fingerprints), the platform strictly uses cautious, non-prejudicial terminology:
  - *"Suspicious network pattern"*
  - *"Potential coordinated activity"*
  - *"Requires investigation"*
- It **never** labels an entity as a "confirmed money mule" or "criminal" without formal judicial and compliance due process.

### 2.6 Fairness, Bias Mitigation & Group Considerations
- Models trained on financial data can inherit biases regarding geography or transaction sizes.
- In our preprocessing and feature engineering:
  - Raw locations are abstracted into change indicators (`location_changed: 0/1`) rather than demographic or regional labels.
  - Amounts are normalized against the *customer's own historical baseline* (`amount_deviation`) rather than broad socio-economic groupings.
  - Stratified sampling guarantees representation across both normal and anomalous distributions.

### 2.7 Known Limitations & Future Work
- **Synthetic Data Boundaries:** While realistic, synthetic data cannot capture the full range of adversarial behaviors seen in live payment systems.
- **Drift & Concept Adaptation:** In a production setting, continuous monitoring for covariate shift and scheduled retraining using the collected analyst feedback loop is mandatory.
- **Human Error:** Analyst feedback itself can be subject to human error or fatigue; secondary review workflows should be implemented for high-stakes decisions.
