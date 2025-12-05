from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime, timedelta
from app.models.interaction import Interaction, InteractionType
from app.schemas.interaction import InteractionCreate, InteractionUpdate


def create_interaction(db: Session, interaction: InteractionCreate) -> Interaction:
    """Create a new interaction."""
    db_interaction = Interaction(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    """Get an interaction by ID."""
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def get_interactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    contact_id: Optional[int] = None,
    interaction_type: Optional[InteractionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> tuple[list[Interaction], int]:
    """
    Get interactions with optional filtering and pagination.
    Returns tuple of (interactions, total_count).
    """
    query = db.query(Interaction)
    
    # Filter by contact
    if contact_id:
        query = query.filter(Interaction.contact_id == contact_id)
    
    # Filter by type
    if interaction_type:
        query = query.filter(Interaction.type == interaction_type)
    
    # Filter by date range
    if start_date:
        query = query.filter(Interaction.occurred_at >= start_date)
    if end_date:
        query = query.filter(Interaction.occurred_at <= end_date)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering (most recent first)
    interactions = query.order_by(Interaction.occurred_at.desc()).offset(skip).limit(limit).all()
    
    return interactions, total


def get_interactions_by_contact(
    db: Session, contact_id: int, skip: int = 0, limit: int = 100
) -> list[Interaction]:
    """Get all interactions for a specific contact."""
    return (
        db.query(Interaction)
        .filter(Interaction.contact_id == contact_id)
        .order_by(Interaction.occurred_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_interaction(
    db: Session, interaction_id: int, interaction_update: InteractionUpdate
) -> Optional[Interaction]:
    """Update an interaction."""
    db_interaction = get_interaction(db, interaction_id)
    if not db_interaction:
        return None
    
    # Update only provided fields
    update_data = interaction_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_interaction, field, value)
    
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def delete_interaction(db: Session, interaction_id: int) -> bool:
    """Delete an interaction. Returns True if deleted, False if not found."""
    db_interaction = get_interaction(db, interaction_id)
    if not db_interaction:
        return False
    
    db.delete(db_interaction)
    db.commit()
    return True


def get_recent_interactions(
    db: Session, days: int = 7, limit: int = 50
) -> list[Interaction]:
    """Get recent interactions within the last N days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    return (
        db.query(Interaction)
        .filter(Interaction.occurred_at >= cutoff_date)
        .order_by(Interaction.occurred_at.desc())
        .limit(limit)
        .all()
    )


def count_interactions_by_type(db: Session, contact_id: Optional[int] = None) -> dict[InteractionType, int]:
    """Get count of interactions grouped by type, optionally filtered by contact."""
    query = db.query(Interaction.type, func.count(Interaction.id))
    
    if contact_id:
        query = query.filter(Interaction.contact_id == contact_id)
    
    results = query.group_by(Interaction.type).all()
    return {interaction_type: count for interaction_type, count in results}