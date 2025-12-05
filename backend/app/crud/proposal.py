from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalCreate, ProposalUpdate


def create_proposal(db: Session, proposal: ProposalCreate) -> Proposal:
    """Create a new proposal."""
    db_proposal = Proposal(**proposal.model_dump())
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


def get_proposal(db: Session, proposal_id: int) -> Optional[Proposal]:
    """Get a proposal by ID."""
    return db.query(Proposal).filter(Proposal.id == proposal_id).first()


def get_proposals(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    contact_id: Optional[int] = None,
    status: Optional[ProposalStatus] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> tuple[list[Proposal], int]:
    """
    Get proposals with optional filtering and pagination.
    Returns tuple of (proposals, total_count).
    """
    query = db.query(Proposal)
    
    # Filter by contact
    if contact_id:
        query = query.filter(Proposal.contact_id == contact_id)
    
    # Filter by status
    if status:
        query = query.filter(Proposal.status == status)
    
    # Filter by value range
    if min_value is not None:
        query = query.filter(Proposal.value >= min_value)
    if max_value is not None:
        query = query.filter(Proposal.value <= max_value)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering (most recent first)
    proposals = query.order_by(Proposal.created_at.desc()).offset(skip).limit(limit).all()
    
    return proposals, total


def get_proposals_by_contact(
    db: Session, contact_id: int, skip: int = 0, limit: int = 100
) -> list[Proposal]:
    """Get all proposals for a specific contact."""
    return (
        db.query(Proposal)
        .filter(Proposal.contact_id == contact_id)
        .order_by(Proposal.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_proposal(
    db: Session, proposal_id: int, proposal_update: ProposalUpdate
) -> Optional[Proposal]:
    """Update a proposal."""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        return None
    
    # Update only provided fields
    update_data = proposal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_proposal, field, value)
    
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


def delete_proposal(db: Session, proposal_id: int) -> bool:
    """Delete a proposal. Returns True if deleted, False if not found."""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        return False
    
    db.delete(db_proposal)
    db.commit()
    return True


def get_proposals_by_status(
    db: Session, status: ProposalStatus, skip: int = 0, limit: int = 100
) -> list[Proposal]:
    """Get proposals by status."""
    return (
        db.query(Proposal)
        .filter(Proposal.status == status)
        .order_by(Proposal.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_expired_proposals(db: Session, limit: int = 100) -> list[Proposal]:
    """Get proposals that have expired but are not closed."""
    now = datetime.now(timezone.utc)
    return (
        db.query(Proposal)
        .filter(
            Proposal.expires_at < now,
            Proposal.status.in_([ProposalStatus.draft, ProposalStatus.submitted])
        )
        .order_by(Proposal.expires_at.desc())
        .limit(limit)
        .all()
    )


def count_proposals_by_status(db: Session, contact_id: Optional[int] = None) -> dict[ProposalStatus, int]:
    """Get count of proposals grouped by status, optionally filtered by contact."""
    query = db.query(Proposal.status, func.count(Proposal.id))
    
    if contact_id:
        query = query.filter(Proposal.contact_id == contact_id)
    
    results = query.group_by(Proposal.status).all()
    return {status: count for status, count in results}


def get_total_value_by_status(db: Session, contact_id: Optional[int] = None) -> dict[ProposalStatus, float]:
    """Get total value of proposals grouped by status, optionally filtered by contact."""
    query = db.query(Proposal.status, func.sum(Proposal.value))
    
    if contact_id:
        query = query.filter(Proposal.contact_id == contact_id)
    
    results = query.group_by(Proposal.status).all()
    return {status: float(total) if total else 0.0 for status, total in results}