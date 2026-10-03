"""
upay AI Shield V3 - Network & Entity Graph Intelligence Service
Maps multi-entity relationships (Customer <-> Receiver <-> Device <-> Location)
to detect potential coordinated activity, device sharing, and mule account patterns.
Computes a transparent, documented network_score (0–100).
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Transaction, Customer

logger = logging.getLogger("upay_shield.network")


class NetworkService:

    @staticmethod
    def calculate_network_risk_score(
        distinct_senders: int,
        shared_devices: int,
        connected_customers: int,
        total_amount: float
    ) -> float:
        """
        Calculates a transparent, documented network_score (0–100) based on
        topological risk indicators:
        - Shared hardware fingerprints across accounts: +35 points
        - High receiver fan-in (mule fund pooling pattern): +30 points
        - Multi-customer entity clustering: +20 points
        - High-value connected flow (>= ৳50,000): +15 points
        """
        score = 5.0
        if shared_devices >= 2:
            score += 35.0
        elif shared_devices == 1:
            score += 15.0

        if distinct_senders >= 4:
            score += 30.0
        elif distinct_senders >= 2:
            score += 15.0

        if connected_customers >= 3:
            score += 20.0
        elif connected_customers >= 1:
            score += 10.0

        if total_amount >= 50000.0:
            score += 15.0
        elif total_amount >= 25000.0:
            score += 8.0

        return float(min(round(score, 1), 100.0))

    @staticmethod
    def get_transaction_entity_network(db: Session, transaction_id: str) -> Dict[str, Any]:
        """
        Builds a localized relationship sub-graph around a transaction's entities:
        Customer, Receiver, Device, and Location.
        """
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not tx:
            return {"nodes": [], "edges": [], "insights": [], "network_score": 10.0}

        cust_id = tx.customer_id or "CUST_UNKNOWN"
        recv_id = tx.receiver_id or "REC_UNKNOWN"
        dev_id = tx.device_id or "DEV_UNKNOWN"
        loc = tx.location or "LOC_UNKNOWN"

        # Check receiver fan-in (how many distinct customers send to this receiver?)
        recv_senders = db.query(
            Transaction.customer_id, func.count(Transaction.transaction_id), func.sum(Transaction.amount)
        ).filter(
            Transaction.receiver_id == recv_id
        ).group_by(Transaction.customer_id).limit(10).all()

        distinct_senders_count = len(recv_senders)

        # Check device sharing (is this device shared across multiple customer accounts?)
        shared_device_users = db.query(
            Transaction.customer_id, func.count(Transaction.transaction_id)
        ).filter(
            Transaction.device_id == dev_id
        ).group_by(Transaction.customer_id).limit(10).all()

        shared_device_count = len(shared_device_users)

        nodes = [
            {"id": cust_id, "label": f"Customer ({cust_id})", "type": "customer", "primary": True},
            {"id": recv_id, "label": f"Beneficiary ({recv_id})", "type": "receiver", "primary": True},
            {"id": dev_id, "label": f"Hardware ({dev_id})", "type": "device", "primary": False},
            {"id": loc, "label": f"Location ({loc})", "type": "location", "primary": False}
        ]

        edges = [
            {"source": cust_id, "target": recv_id, "label": f"৳{float(tx.amount):,.2f}", "type": "transfer"},
            {"source": cust_id, "target": dev_id, "label": "Device Used", "type": "session"},
            {"source": cust_id, "target": loc, "label": "Originated In", "type": "geo"}
        ]

        insights = []

        # Analyze potential coordinated or mule fan-in patterns
        if distinct_senders_count >= 3:
            insights.append({
                "severity": "HIGH",
                "pattern": "High Beneficiary Fan-In (Potential Coordinated Inflow)",
                "description": f"Receiver {recv_id} has received transfers from {distinct_senders_count} distinct customer accounts. Requires investigation for coordinated fund pooling.",
                "type": "MULE_FAN_IN"
            })
            for sender_id, cnt, amt in recv_senders[:4]:
                if sender_id != cust_id:
                    nodes.append({"id": sender_id, "label": f"Customer ({sender_id})", "type": "customer", "primary": False})
                    edges.append({"source": sender_id, "target": recv_id, "label": f"৳{float(amt or 0):,.0f}", "type": "transfer"})

        if shared_device_count >= 2:
            insights.append({
                "severity": "HIGH",
                "pattern": "Multi-Account Device Sharing (Suspicious Hardware Re-use)",
                "description": f"Device {dev_id} has been utilized by {shared_device_count} distinct customer accounts. Potential indicator of organized fraud operator activity.",
                "type": "DEVICE_SHARING"
            })
            for user_id, cnt in shared_device_users[:3]:
                if user_id != cust_id and not any(n["id"] == user_id for n in nodes):
                    nodes.append({"id": user_id, "label": f"Customer ({user_id})", "type": "customer", "primary": False})
                    edges.append({"source": user_id, "target": dev_id, "label": "Shared Device", "type": "session"})

        if not insights:
            insights.append({
                "severity": "LOW",
                "pattern": "Standard Single-Channel Network Profile",
                "description": "No multi-account device sharing or anomalous beneficiary fan-in patterns detected across the immediate graph.",
                "type": "STANDARD"
            })

        net_score = NetworkService.calculate_network_risk_score(
            distinct_senders=distinct_senders_count,
            shared_devices=shared_device_count,
            connected_customers=max(len(recv_senders) - 1, 0),
            total_amount=float(tx.amount)
        )

        return {
            "transaction_id": transaction_id,
            "network_score": net_score,
            "nodes": nodes,
            "edges": edges,
            "insights": insights,
            "summary": {
                "distinct_customers_to_receiver": distinct_senders_count,
                "accounts_sharing_device": shared_device_count
            },
            "disclaimer": "Automated relationship mapping. Shows potential coordinated activity indicators; does not confirm criminality."
        }

    @staticmethod
    def get_customer_network(db: Session, customer_id: str) -> Dict[str, Any]:
        """
        Builds a multi-hop relationship graph around a specific customer:
        All known receivers, devices, locations, and other customers linked via shared devices or receivers.
        """
        txs = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
        if not txs:
            txs = db.query(Transaction).limit(10).all()
            if txs:
                customer_id = txs[0].customer_id or customer_id

        total_tx_count = len(txs)
        total_amount = sum(float(t.amount or 0.0) for t in txs)

        receivers = set()
        devices = set()
        locations = set()

        for t in txs:
            if t.receiver_id:
                receivers.add(t.receiver_id)
            if t.device_id:
                devices.add(t.device_id)
            if t.location:
                locations.add(t.location)

        nodes = [
            {"id": customer_id, "label": f"Customer ({customer_id})", "type": "customer", "primary": True}
        ]
        edges = []

        # Add receivers
        for rec in list(receivers)[:8]:
            nodes.append({"id": rec, "label": f"Beneficiary ({rec})", "type": "receiver", "primary": False})
            edges.append({"source": customer_id, "target": rec, "label": "Sent To", "type": "transfer"})

        # Add devices
        for dev in list(devices)[:5]:
            nodes.append({"id": dev, "label": f"Device ({dev})", "type": "device", "primary": False})
            edges.append({"source": customer_id, "target": dev, "label": "Used Device", "type": "session"})

        # Add locations
        for loc in list(locations)[:5]:
            nodes.append({"id": loc, "label": f"Location ({loc})", "type": "location", "primary": False})
            edges.append({"source": customer_id, "target": loc, "label": "Occurred At", "type": "geo"})

        # Find other customers sharing these devices
        shared_customers = set()
        for dev in list(devices)[:3]:
            other_dev_txs = db.query(Transaction.customer_id).filter(
                Transaction.device_id == dev,
                Transaction.customer_id != customer_id
            ).distinct().limit(5).all()
            for (other_c,) in other_dev_txs:
                if other_c:
                    shared_customers.add(other_c)
                    if not any(n["id"] == other_c for n in nodes):
                        nodes.append({"id": other_c, "label": f"Customer ({other_c})", "type": "customer", "primary": False})
                    edges.append({"source": other_c, "target": dev, "label": "Used Device", "type": "session"})

        # Find other customers sending to these receivers
        for rec in list(receivers)[:3]:
            other_rec_txs = db.query(Transaction.customer_id, func.sum(Transaction.amount)).filter(
                Transaction.receiver_id == rec,
                Transaction.customer_id != customer_id
            ).group_by(Transaction.customer_id).limit(4).all()
            for (other_c, sum_amt) in other_rec_txs:
                if other_c:
                    shared_customers.add(other_c)
                    if not any(n["id"] == other_c for n in nodes):
                        nodes.append({"id": other_c, "label": f"Customer ({other_c})", "type": "customer", "primary": False})
                    edges.append({"source": other_c, "target": rec, "label": "Sent To", "type": "transfer"})

        insights = []
        if len(shared_customers) >= 2:
            insights.append({
                "severity": "HIGH",
                "pattern": "Multi-Entity Coordinated Cluster",
                "description": f"Customer {customer_id} shares hardware or beneficiary entities with {len(shared_customers)} other accounts. Potential syndicate or mule network indicator."
            })
        if len(receivers) >= 4 and total_amount > 50000:
            insights.append({
                "severity": "MEDIUM",
                "pattern": "High-Volume Beneficiary Dispersion",
                "description": f"Fund routing across {len(receivers)} different recipients totaling ৳{total_amount:,.2f}."
            })
        if not insights:
            insights.append({
                "severity": "LOW",
                "pattern": "Standard Peer Network Profile",
                "description": "Entity connections are consistent with standard peer-to-peer personal MFS activity."
            })

        net_score = NetworkService.calculate_network_risk_score(
            distinct_senders=len(receivers),
            shared_devices=len(devices),
            connected_customers=len(shared_customers),
            total_amount=total_amount
        )

        return {
            "customer_id": customer_id,
            "network_score": net_score,
            "connected_customers": len(shared_customers),
            "shared_receivers": len(receivers),
            "shared_devices": len(devices),
            "shared_locations": len(locations),
            "transaction_count": total_tx_count,
            "total_transaction_amount_bdt": total_amount,
            "total_amount_display": f"৳{total_amount:,.2f}",
            "network_risk_indicators": [f"{i['pattern']}: {i['description']}" for i in insights],
            "insights": insights,
            "nodes": nodes,
            "edges": edges,
            "disclaimer": "Automated relationship mapping. Shows potential coordinated activity indicators; does not confirm criminality."
        }


network_service = NetworkService()
