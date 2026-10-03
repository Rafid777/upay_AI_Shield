"""
upay AI Shield - Scam Pattern Intelligence Service
Detects compound scam and social engineering transaction patterns using empirical telemetry.

IMPORTANT RESPONSIBLE AI DIRECTIVE:
Never declare a "confirmed scam" based on synthetic signals alone.
Status and interpretations must use cautious risk terminology:
"Potential Scam Pattern", "Requires Investigation", "Suspicious Pattern Detected".
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScamIntelligenceService:
    """
    Evaluates transactions for signature scam and social engineering patterns:
    1. UNUSUAL_HIGH_VALUE_TRANSFER
    2. NEW_RECEIVER_TRANSFER
    3. RAPID_REPEATED_TRANSFERS
    4. NEW_DEVICE_TRANSFER
    5. SUSPICIOUS_TIME_ACTIVITY
    6. MULTIPLE_FAILED_ATTEMPTS
    7. LOCATION_CHANGE
    8. HIGH_VELOCITY_ACTIVITY
    9. MULTIPLE_RISK_SIGNALS
    """

    def analyze_scam_patterns(
        self,
        transaction_data: Dict[str, Any],
        baseline_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tx_id = transaction_data.get("transaction_id", "UNKNOWN")
        amount = float(transaction_data.get("amount", 0.0))
        hour = int(transaction_data.get("hour", 12))
        is_new_device = int(transaction_data.get("is_new_device", 0)) == 1
        is_new_receiver = int(transaction_data.get("is_new_receiver", 0)) == 1
        location_changed = int(transaction_data.get("location_changed", 0)) == 1
        vel_1h = int(transaction_data.get("transactions_last_1h", 0))
        vel_24h = int(transaction_data.get("transactions_last_24h", 0))
        failed_attempts = int(transaction_data.get("failed_attempts", 0))
        amount_dev = float(transaction_data.get("amount_deviation", 1.0))
        receiver_count = int(transaction_data.get("receiver_transaction_count", 10))

        detected_patterns = []
        signals_summary = []

        # 1. UNUSUAL_HIGH_VALUE_TRANSFER
        if amount_dev >= 5.0 or (amount >= 25000.0 and amount_dev >= 3.0):
            matched = [f"Amount ৳{amount:,.2f} is {amount_dev:.1f}x higher than baseline"]
            signals_summary.append(f"Severe value anomaly: ৳{amount:,.2f} ({amount_dev:.1f}x customer norm)")
            detected_patterns.append({
                "pattern_code": "UNUSUAL_HIGH_VALUE_TRANSFER",
                "pattern_name": "Unusual High-Value Outflow",
                "severity": "CRITICAL" if amount_dev >= 10.0 else "HIGH",
                "description": f"Transaction amount of ৳{amount:,.2f} represents an abrupt {amount_dev:.1f}x deviation from customer's historical average.",
                "matched_signals": matched,
                "recommendation": "Confirm customer intended transfer and check if customer is acting under coercion or urgent social engineering scam pressure."
            })

        # 2. NEW_RECEIVER_TRANSFER
        if is_new_receiver:
            matched = ["First-time transfer to unseen beneficiary"]
            if receiver_count <= 2:
                matched.append("Recipient account has little to no transaction history")
            signals_summary.append("Transfer directed to a newly added, previously unverified counterparty")
            detected_patterns.append({
                "pattern_code": "NEW_RECEIVER_TRANSFER",
                "pattern_name": "Unverified Beneficiary Outflow",
                "severity": "HIGH" if (amount_dev > 2.0 or receiver_count <= 1) else "MEDIUM",
                "description": "Payment routed to a recipient with zero prior transactions from this customer.",
                "matched_signals": matched,
                "recommendation": "Verify beneficiary identity and ensure customer was not misled into sending funds to a fraudulent agent or fake merchant."
            })

        # 3. RAPID_REPEATED_TRANSFERS
        if vel_1h >= 5 or (vel_24h >= 18 and vel_1h >= 3):
            matched = [f"{vel_1h} transactions initiated in the past hour", f"{vel_24h} transactions in 24 hours"]
            signals_summary.append(f"Rapid repeated activity ({vel_1h} txs/hour)")
            detected_patterns.append({
                "pattern_code": "RAPID_REPEATED_TRANSFERS",
                "pattern_name": "Rapid Successive Transfer Surge",
                "severity": "HIGH" if vel_1h >= 7 else "MEDIUM",
                "description": f"Observed abnormal burst velocity with {vel_1h} transfers within 60 minutes.",
                "matched_signals": matched,
                "recommendation": "Inspect for automated scripting, rapid drain attack, or panicky repeated transfers under telephone fraud instructions."
            })

        # 4. NEW_DEVICE_TRANSFER
        if is_new_device:
            signals_summary.append("Originating device hardware ID is not registered on customer's account")
            detected_patterns.append({
                "pattern_code": "NEW_DEVICE_TRANSFER",
                "pattern_name": "Unrecognized Device Fingerprint",
                "severity": "HIGH" if (location_changed or amount_dev >= 3.0) else "MEDIUM",
                "description": "Session authenticated from a mobile hardware ID not previously associated with this customer.",
                "matched_signals": ["Unregistered hardware fingerprint detected"],
                "recommendation": "Establish out-of-band contact via registered mobile phone number to verify device enrollment."
            })

        # 5. SUSPICIOUS_TIME_ACTIVITY
        if hour < 6 or hour >= 23:
            signals_summary.append(f"Off-hours activity at {hour:02d}:00 (outside normal daylight operating hours)")
            detected_patterns.append({
                "pattern_code": "SUSPICIOUS_TIME_ACTIVITY",
                "pattern_name": "Anomalous Circadian Activity Window",
                "severity": "MEDIUM" if not is_new_device else "HIGH",
                "description": f"Transaction initiated at {hour:02d}:00, diverging significantly from typical MFS active usage windows.",
                "matched_signals": [f"Initiated at {hour:02d}:00"],
                "recommendation": "Verify whether the customer habitually conducts nocturnal transfers or if the session indicates unauthorized off-hours compromise."
            })

        # 6. MULTIPLE_FAILED_ATTEMPTS
        if failed_attempts >= 2:
            signals_summary.append(f"Cluster of {failed_attempts} failed authentication attempts preceding transaction")
            detected_patterns.append({
                "pattern_code": "MULTIPLE_FAILED_ATTEMPTS",
                "pattern_name": "Preceding Authentication Friction Cluster",
                "severity": "HIGH" if failed_attempts >= 3 else "MEDIUM",
                "description": f"Account recorded {failed_attempts} sequential failed login/PIN verification attempts before this successful execution.",
                "matched_signals": [f"{failed_attempts} consecutive failed attempts"],
                "recommendation": "Check for brute-force PIN guessing, credential spraying, or password reset social engineering."
            })

        # 7. LOCATION_CHANGE
        if location_changed:
            loc = transaction_data.get("location", "Unusual Region")
            signals_summary.append(f"Geographic discrepancy: Originated from {loc}")
            detected_patterns.append({
                "pattern_code": "LOCATION_CHANGE",
                "pattern_name": "Geographic Telemetry Discrepancy",
                "severity": "MEDIUM" if not is_new_device else "HIGH",
                "description": f"Transaction originated from {loc}, diverging from customer's home district baseline.",
                "matched_signals": [f"Current location {loc} differs from home region"],
                "recommendation": "Verify customer travel status or use of proxy/VPN masking."
            })

        # 8. HIGH_VELOCITY_ACTIVITY
        if vel_1h >= 7:
            signals_summary.append(f"Extremely high velocity: {vel_1h} transactions/hr")
            detected_patterns.append({
                "pattern_code": "HIGH_VELOCITY_ACTIVITY",
                "pattern_name": "Extreme Velocity Surge",
                "severity": "CRITICAL" if vel_1h >= 10 else "HIGH",
                "description": f"Velocity of {vel_1h} tx/hr exceeds 99.5th percentile of normal customer behavior.",
                "matched_signals": [f"{vel_1h} transactions in 1 hour"],
                "recommendation": "Immediate operational hold suggested for human analyst contact before further balance dissipation."
            })

        # 9. MULTIPLE_RISK_SIGNALS
        signal_count = len(signals_summary)
        if signal_count >= 3:
            detected_patterns.append({
                "pattern_code": "MULTIPLE_RISK_SIGNALS",
                "pattern_name": "Compound Multi-Factor Scam Signature",
                "severity": "CRITICAL" if signal_count >= 5 else "HIGH",
                "description": f"Session exhibits {signal_count} compounding risk indicators spanning device, recipient, circadian timing, and transaction value.",
                "matched_signals": signals_summary[:5],
                "recommendation": "Priority triage: Confluence of multiple anomalies strongly suggests coordinated account takeover or active scam manipulation."
            })

        # Determine overall severity
        severities = [p["severity"] for p in detected_patterns]
        if "CRITICAL" in severities:
            highest_sev = "CRITICAL"
        elif "HIGH" in severities:
            highest_sev = "HIGH"
        elif "MEDIUM" in severities:
            highest_sev = "MEDIUM"
        else:
            highest_sev = "LOW"

        status = "Requires Human Investigation" if highest_sev in ["HIGH", "CRITICAL"] else (
            "Additional Monitoring Advised" if highest_sev == "MEDIUM" else "Standard Monitoring"
        )

        guidance = (
            "Potential scam pattern indicators detected. Do not autonomously freeze funds; initiate out-of-band customer verification "
            "to determine whether transaction was authorized and free of coercive social engineering."
            if detected_patterns else
            "Telemetry conforms to standard operational tolerances. No acute scam signatures observed."
        )

        # Calculate continuous scam_score (0–100)
        scam_score = 5.0
        for p in detected_patterns:
            sev = p.get("severity", "LOW")
            if sev == "CRITICAL":
                scam_score += 30.0
            elif sev == "HIGH":
                scam_score += 20.0
            elif sev == "MEDIUM":
                scam_score += 10.0
            else:
                scam_score += 5.0
        scam_score = float(min(round(scam_score, 1), 100.0))

        top_pattern_name = detected_patterns[0]["pattern_name"] if detected_patterns else "Standard Transfer Pattern"
        confidence_str = "HIGH" if highest_sev in ["HIGH", "CRITICAL"] else ("MEDIUM" if highest_sev == "MEDIUM" else "LOW")

        return {
            "transaction_id": tx_id,
            "scam_score": scam_score,
            "pattern": top_pattern_name,
            "confidence": confidence_str,
            "signals": signals_summary,
            "evidence": [f"{p['pattern_name']}: {p['description']}" for p in detected_patterns],
            "requires_human_review": highest_sev in ["HIGH", "CRITICAL"],
            "patterns_detected": detected_patterns,
            "highest_severity": highest_sev,
            "status": status,
            "signals_summary": signals_summary,
            "investigation_guidance": guidance
        }


scam_service = ScamIntelligenceService()
