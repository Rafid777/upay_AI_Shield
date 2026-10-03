"""
upay AI Shield - Analyst Case Management Service
Manages full fraud investigation case lifecycle: creation, triage, status updates,
event logging, and formal human analyst determinations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models import Case, CaseEvent, Transaction, AnalystFeedback
from backend.schemas import CaseCreate, CaseUpdate, CaseDecisionRequest


def utc_now():
    return datetime.now(timezone.utc)


class CaseManagementService:
    def create_case(
        self,
        db: Session,
        case_in: CaseCreate,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Case:
        # Check if case already exists for transaction
        existing = db.query(Case).filter(Case.transaction_id == case_in.transaction_id).first()
        if existing:
            return existing

        # Fetch transaction
        tx = db.query(Transaction).filter(Transaction.transaction_id == case_in.transaction_id).first()
        score = float(tx.demo_risk_score if tx and tx.demo_risk_score else 85.0)
        level = tx.risk_level if tx and tx.risk_level else "HIGH"
        cust_id = tx.customer_id if tx else "CUST_UNKNOWN"

        # Generate case_id: CASE-1001, CASE-1002...
        case_count = db.query(Case).count()
        case_id = f"CASE-{1001 + case_count}"

        new_case = Case(
            case_id=case_id,
            transaction_id=case_in.transaction_id,
            customer_id=cust_id,
            risk_score=score,
            risk_level=level,
            priority=case_in.priority or ("CRITICAL" if score >= 90 else "HIGH"),
            assigned_analyst=case_in.assigned_analyst or "lead_analyst",
            status="OPEN",
            evidence=evidence or {
                "amount": float(tx.amount) if tx else 0.0,
                "hour": int(tx.hour) if tx else 12,
                "amount_deviation": float(tx.amount_deviation) if tx else 1.0,
                "is_new_device": int(tx.is_new_device) if tx else 0,
                "location": tx.location if tx else "Dhaka"
            },
            analyst_notes=case_in.analyst_notes or "Case opened for formal human analyst investigation.",
            created_at=utc_now(),
            updated_at=utc_now()
        )
        db.add(new_case)
        db.flush()

        # Add initial CaseEvent
        initial_event = CaseEvent(
            case_id=case_id,
            event_type="CREATED",
            actor=case_in.assigned_analyst or "lead_analyst",
            details={"priority": new_case.priority, "status": "OPEN", "risk_score": score},
            created_at=utc_now()
        )
        db.add(initial_event)
        db.commit()
        db.refresh(new_case)
        return new_case

    def list_cases(
        self,
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        # Auto-seed initial benchmark cases if table is completely empty
        if db.query(Case).count() == 0:
            self._seed_initial_cases(db)

        query = db.query(Case)
        if status and status != "ALL":
            query = query.filter(Case.status == status)
        if priority and priority != "ALL":
            query = query.filter(Case.priority == priority)

        total = query.count()
        cases = query.order_by(Case.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        return {
            "total": total,
            "cases": cases
        }

    def get_case(self, db: Session, case_id: str) -> Optional[Case]:
        return db.query(Case).filter(Case.case_id == case_id).first()

    def update_case(
        self,
        db: Session,
        case_id: str,
        case_up: CaseUpdate,
        actor: str = "analyst"
    ) -> Optional[Case]:
        c = self.get_case(db, case_id)
        if not c:
            return None

        event_details = {}
        if case_up.status and case_up.status != c.status:
            event_details["old_status"] = c.status
            event_details["new_status"] = case_up.status
            c.status = case_up.status

        if case_up.priority and case_up.priority != c.priority:
            event_details["old_priority"] = c.priority
            event_details["new_priority"] = case_up.priority
            c.priority = case_up.priority

        if case_up.assigned_analyst:
            c.assigned_analyst = case_up.assigned_analyst

        if case_up.analyst_notes:
            c.analyst_notes = case_up.analyst_notes

        c.updated_at = utc_now()

        if event_details:
            ev = CaseEvent(
                case_id=case_id,
                event_type="STATUS_CHANGED",
                actor=actor,
                details=event_details,
                created_at=utc_now()
            )
            db.add(ev)

        db.commit()
        db.refresh(c)
        return c

    def record_decision(
        self,
        db: Session,
        case_id: str,
        decision_in: CaseDecisionRequest
    ) -> Optional[Case]:
        c = self.get_case(db, case_id)
        if not c:
            return None

        c.decision = decision_in.decision
        c.status = "RESOLVED"
        if decision_in.analyst_notes:
            c.analyst_notes = decision_in.analyst_notes
        c.updated_at = utc_now()

        # Log event
        ev = CaseEvent(
            case_id=case_id,
            event_type="DECISION_RECORDED",
            actor=decision_in.analyst_id or "lead_analyst",
            details={"decision": decision_in.decision, "notes": decision_in.analyst_notes},
            created_at=utc_now()
        )
        db.add(ev)

        # Sync to AnalystFeedback table for model feedback loop
        feedback_decision = "SUSPICIOUS" if decision_in.decision == "CONFIRM_SUSPICIOUS" else (
            "LEGITIMATE" if decision_in.decision == "MARK_LEGITIMATE" else "NEEDS_REVIEW"
        )
        fb = AnalystFeedback(
            transaction_id=c.transaction_id,
            predicted_risk=c.risk_score,
            predicted_level=c.risk_level,
            decision=feedback_decision,
            comment=decision_in.analyst_notes,
            reason=decision_in.analyst_notes,
            analyst_id=decision_in.analyst_id or "lead_analyst",
            created_at=utc_now()
        )
        db.add(fb)

        db.commit()
        db.refresh(c)
        return c

    def _seed_initial_cases(self, db: Session):
        """Seeds benchmark initial cases using high-risk transactions from the database."""
        high_txs = db.query(Transaction).filter(Transaction.risk_level == "HIGH").limit(4).all()
        priorities = ["CRITICAL", "HIGH", "HIGH", "MEDIUM"]
        statuses = ["OPEN", "UNDER_REVIEW", "OPEN", "NEEDS_MORE_INFORMATION"]

        for i, tx in enumerate(high_txs):
            cid = f"CASE-{1001 + i}"
            c = Case(
                case_id=cid,
                transaction_id=tx.transaction_id,
                customer_id=tx.customer_id,
                risk_score=float(tx.demo_risk_score or 90.0),
                risk_level=tx.risk_level or "HIGH",
                priority=priorities[i % len(priorities)],
                assigned_analyst="lead_fraud_analyst",
                status=statuses[i % len(statuses)],
                evidence={
                    "amount_bdt": float(tx.amount),
                    "amount_deviation": float(tx.amount_deviation),
                    "channel": tx.channel,
                    "location": tx.location,
                    "is_new_device": int(tx.is_new_device)
                },
                analyst_notes=f"Flagged for human triage due to {tx.amount_deviation:.1f}x amount surge and new device telemetry.",
                created_at=utc_now(),
                updated_at=utc_now()
            )
            db.add(c)
            ev = CaseEvent(
                case_id=cid,
                event_type="CREATED",
                actor="system_auto_triage",
                details={"priority": c.priority, "status": c.status},
                created_at=utc_now()
            )
            db.add(ev)
        db.commit()


case_service = CaseManagementService()
