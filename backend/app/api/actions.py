from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.schemas.action import (
    ActionCreate,
    ActionUpdate,
    ActionResponse,
    ActionListResponse,
)
from app.models.action import ActionType
from app.crud import action as action_crud
from app.crud import contact as contact_crud


router = APIRouter(prefix="/actions", tags=["actions"])


"""
create_action
get_action
get_actions
get_actions_by_contact
update_action
delete_action
get_pending_actions
get_overdue_actions
get_upcoming_actions
count_actions_by_status
count_actions_by_priority
"""


@router.get("/recent", response_model=list[ActionResponse])
def get_recent_actions(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent actions within the last N days."""
    return action_crud.get_recent_actions(db, days, limit)


@router.get("/stats/by-type")
def get_action_stats(contact_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get action statistics grouped by type, optionally filtered by contact."""
    if contact_id:
        # Verify contact exists
        contact = contact_crud.get_contact(db, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

    counts = action_crud.count_actions_by_type(db, contact_id)
    return {
        "total": sum(counts.values()),
        "by_type": {action_type.value: count for action_type, count in counts.items()},
    }


@router.post("/", response_model=ActionResponse, status_code=201)
def create_action(action: ActionCreate, db: Session = Depends(get_db)):
    """Create a new action."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, action.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return action_crud.create_action(db, action)


@router.get("/", response_model=ActionListResponse)
def list_actions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    contact_id: Optional[int] = None,
    action_type: Optional[ActionType] = None,
    start_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    db: Session = Depends(get_db),
):
    """
    List actions with optional filtering and pagination.

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **contact_id**: Filter by contact ID
    - **action_type**: Filter by action type
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

    actions, total = action_crud.get_actions(
        db,
        skip=skip,
        limit=limit,
        contact_id=contact_id,
        action_type=action_type,
        start_date=start_datetime,
        end_date=end_datetime,
    )

    page = (skip // limit) + 1 if limit > 0 else 1

    return ActionListResponse(items=actions, total=total, page=page, page_size=limit)


@router.get("/{action_id}", response_model=ActionResponse)
def get_action(action_id: int, db: Session = Depends(get_db)):
    """Get a specific action by ID."""
    action = action_crud.get_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.put("/{action_id}", response_model=ActionResponse)
def update_action(
    action_id: int,
    action_update: ActionUpdate,
    db: Session = Depends(get_db),
):
    """Update an action."""
    updated = action_crud.update_action(db, action_id, action_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Action not found")
    return updated


@router.delete("/{action_id}", status_code=204)
def delete_action(action_id: int, db: Session = Depends(get_db)):
    """Delete an action."""
    success = action_crud.delete_action(db, action_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action not found")


@router.get("/contact/{contact_id}", response_model=list[ActionResponse])
def get_contact_actions(
    contact_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all actions for a specific contact."""
    # Verify contact exists
    contact = contact_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return action_crud.get_actions_by_contact(db, contact_id, skip, limit)
