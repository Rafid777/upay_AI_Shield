# Customer Behavior Profile — upay AI Shield
**Longitudinal Baseline Profiling & Behavioral Deviation Analysis**

---

## 1. Overview & Mathematical Formulation

To distinguish legitimate financial activities from account takeover (ATO) or scam coercion, **upay AI Shield** maintains an empirical 30-day rolling baseline for each customer account.

Rather than applying rigid static thresholds across all users, the system evaluates transactions relative to the customer's own habitual profile:

$$\text{Amount Deviation Multiplier} = \frac{\text{Current Transaction Amount}}{\max(\text{Customer Historical Baseline Average}, 1.0)}$$

$$\text{Velocity Anomaly} = \frac{\text{Transactions Last 1 Hour}}{\max(\text{Historical Hourly Baseline}, 1.0)}$$

---

## 2. Profile Structure & Metrics

### A. Normal Historical Baseline
- **Average Transaction Amount**: Historical mean monetary value in Bangladesh Taka (`৳`).
- **Typical Activity Window**: Habitual hours of active operation (e.g. `10:00 AM – 09:00 PM`).
- **Known Devices**: Set of unique device identifiers previously authenticated by the customer.
- **Known Receivers**: Distinct counterparty accounts previously transacted with.
- **Average Daily Transactions**: Mean frequency of transactions executed per 24-hour cycle.
- **Habitual Locations**: Top administrative divisions where the customer normally transacts (e.g., `Dhaka`, `Chattogram`).
- **Baseline Velocity**: Typical transactions per hour under normal conditions.

### B. Current Transaction Telemetry
- **Current Amount**: Evaluated transaction value in Bangladesh Taka (`৳`).
- **Current Hour**: Exact hour of submission (Dhaka Local Time).
- **Current Device**: Device fingerprint ID (`DEVxxxxx`).
- **Current Receiver**: Beneficiary account (`RECxxxxx`).
- **Current Location**: Originating geographic location.
- **Current Velocity**: Frequency of transactions submitted in the trailing 1-hour window.

### C. Calculated Behavioral Deviations
- **Amount Surge**: Multiplier relative to baseline (e.g., `14.8x above normal baseline`).
- **Temporal Deviation**: Flagged if submitted outside the user's historical 90th percentile operating hours.
- **Device Anomaly**: `Previously unseen device` if device fingerprint has never been authenticated by this customer.
- **Beneficiary Anomaly**: `First-time recipient` if receiver account has no prior transaction history with customer.
- **Velocity Burst**: Multiple standard deviations above typical hourly transaction volume.

---

## 3. Real Example (CUST02516)

```
CUSTOMER BEHAVIOR PROFILE
Customer: CUST02516 | Account Age: 1,242 Days

NORMAL BASELINE (30-Day History)
• Average Amount:         ৳1,476.27
• Typical Hours:          08:00 AM – 10:00 PM
• Known Devices:          1 registered device
• Known Receivers:        4 previous counterparties
• Average Daily Velocity: 3.2 transactions / day
• Primary Location:       Dhaka

CURRENT TRANSACTION (TX103934)
• Amount:                 ৳31,495.48
• Hour:                   00:42 AM (Nocturnal)
• Device:                 DEV01037 (NEW)
• Receiver:               REC00630 (NEW)
• Location:               Chattogram (CHANGED)
• Velocity Last 1h:       13 transactions / hour

BEHAVIORAL DEVIATIONS
• Amount Multiplier:      19.0× above baseline average
• Temporal Anomaly:       Outside habitual activity window
• Device Status:          Previously unseen hardware fingerprint
• Beneficiary Status:     First-time recipient
• Velocity Surge:         Significantly above normal velocity
```

---

## 4. API Reference

### Endpoint
`GET /api/v1/customers/{customer_id}/behavior`

### JSON Response Schema
```json
{
  "customer_id": "CUST02516",
  "account_age_days": 1242,
  "normal_behavior": {
    "avg_transaction_amount_bdt": 1476.27,
    "typical_hours": "08:00 - 22:00",
    "known_devices_count": 1,
    "known_receivers_count": 4,
    "avg_daily_transactions": 3.2,
    "normal_locations": ["Dhaka"],
    "baseline_velocity_per_hour": 1.0
  },
  "current_transaction": {
    "transaction_id": "TX103934",
    "amount_bdt": 31495.48,
    "hour": 0,
    "device_status": "NEW",
    "receiver_status": "NEW",
    "location_status": "CHANGED",
    "velocity_last_1h": 13
  },
  "behavioral_deviations": {
    "amount_deviation_multiplier": 18.98,
    "is_unusual_hour": true,
    "is_new_device": true,
    "is_new_receiver": true,
    "is_location_changed": true,
    "velocity_burst": true,
    "summary": "Critical divergence across 5 behavioral vectors: 19.0x amount surge, nocturnal submission, unseen device, new counterparty, and velocity burst."
  }
}
```
