from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.proposal import (
    ProposalCreate,
    ProposalUpdate,
    ProposalResponse,
    ProposalListResponse,
)
from app.models.proposal import ProposalStatus
from app.crud import proposal as proposal_crud
from app.crud import contact as contact_crud


router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("/expired", response_model=list[ProposalResponse])
def get_expired_proposals(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get proposals that have expired but are not closed."""
    return proposal_crud.get_expired_proposals(db, limit)


@router.get("/stats/by-status")
def get_proposal_stats(
    contact_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get proposal statistics grouped by status, optionally filtered by contact."""
    if contact_id:
        # Verify contact exists
        contact = contact_crud.get_contact(db, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
    
    counts = proposal_crud.count_proposals_by_status(db, contact_id)
    totals = proposal_crud.get_total_value_by_status(db, contact_id)
    
    return {
        "total_count": sum(counts.values()),
        "total_value": sum(totals.values()),
        "by_status": {
            status.value: {
                "count": counts.get(status, 0),
                "total_value": totals.get(status, 0.0)
            }
            for status in ProposalStatus
        }
    }


@router.post("/", response_model=ProposalResponse, status_code=201)
def create_proposal(proposal: ProposalCreate, db: Session = Depends(get_db)):
    """Create a new proposal."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, proposal.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return proposal_crud.create_proposal(db, proposal)


@router.get("/", response_model=ProposalListResponse)
def list_proposals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    contact_id: Optional[int] = None,
    status: Optional[ProposalStatus] = None,
    min_value: Optional[float] = Query(None, ge=0),
    max_value: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """
    List proposals with optional filtering and pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **contact_id**: Filter by contact ID
    - **status**: Filter by proposal status
    - **min_value**: Filter by minimum value
    - **max_value**: Filter by maximum value
    """
    proposals, total = proposal_crud.get_proposals(
        db,
        skip=skip,
        limit=limit,
        contact_id=contact_id,
        status=status,
        min_value=min_value,
        max_value=max_value,
    )
    
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return ProposalListResponse(
        items=proposals,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Get a specific proposal by ID."""
    proposal = proposal_crud.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.put("/{proposal_id}", response_model=ProposalResponse)
def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    db: Session = Depends(get_db)
):
    """Update a proposal."""
    updated = proposal_crud.update_proposal(db, proposal_id, proposal_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return updated


@router.delete("/{proposal_id}", status_code=204)
def delete_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Delete a proposal."""
    success = proposal_crud.delete_proposal(db, proposal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proposal not found")


@router.get("/contact/{contact_id}", response_model=list[ProposalResponse])
def get_contact_proposals(
    contact_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all proposals for a specific contact."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return proposal_crud.get_proposals_by_contact(db, contact_id, skip, limit)