# Suspicious Network Intelligence — upay AI Shield
**Transaction Topology & Multi-Hop Entity Relationship Graph**

---

## 1. Overview & Objective

Fraud syndicates, mule rings, and coordinated cash-out operations rarely operate in isolation. While individual transactions may appear benign when viewed in isolation, the underlying entity relationships often reveal coordinated behavioral structures.

The **Network Intelligence** module dynamically constructs multi-hop relational graphs from actual transaction telemetry:

```
Customer ──[SENT_TO]──► Receiver ◄──[SENT_TO]── Other Customers
   │                        ▲
[USED_DEVICE]            [OCCURRED_AT]
   ▼                        │
 Device                 Location
```

---

## 2. Core Entity Graph Schema

The network engine operates across four primary node types and three directed edge types:

### Node Types
- **Customer Node** (`#3B82F6` Blue): The originating account holder in the transaction.
- **Receiver Node** (`#EF4444` Red): The counterparty account, merchant, or agent receiving funds.
- **Device Node** (`#10B981` Emerald): The hardware/browser fingerprint identifier (`DEVxxxxx`).
- **Location Node** (`#F59E0B` Amber): The Bangladesh administrative division/city where the transaction originated.

### Relational Edges
- `SENT_TO`: Financial value transfer link containing transaction count and aggregate BDT amount (`৳`).
- `USED_DEVICE`: Hardware association linking an account to a hardware fingerprint.
- `OCCURRED_AT`: Geographic association linking a transaction session to a city/division.

---

## 3. Network Risk Indicators

The engine computes network anomaly metrics without declaring unverified criminality:

1. **High Receiver Fan-In (Mule Account Pattern)**:
   - A single receiver receiving payments from $\ge 3$ distinct originating customer accounts within a short temporal window.
   - *Indicator*: `Potential High-Degree Receiver / Shared Destination`.

2. **Device Sharing (Syndicate Fingerprint)**:
   - Multiple customer accounts logging in from the same physical handset or browser fingerprint (`is_new_device == 1` across multiple accounts).
   - *Indicator*: `Multi-Account Device Reuse`.

3. **Geographic Clustering**:
   - Out-of-area customer accounts converging on a single geographic location to execute high-value cash-outs.
   - *Indicator*: `Distant Cash-Out Concentration`.

---

## 4. Responsible AI & Legal Guardrail

> **Strict Compliance Policy**:
> The network engine **never** designates an entity as a "Confirmed Money Mule", "Criminal Syndicate", or "Illegal Ring".
> All outputs are framed strictly as:
> - **Potential Suspicious Network**
> - **Shared Entity Cluster Detected**
> - **High-Degree Receiver Concentration**

---

## 5. API Reference & Payload

### Endpoint
`GET /api/v1/customers/{customer_id}/network`

### Sample Response
```json
{
  "customer_id": "CUST02516",
  "connected_customers": 4,
  "shared_receivers": 6,
  "shared_devices": 3,
  "shared_locations": 2,
  "transaction_count": 8,
  "total_transaction_amount_bdt": 58400.0,
  "total_amount_display": "৳58,400.00",
  "network_risk_indicators": [
    "High receiver degree: Receiver REC00870 receives funds from 3 distinct customers.",
    "Hardware collision: Device DEV00935 observed across multiple customer accounts."
  ],
  "nodes": [
    {"id": "CUST02516", "label": "Customer CUST02516", "type": "customer"},
    {"id": "REC00870", "label": "Receiver REC00870", "type": "receiver"},
    {"id": "DEV00935", "label": "Device DEV00935", "type": "device"},
    {"id": "Dhaka", "label": "Dhaka", "type": "location"}
  ],
  "edges": [
    {"source": "CUST02516", "target": "REC00870", "label": "৳18,500"},
    {"source": "CUST02516", "target": "DEV00935", "label": "used"},
    {"source": "CUST02516", "target": "Dhaka", "label": "in"}
  ],
  "disclaimer": "Network indicators represent structural transaction patterns. Verification by a human risk analyst is required prior to taking restrictive operational actions."
}
```

---

## 6. Interactive Frontend Visualizer

- Rendered natively via scalable vector graphics (SVG) with force-directed circular layouts.
- Interactive node inspection: Clicking any entity node displays its connected neighbors, transaction volume, and total BDT flows.
