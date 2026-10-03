"""
upay AI Shield V3 - Deterministic Rule Engine
Evaluates transparent, auditable business and risk rules to produce
a deterministic rule_score (0–100) and triggered rule explanations.
"""

from typing import Dict, Any, List


class DeterministicRuleEngine:
    """
    Transparent, verifiable financial risk rule evaluator.
    Provides immediate policy-based risk signals independent of ML probability.
    """

    def evaluate_rules(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        amount = float(transaction_data.get("amount", 0.0))
        amount_dev = float(transaction_data.get("amount_deviation", 1.0))
        is_new_device = int(transaction_data.get("is_new_device", 0)) == 1
        is_new_receiver = int(transaction_data.get("is_new_receiver", 0)) == 1
        location_changed = int(transaction_data.get("location_changed", 0)) == 1
        hour = int(transaction_data.get("hour", 12))
        vel_1h = int(transaction_data.get("transactions_last_1h", 0))
        failed_attempts = int(transaction_data.get("failed_attempts", 0))

        triggered_rules = []
        raw_score = 0.0

        # Rule 1: Extreme Amount Surge (>= 5x baseline)
        if amount_dev >= 5.0:
            weight = 25.0 if amount_dev >= 10.0 else 18.0
            triggered_rules.append({
                "rule_id": "RULE_AMOUNT_SURGE",
                "name": "Extreme Amount Deviation",
                "description": f"Transfer amount is {amount_dev:.1f}x higher than customer baseline average.",
                "weight": weight
            })
            raw_score += weight

        # Rule 2: Unregistered Device
        if is_new_device:
            weight = 20.0
            triggered_rules.append({
                "rule_id": "RULE_NEW_DEVICE",
                "name": "Unregistered Device Authentication",
                "description": "Session authenticated from a hardware identifier never previously linked to this account.",
                "weight": weight
            })
            raw_score += weight

        # Rule 3: High-Value First-Time Beneficiary
        if is_new_receiver and (amount_dev >= 2.0 or amount >= 15000.0):
            weight = 15.0
            triggered_rules.append({
                "rule_id": "RULE_NEW_RECEIVER_SURGE",
                "name": "First-Time Recipient High Outflow",
                "description": "Substantial fund transfer routed to an unverified, newly introduced beneficiary account.",
                "weight": weight
            })
            raw_score += weight

        # Rule 4: Velocity Burst (>= 5 tx/1h)
        if vel_1h >= 5:
            weight = 20.0 if vel_1h >= 8 else 15.0
            triggered_rules.append({
                "rule_id": "RULE_VELOCITY_BURST",
                "name": "Short-Term Velocity Surge",
                "description": f"Encountered {vel_1h} transactions within 60 minutes, exceeding normal operational limits.",
                "weight": weight
            })
            raw_score += weight

        # Rule 5: Nocturnal Off-Hours Activity (00:00 - 05:59)
        if 0 <= hour <= 5:
            weight = 12.0
            triggered_rules.append({
                "rule_id": "RULE_NOCTURNAL_HOUR",
                "name": "Off-Hours Transaction Window",
                "description": f"Transaction initiated at {hour:02d}:00 during overnight inactivity window.",
                "weight": weight
            })
            raw_score += weight

        # Rule 6: Preceding Authentication Friction (>= 3 failed logins)
        if failed_attempts >= 3:
            weight = 18.0 if failed_attempts >= 5 else 12.0
            triggered_rules.append({
                "rule_id": "RULE_AUTH_FAILURES",
                "name": "Pre-Transaction Authentication Failures",
                "description": f"Preceded by {failed_attempts} failed login/PIN challenge attempts.",
                "weight": weight
            })
            raw_score += weight

        # Rule 7: Geographic Location Discrepancy
        if location_changed:
            weight = 10.0
            triggered_rules.append({
                "rule_id": "RULE_LOCATION_SHIFT",
                "name": "Geographic Telemetry Discrepancy",
                "description": "Originating location diverges from customer's habitual residential district.",
                "weight": weight
            })
            raw_score += weight

        # Rule 8: Absolute High Value Outflow (>= ৳50,000)
        if amount >= 50000.0:
            weight = 15.0
            triggered_rules.append({
                "rule_id": "RULE_HIGH_VALUE_THRESHOLD",
                "name": "Large Value Transaction Policy Trigger",
                "description": f"Transaction amount of ৳{amount:,.2f} exceeds high-value threshold (৳50,000).",
                "weight": weight
            })
            raw_score += weight

        rule_score = float(min(round(raw_score, 1), 100.0))

        return {
            "rule_score": rule_score,
            "triggered_rules_count": len(triggered_rules),
            "triggered_rules": triggered_rules,
            "status": "POLICY_FLAGGED" if rule_score >= 40.0 else "POLICY_PASSED"
        }


rule_engine = DeterministicRuleEngine()
