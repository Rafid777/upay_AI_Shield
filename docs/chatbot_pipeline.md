# Gemini AI Investigation Assistant Pipeline — upay AI Shield

## 1. Architectural Role of Gemini
In **upay AI Shield**, Large Language Models (LLMs) are **never used as numerical fraud classifiers**. Financial risk scoring requires deterministic mathematical calibration provided by XGBoost and SHAP. 

Gemini 2.5 Flash functions exclusively as a **cognitive synthesis and investigation copilot**:

```
Transaction Telemetry
         ↓
  XGBoost Engine  ──► Risk Probability (0.0 to 1.0)
         ↓
SHAP TreeExplainer ──► Quantified Feature Attribution
         ↓
Evidence Aggregator ──► Structured JSON Context
         ↓
Gemini 2.5 Flash ──► Investigation Assistant (Brief & Q&A)
         ↓
Human Fraud Analyst ──► Final Consequential Decision
```

---

## 2. Guardrails & System Instructions
The assistant operates under strict governance rules:
1. **No Autonomous Confirmation:** The AI must never state with certainty that a transaction is fraudulent.
2. **No Data Hallucination:** The assistant only reasons over the supplied transaction telemetry, customer baseline, and SHAP vectors.
3. **No Autonomous Fund Freezing:** Financial decisions require a certified human analyst.
4. **Structured JSON Output:** Responses are formatted into discrete fields: `summary`, `key_findings`, `evidence_to_review`, and `recommended_action`.

---

## 3. Graceful Fallback Architecture
If the external Gemini API is unreachable, times out, or experiences rate limits, the system does not crash or block users. It activates a **deterministic safe fallback engine** that compiles the exact same structured JSON contract directly from the XGBoost risk score and SHAP feature vectors.
