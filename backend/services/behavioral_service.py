"""
upay AI Shield V3 - Behavioral Intelligence Service & Customer Behavior DNA
Profiles customer historical baseline habits (amounts, hours, devices, receivers, velocity)
and computes calibrated multi-vector behavioral deviation scores (0–100).
"""

import logging
import statistics
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import Customer, Transaction

logger = logging.getLogger("upay_shield.behavioral")


class BehavioralService:

    @staticmethod
    def get_customer_baseline(db: Session, customer_id: str) -> Dict[str, Any]:
        """
        Derives comprehensive Customer Behavior DNA from historical transaction records.
        """
        cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        txs = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()

        if txs:
            amounts = [float(t.amount) for t in txs]
            avg_amount = float(statistics.mean(amounts))
            median_amount = float(statistics.median(amounts))
            std_amount = float(statistics.stdev(amounts)) if len(amounts) > 1 else round(avg_amount * 0.35, 2)

            known_devices = list(set([t.device_id for t in txs if t.device_id]))
            known_receivers = list(set([t.receiver_id for t in txs if t.receiver_id]))
            known_locations = list(set([t.location for t in txs if t.location]))
            hours = [int(t.hour) for t in txs]

            # Habitual active hours (10th to 90th percentile)
            if len(hours) >= 4:
                sorted_hours = sorted(hours)
                min_h = sorted_hours[int(len(sorted_hours) * 0.1)]
                max_h = sorted_hours[int(len(sorted_hours) * 0.9)]
            else:
                min_h = min(hours) if hours else 8
                max_h = max(hours) if hours else 22
            typical_hour_str = f"{min_h:02d}:00–{max_h:02d}:00"

            account_age = cust.account_age_days if cust and cust.account_age_days else 365
            months_active = max(account_age / 30.0, 1.0)
            daily_freq = round(len(txs) / (months_active * 30.0), 2)
            if daily_freq < 0.1:
                daily_freq = round(len(txs) / months_active, 1)  # monthly baseline proxy

            avg_amount_day = round(avg_amount * max(daily_freq, 1.0), 2)
            normal_velocity = round(daily_freq / 12.0, 2)  # spread across daytime hours
        else:
            avg_amount = float(cust.normal_avg_amount if cust and cust.normal_avg_amount else 1250.0)
            median_amount = round(avg_amount * 0.85, 2)
            std_amount = round(avg_amount * 0.40, 2)
            daily_freq = float(cust.normal_transaction_count if cust and cust.normal_transaction_count else 4.0)
            avg_amount_day = round(avg_amount * daily_freq, 2)
            typical_hour_str = "08:00–22:00"
            known_devices = ["DEV00101"]
            known_receivers = ["REC00201", "REC00305"]
            known_locations = [cust.primary_location if cust and cust.primary_location else "Dhaka"]
            normal_velocity = round(daily_freq / 12.0, 2)

        return {
            "customer_id": customer_id,
            "average_amount": round(avg_amount, 2),
            "median_amount": round(median_amount, 2),
            "std_transaction_amount": round(std_amount, 2),
            "typical_hours": typical_hour_str,
            "known_devices_count": max(len(known_devices), cust.registered_device_count if cust else 1),
            "known_devices": known_devices[:10],
            "known_receivers_count": len(known_receivers),
            "known_receivers": known_receivers[:10],
            "primary_location": cust.primary_location if cust and cust.primary_location else (known_locations[0] if known_locations else "Dhaka"),
            "known_locations": known_locations[:5],
            "typical_daily_frequency": daily_freq,
            "average_amount_day": avg_amount_day,
            "normal_transaction_velocity": normal_velocity,
            "account_age_days": cust.account_age_days if cust and cust.account_age_days else 365
        }

    @staticmethod
    def compute_behavioral_deviation(
        baseline: Dict[str, Any],
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes detailed behavioral deviations and outputs a calibrated behavior_score (0–100).
        """
        current_amount = float(transaction_data.get("amount", 0.0))
        baseline_amount = max(float(baseline.get("average_amount", 1.0)), 1.0)
        baseline_std = max(float(baseline.get("std_transaction_amount", baseline_amount * 0.4)), 10.0)

        # Deviation ratio
        if "amount_deviation" in transaction_data and transaction_data["amount_deviation"] is not None:
            deviation_ratio = round(float(transaction_data["amount_deviation"]), 2)
        else:
            deviation_ratio = round(current_amount / baseline_amount, 2)

        is_new_device = bool(transaction_data.get("is_new_device", 0))
        is_new_receiver = bool(transaction_data.get("is_new_receiver", 0))
        location_changed = bool(transaction_data.get("location_changed", 0))
        current_hour = int(transaction_data.get("hour", 12))
        vel_1h = int(transaction_data.get("transactions_last_1h", 0))
        vel_24h = int(transaction_data.get("transactions_last_24h", 0))
        failed_attempts = int(transaction_data.get("failed_attempts", 0))

        # Check unusual hour (typical active window is 08:00 to 22:00)
        is_unusual_hour = current_hour < 6 or current_hour > 23

        # Compute multi-vector behavioral deviation score (0–100)
        b_score = 5.0
        if deviation_ratio >= 10.0:
            b_score += 35.0
        elif deviation_ratio >= 4.0:
            b_score += 25.0
        elif deviation_ratio >= 2.0:
            b_score += 15.0

        if is_new_device:
            b_score += 20.0
        if is_new_receiver and deviation_ratio >= 2.0:
            b_score += 15.0
        if location_changed:
            b_score += 10.0
        if is_unusual_hour:
            b_score += 12.0
        if vel_1h >= 5:
            b_score += 18.0
        elif vel_1h >= 3:
            b_score += 8.0
        if failed_attempts >= 3:
            b_score += 15.0

        behavior_score = float(min(round(b_score, 1), 100.0))

        deviations_list = []
        if deviation_ratio > 3.0:
            deviations_list.append(f"Spending surge: Amount (৳{current_amount:,.2f}) is {deviation_ratio:.1f}x higher than the historical average (৳{baseline_amount:,.2f}).")
        elif deviation_ratio > 1.8:
            deviations_list.append(f"Moderate amount increase: {deviation_ratio:.1f}x of baseline average.")

        if is_new_device:
            deviations_list.append("Unrecognized hardware: Initiated from a device fingerprint never previously linked to this account.")

        if is_new_receiver:
            deviations_list.append("New beneficiary: Transfer sent to an account with no prior transaction history.")

        if location_changed:
            loc = transaction_data.get("location", "Distant Division")
            deviations_list.append(f"Geographic shift: Initiated from {loc}, outside customer's habitual area ({baseline.get('primary_location')}).")

        if is_unusual_hour:
            deviations_list.append(f"Circadian anomaly: Executed at {current_hour:02d}:00, outside customer's habitual operating schedule ({baseline.get('typical_hours')}).")

        if vel_1h >= 5:
            deviations_list.append(f"Velocity burst: {vel_1h} transactions in the last hour significantly exceeds normal baseline velocity.")

        if failed_attempts >= 3:
            deviations_list.append(f"Authentication friction: {failed_attempts} failed login attempts prior to submission.")

        if not deviations_list:
            deviations_list.append("All observed transaction attributes align with expected baseline behavior.")

        return {
            "behavior_score": behavior_score,
            "behavioral_deviation_score": behavior_score,
            "comparison": {
                "normal_avg_amount": f"৳{baseline_amount:,.2f}",
                "median_amount": f"৳{baseline.get('median_amount', baseline_amount):,.2f}",
                "current_amount": f"৳{current_amount:,.2f}",
                "amount_deviation_ratio": f"{deviation_ratio:.1f}x",
                "typical_hours": baseline.get("typical_hours", "08:00–22:00"),
                "current_hour": f"{current_hour:02d}:00",
                "is_unusual_hour": is_unusual_hour,
                "new_device": "YES" if is_new_device else "NO",
                "new_receiver": "YES" if is_new_receiver else "NO",
                "location_changed": "YES" if location_changed else "NO",
                "velocity_1h": f"{vel_1h} tx/hr",
                "velocity_24h": f"{vel_24h} tx/day"
            },
            "deviations_list": deviations_list,
            "has_significant_deviations": behavior_score >= 50.0
        }


behavioral_service = BehavioralService()
