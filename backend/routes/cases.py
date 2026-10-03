"""
upay AI Shield - Analyst Case Management Routes
Endpoints for creating, listing, triaging cases, and recording formal human analyst decisions.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    CaseCreate,
    CaseUpdate,
    CaseDecisionRequest,
    CaseResponse,
    CaseListResponse
)
from backend.services.case_service import case_service

router = APIRouter(prefix="/cases", tags=["Case Management"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db)
):
    """
    Opens an analyst investigation case for a flagged transaction.
    """
    case = case_service.create_case(db=db, case_in=payload)
    return case


@router.get("", response_model=CaseListResponse)
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lists analyst cases with filtering by status and priority.
    """
    res = case_service.list_cases(
        db=db,
        status=status_filter,
        priority=priority_filter,
        page=page,
        limit=limit
    )
    return res


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full case details including audit trail events.
    """
    case = case_service.get_case(db=db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found."
        )
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    payload: CaseUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates case status, priority, or analyst notes.
    """
    case = case_service.update_case(db=db, case_id=case_id, case_up=payload)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found."
        )
    return case


@router.post("/{case_id}/decision", response_model=CaseResponse)
def record_case_decision(
    case_id: str,
    payload: CaseDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Records a formal human analyst decision on a case (CONFIRM_SUSPICIOUS, MARK_LEGITIMATE, NEEDS_MORE_INVESTIGATION)
    and syncs to feedback loop.
    """
    case = case_service.record_decision(db=db, case_id=case_id, decision_in=payload)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found."
        )
    return case
