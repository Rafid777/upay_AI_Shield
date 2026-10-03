# Scam Pattern Intelligence — upay AI Shield
**Automated Typology Detection & Suspicion Signal Engine**

---

## 1. Overview & Core Philosophy

The **Scam Pattern Intelligence** engine serves as an intermediate heuristic and behavioral layer situated between the **XGBoost Risk Model** and the **Gemini Investigation Assistant**.

```
Transaction → XGBoost Score → Behavioral Baseline → Scam Pattern Engine → Evidence Signals → Human Review
```

### Critical Legal & Ethical Constraint
> **Important Compliance Rule**:
> The system **never** claims "confirmed scam" or "proven fraud" based on algorithmic or synthetic signals. All detections are classified as:
> - **Potential Scam Pattern**
> - **Requires Human Investigation**
> - **Suspicious Behavioral Signals Detected**

---

## 2. Nine Empirical Scam Typologies

The engine evaluates each transaction against nine distinct empirical patterns derived from mobile financial services (MFS) abuse patterns in Bangladesh:

| Pattern Key | Typology Title | Detection Criteria | Typical Fraud Scenario in Bangladesh MFS |
| :--- | :--- | :--- | :--- |
| `UNUSUAL_HIGH_VALUE_TRANSFER` | Unusual High-Value Transfer | Transaction amount $\ge 3.0\times$ customer 30-day baseline average, OR absolute amount $\ge \text{৳}25,000$. | Social engineering / fake lottery scam coercing victim into large immediate transfer. |
| `NEW_RECEIVER_TRANSFER` | First-Time Recipient Transfer | `is_new_receiver == 1` with high value or amount deviation $\ge 2.5\times$. | Impersonation scam directing funds to an unverified mule wallet. |
| `RAPID_REPEATED_TRANSFERS` | Rapid Repeated Velocity | `transactions_last_1h >= 5` with multiple high-velocity transfers. | Account draining after credential compromise. |
| `NEW_DEVICE_TRANSFER` | Unregistered Device Activity | `is_new_device == 1` combined with off-hours or high transaction value. | SIM swap, handset theft, or phishing credential takeover. |
| `SUSPICIOUS_TIME_ACTIVITY` | Off-Hours Activity Window | Transaction occurs between `00:00` and `05:00` (Dhaka Time), or outside customer's habitual activity hours. | Unauthorized night-time draining when customer is asleep and cannot notice SMS alerts. |
| `MULTIPLE_FAILED_ATTEMPTS` | Pre-Transaction Auth Failures | `failed_attempts >= 3` prior to successful PIN/OTP entry. | Credential stuffing or brute-force PIN guessing. |
| `LOCATION_CHANGE` | Geographic Anomaly | `location_changed == 1` across distinct Bangladesh administrative divisions. | Distant unauthorized login attempt via compromised web portal or remote session. |
| `HIGH_VELOCITY_ACTIVITY` | Elevated Hourly Velocity | `transactions_last_1h >= 4` or `transactions_last_24h >= 15`. | Smurfing or automated bot-assisted cash-out operations. |
| `MULTIPLE_RISK_SIGNALS` | Multi-Vector Risk Convergence | Concurrent trigger of $\ge 3$ distinct risk signals (e.g. New Device + New Location + Off-Hours + High Velocity). | Critical Account Takeover (ATO) or coordinated syndicate cash-out. |

---

## 3. Data-Driven Evidence Output

The pattern engine generates structured diagnostic evidence rather than arbitrary boolean flags:

```json
{
  "transaction_id": "TX103934",
  "patterns_detected": [
    {
      "pattern_code": "UNUSUAL_HIGH_VALUE_TRANSFER",
      "pattern_name": "Unusual High-Value Transfer",
      "severity": "CRITICAL",
      "description": "Transaction amount ৳31,495.48 exceeds customer historical baseline average by 19.0x.",
      "evidence": {
        "amount_bdt": 31495.48,
        "amount_deviation": 18.98,
        "baseline_avg_bdt": 1659.4
      }
    },
    {
      "pattern_code": "NEW_DEVICE_TRANSFER",
      "pattern_name": "Unregistered Device Transfer",
      "severity": "HIGH",
      "description": "Transaction originated from previously unseen device DEV01037.",
      "evidence": {
        "device_id": "DEV01037",
        "known_customer_devices": 1
      }
    },
    {
      "pattern_code": "SUSPICIOUS_TIME_ACTIVITY",
      "pattern_name": "Off-Hours Activity Window",
      "severity": "MEDIUM",
      "description": "Executed at 00:42 AM, outside the customer's typical operating window (08:00 AM – 10:00 PM).",
      "evidence": {
        "hour": 0,
        "typical_hours": "08:00 - 22:00"
      }
    }
  ],
  "highest_severity": "CRITICAL",
  "status": "Requires Human Investigation",
  "signals_summary": "3 suspicious behavioral indicators detected: High-value anomaly, new device, and nocturnal activity.",
  "investigation_guidance": "Verify whether customer authorized device DEV01037 and validate the recipient account identity before clearing."
}
```

---

## 4. Integration with Human Review

- Every detected scam pattern is presented in the **Investigation Workspace** under Section 6.
- The analyst can immediately escalate the evidence into a formal **Case** (`POST /api/v1/cases`).
- If confirmed by customer outreach (e.g., SIM swap or vishing victim), the analyst marks the decision `CONFIRM_SUSPICIOUS`, feeding the ground-truth back into the model retraining pipeline.
