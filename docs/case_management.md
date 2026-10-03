# Analyst Case Management & Investigation Workspace — upay AI Shield
**Enterprise Human-in-the-Loop Triage, Audit Trail & Decision Governance**

---

## 1. Overview & Governance Principle

In compliance with financial regulations and Responsible AI standards, **upay AI Shield** enforces a strict operational separation:
- **AI Models & Engines**: Responsible for telemetry analysis, risk scoring (0–100), SHAP factor breakdown, and narrative evidence synthesis.
- **Human Fraud Analysts**: Hold **sole consequential authority** over account freezing, fund restrictions, and case determinations.

The **Case Management System** formalizes this handoff, tracking investigations through a transparent, auditable lifecycle.

---

## 2. Case Lifecycle & State Transitions

```
[Transaction Flagged]
        │
        ▼
   ┌─────────┐
   │  OPEN   │◄── Auto-seeded or created via "Create Formal Case"
   └────┬────┘
        │ Analyst begins customer outreach or log inspection
        ▼
 ┌──────────────┐
 │ UNDER_REVIEW │
 └──────┬───────┘
        │
        ├──────────────────────────────┐
        ▼                              ▼
┌────────────────────────┐      ┌────────────┐
│ NEEDS_MORE_INFORMATION│      │  RESOLVED  │
└────────────────────────┘      └─────┬──────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              ▼                       ▼                        ▼
     CONFIRM_SUSPICIOUS        MARK_LEGITIMATE     NEEDS_MORE_INVESTIGATION
```

### Case Statuses
- **`OPEN`**: Case created; awaiting initial analyst triage.
- **`UNDER_REVIEW`**: Analyst is actively conducting customer verification, telco checks, or network queries.
- **`NEEDS_MORE_INFORMATION`**: Escalated to branch, customer care, or law enforcement liaison.
- **`RESOLVED`**: Formal human determination recorded.

### Formal Analyst Decisions
- **`CONFIRM_SUSPICIOUS`**: Analyst verified fraud/ATO/scam (e.g., customer confirms unauthorized SIM swap).
- **`MARK_LEGITIMATE`**: Analyst verified genuine customer activity (e.g., legitimate emergency transfer).
- **`NEEDS_MORE_INVESTIGATION`**: Inconclusive evidence requiring prolonged observation.

---

## 3. Case Schema & Data Model

| Field | Type | Description |
| :--- | :--- | :--- |
| `case_id` | `VARCHAR(32)` | Primary Key (e.g., `CASE-1001`, `CASE-1002`). |
| `transaction_id` | `VARCHAR(32)` | Associated transaction identifier (Foreign Key). |
| `customer_id` | `VARCHAR(32)` | Associated customer identifier. |
| `risk_score` | `FLOAT` | XGBoost risk score at time of case creation (0.00 – 100.00). |
| `risk_level` | `VARCHAR(16)` | `HIGH`, `MEDIUM`, or `LOW`. |
| `priority` | `VARCHAR(16)` | `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`. |
| `assigned_analyst`| `VARCHAR(64)` | Assigned risk analyst handle (e.g., `analyst_shafi`). |
| `status` | `VARCHAR(32)` | Lifecycle state: `OPEN`, `UNDER_REVIEW`, `NEEDS_MORE_INFORMATION`, `RESOLVED`. |
| `evidence` | `JSON` | Structured snapshot of features, SHAP factors, baseline deviations, and telemetry. |
| `analyst_notes` | `TEXT` | Human rationale, customer interview notes, and investigation steps. |
| `decision` | `VARCHAR(32)` | Final determination (`CONFIRM_SUSPICIOUS`, `MARK_LEGITIMATE`, `NEEDS_MORE_INVESTIGATION`). |
| `created_at` | `DATETIME` | UTC timestamp of case initiation. |
| `updated_at` | `DATETIME` | UTC timestamp of last status or decision update. |

---

## 4. Audit Trail (`case_events`)

Every modification to a case is permanently recorded in the `case_events` table for compliance and forensic auditing:
- `CREATED`: Logged when the case is opened.
- `STATUS_CHANGED`: Logged whenever status or priority shifts (records `old_status` and `new_status`).
- `DECISION_RECORDED`: Logged when an analyst enters a final determination, capturing analyst ID, decision, and justification notes.

---

## 5. Ten-Section Investigation Workspace

When an analyst opens any case or transaction from the dashboard, the 10-section **Investigation Workspace** presents comprehensive, unified intelligence:

1. **Case Header**: Case ID, Transaction ID, Customer ID, Risk Score gauge (0–100), Risk Level badge, and Status badge.
2. **Transaction Details**: Amount in Bangladesh Taka (`৳`), UTC timestamp, channel (`APP`, `USSD`, `WEB`), transaction type (`SEND_MONEY`, `CASH_OUT`, etc.), receiver, device, and location.
3. **Behavior Profile Comparison**: Side-by-side comparison table of 30-day baseline vs. current transaction with exact deviation multipliers.
4. **Risk Contributors (SHAP Breakdown)**: Positive risk-increasing signals with exact point additions and mitigating factors.
5. **Account Takeover (ATO) Indicators**: Multi-vector checklist (unseen device, geographic shift, nocturnal hour, failed logins).
6. **Scam Pattern Intelligence**: Empirical scam typologies triggered with severity badges.
7. **Network Intelligence**: Connected entities count, shared devices, and high-degree receiver alerts.
8. **Risk Story & Chronological Timeline**: Step-by-step narrative sequence reconstructing the suspicious session.
9. **Gemini AI Investigation Assistant**: Structured narrative brief, key findings, investigation questions, and recommended next steps (with deterministic fallback).
10. **Analyst Decision & Feedback Submission**: Radio controls for formal determination, freeform justification textarea, and one-click database commit.

---

## 6. API Reference

- `POST /api/v1/cases`: Open a formal investigation case.
- `GET /api/v1/cases`: List paginated cases with status/priority filters.
- `GET /api/v1/cases/{case_id}`: Retrieve detailed case with full event history.
- `PATCH /api/v1/cases/{case_id}`: Update status, priority, or analyst notes.
- `POST /api/v1/cases/{case_id}/decision`: Record final human decision and sync to model feedback loop.
