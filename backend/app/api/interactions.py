from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.schemas.interaction import (
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    InteractionListResponse,
)
from app.models.interaction import InteractionType
from app.crud import interaction as interaction_crud
from app.crud import contact as contact_crud


router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/recent", response_model=list[InteractionResponse])
def get_recent_interactions(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent interactions within the last N days."""
    return interaction_crud.get_recent_interactions(db, days, limit)


@router.get("/stats/by-type")
def get_interaction_stats(
    contact_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """Get interaction statistics grouped by type, optionally filtered by contact."""
    if contact_id:
        # Verify contact exists
        contact = contact_crud.get_contact(db, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

    counts = interaction_crud.count_interactions_by_type(db, contact_id)
    return {
        "total": sum(counts.values()),
        "by_type": {
            interaction_type.value: count for interaction_type, count in counts.items()
        },
    }


@router.post("/", response_model=InteractionResponse, status_code=201)
def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    """Create a new interaction."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, interaction.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return interaction_crud.create_interaction(db, interaction)


@router.get("/", response_model=InteractionListResponse)
def list_interactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    contact_id: Optional[int] = None,
    interaction_type: Optional[InteractionType] = None,
    start_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    db: Session = Depends(get_db),
):
    """
    List interactions with optional filtering and pagination.

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **contact_id**: Filter by contact ID
    - **interaction_type**: Filter by interaction type
    - **start_date**: Filter by start date (ISO format)
    - **end_date**: Filter by end date (ISO format)
    """
    # Parse date strings if provided
    start_datetime = None
    end_datetime = None

    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            ) from exc

    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            ) from exc

    interactions, total = interaction_crud.get_interactions(
        db,
        skip=skip,
        limit=limit,
        contact_id=contact_id,
        interaction_type=interaction_type,
        start_date=start_datetime,
        end_date=end_datetime,
    )

    page = (skip // limit) + 1 if limit > 0 else 1

    return InteractionListResponse(
        items=interactions, total=total, page=page, page_size=limit
    )


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    """Get a specific interaction by ID."""
    interaction = interaction_crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.put("/{interaction_id}", response_model=InteractionResponse)
def update_interaction(
    interaction_id: int,
    interaction_update: InteractionUpdate,
    db: Session = Depends(get_db),
):
    """Update an interaction."""
    updated = interaction_crud.update_interaction(
        db, interaction_id, interaction_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return updated


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    """Delete an interaction."""
    success = interaction_crud.delete_interaction(db, interaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Interaction not found")


@router.get("/contact/{contact_id}", response_model=list[InteractionResponse])
def get_contact_interactions(
    contact_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all interactions for a specific contact."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return interaction_crud.get_interactions_by_contact(db, contact_id, skip, limit)
