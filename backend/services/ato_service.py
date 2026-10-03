"""
upay AI Shield - Account Takeover (ATO) Intelligence Service
Analyzes combinations of authentication, device, geographic, and velocity anomalies
to isolate potential account takeover indicators.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ATOService:

    @staticmethod
    def evaluate_ato_signals(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates multi-signal combinations typical of credential stuffing and account takeover.
        CRITICAL GOVERNANCE: Always uses cautious language ('potential indicators'), never confirms crimes.
        """
        is_new_device = bool(transaction_data.get("is_new_device", 0))
        location_changed = bool(transaction_data.get("location_changed", 0))
        is_new_receiver = bool(transaction_data.get("is_new_receiver", 0))
        failed_attempts = int(transaction_data.get("failed_attempts", 0))
        current_hour = int(transaction_data.get("hour", 12))
        amount_dev = float(transaction_data.get("amount_deviation", 1.0))
        vel_1h = int(transaction_data.get("transactions_last_1h", 0))

        is_unusual_hour = current_hour < 6 or current_hour > 23

        detected_signals = []
        score_weight = 0

        # 1. Unrecognized device
        if is_new_device:
            detected_signals.append({
                "code": "ATO_NEW_DEVICE",
                "label": "Unregistered Device Fingerprint",
                "description": "Transaction initiated from a hardware identifier with no prior association to this account.",
                "weight": 25
            })
            score_weight += 25

        # 2. Location anomaly
        if location_changed:
            detected_signals.append({
                "code": "ATO_LOCATION_SHIFT",
                "label": "Geographic Origin Anomaly",
                "description": "Origin IP or geographic coordinates deviate from customer's home region.",
                "weight": 20
            })
            score_weight += 20

        # 3. Preceding failed logins
        if failed_attempts >= 3:
            detected_signals.append({
                "code": "ATO_FAILED_AUTH",
                "label": f"Repeated Failed Logins ({failed_attempts} attempts)",
                "description": f"Encountered {failed_attempts} failed authentication attempts prior to session establishment.",
                "weight": 25
            })
            score_weight += 25
        elif failed_attempts > 0:
            detected_signals.append({
                "code": "ATO_FAILED_AUTH_MINOR",
                "label": f"Failed Login ({failed_attempts} attempt)",
                "description": f"Preceded by {failed_attempts} failed credentials challenge.",
                "weight": 10
            })
            score_weight += 10

        # 4. Beneficiary unfamiliarity
        if is_new_receiver and (is_new_device or location_changed):
            detected_signals.append({
                "code": "ATO_NEW_BENEFICIARY",
                "label": "First-Time Recipient Following Device/Location Shift",
                "description": "High-risk pattern: immediate fund routing to unseen recipient after environment change.",
                "weight": 20
            })
            score_weight += 20

        # 5. Circadian disruption
        if is_unusual_hour:
            detected_signals.append({
                "code": "ATO_OFF_HOURS",
                "label": f"Off-Hours Activity ({current_hour:02d}:00)",
                "description": "Transaction scheduled during typical sleep hours (00:00 - 05:59).",
                "weight": 10
            })
            score_weight += 10

        # 6. Sudden high amount surge
        if amount_dev >= 5.0:
            detected_signals.append({
                "code": "ATO_AMOUNT_SURGE",
                "label": f"Significant Balance Drain Surge ({amount_dev:.1f}x baseline)",
                "description": "Attempted transaction amount drastically exceeds historical customer ticket size.",
                "weight": 15
            })
            score_weight += 15

        # 7. Velocity burst
        if vel_1h >= 5:
            detected_signals.append({
                "code": "ATO_BURST_VELOCITY",
                "label": f"Rapid Velocity Burst ({vel_1h} tx/hr)",
                "description": "Rapid succession of transfers, characteristic of account liquidation scripts.",
                "weight": 15
            })
            score_weight += 15

        # Determine ATO Severity
        if score_weight >= 60 or (is_new_device and failed_attempts >= 3 and amount_dev >= 4.0):
            severity = "HIGH"
            headline = "Potential account takeover indicators detected."
            action_guidance = "Prompt customer out-of-band verification recommended before executing transfers."
        elif score_weight >= 30:
            severity = "MEDIUM"
            headline = "Moderate account takeover signals observed."
            action_guidance = "Review device history and secondary authentication channels."
        elif score_weight > 0:
            severity = "LOW"
            headline = "Isolated behavioral variance detected."
            action_guidance = "Standard monitoring; no acute ATO indicators present."
        else:
            severity = "NONE"
            headline = "No account takeover signals detected."
            action_guidance = "Session characteristics conform to normal customer profile."

        ato_pattern_desc = (
            "Multi-Vector Account Takeover Signature" if len(detected_signals) >= 3 else
            ("Unregistered Device Shift" if is_new_device else
             ("Off-Hours Velocity Anomaly" if is_unusual_hour else "Standard Session Baseline"))
        )

        return {
            "severity": severity,
            "headline": headline,
            "signal_count": len(detected_signals),
            "ato_indicator_count": len(detected_signals),
            "ato_score": min(score_weight, 100),
            "ato_pattern": ato_pattern_desc,
            "detected_signals": detected_signals,
            "action_guidance": action_guidance,
            "disclaimer": "Automated behavioral indicators only. Not a confirmation of account compromise."
        }


ato_service = ATOService()
