"""
upay AI Shield - Transactions API Route
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from backend.database import get_db
from backend.models import Transaction
from backend.schemas import TransactionResponse, TransactionListResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH"),
    search: Optional[str] = Query(None, description="Search by transaction_id, customer_id, receiver_id"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount"),
    db: Session = Depends(get_db)
):
    """Retrieves paginated transactions with optional risk, search, and amount filtering."""
    query = db.query(Transaction)

    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper())

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.transaction_id.ilike(s),
                Transaction.customer_id.ilike(s),
                Transaction.receiver_id.ilike(s),
                Transaction.location.ilike(s)
            )
        )

    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(Transaction.amount_deviation), desc(Transaction.amount)).offset(offset).limit(limit).all()

    return TransactionListResponse(
        total=total,
        page=page,
        limit=limit,
        transactions=[TransactionResponse.model_validate(r) for r in results]
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves detailed record for a specific transaction."""
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    return TransactionResponse.model_validate(tx)
