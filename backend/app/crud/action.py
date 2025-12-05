from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.models.action import Action, ActionStatus, ActionPriority, ActionType
from app.schemas.action import ActionCreate, ActionUpdate


def create_action(db: Session, action: ActionCreate) -> Action:
    """Create a new action."""
    db_action = Action(**action.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


def get_action(db: Session, action_id: int) -> Optional[Action]:
    """Get an action by ID."""
    return db.query(Action).filter(Action.id == action_id).first()


def get_actions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    contact_id: Optional[int] = None,
    status: Optional[ActionStatus] = None,
    priority: Optional[ActionPriority] = None,
    action_type: Optional[ActionType] = None,
    assigned_to: Optional[int] = None,
    overdue_only: bool = False,
) -> tuple[list[Action], int]:
    """
    Get actions with optional filtering and pagination.
    Returns tuple of (actions, total_count).
    """
    query = db.query(Action)

    # Filter by contact
    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    # Filter by status
    if status:
        query = query.filter(Action.status == status)

    # Filter by priority
    if priority:
        query = query.filter(Action.priority == priority)

    # Filter by action type
    if action_type:
        query = query.filter(Action.action_type == action_type)

    # Filter by assigned user
    if assigned_to:
        query = query.filter(Action.assigned_to == assigned_to)

    # Filter overdue actions
    if overdue_only:
        now = datetime.now(timezone.utc)
        query = query.filter(Action.status == ActionStatus.pending, Action.due_at < now)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering (most urgent first, then by due date)
    actions = (
        query.order_by(Action.priority.desc(), Action.due_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return actions, total


def get_actions_by_contact(
    db: Session, contact_id: int, skip: int = 0, limit: int = 100
) -> list[Action]:
    """Get all actions for a specific contact."""
    return (
        db.query(Action)
        .filter(Action.contact_id == contact_id)
        .order_by(Action.priority.desc(), Action.due_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_action(
    db: Session, action_id: int, action_update: ActionUpdate
) -> Optional[Action]:
    """Update an action."""
    db_action = get_action(db, action_id)
    if not db_action:
        return None

    # Update only provided fields
    update_data = action_update.model_dump(exclude_unset=True)

    # If status is being changed to completed, set completed_at
    if "status" in update_data and update_data["status"] == ActionStatus.completed:
        if not db_action.completed_at:
            update_data["completed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(db_action, field, value)

    db.commit()
    db.refresh(db_action)
    return db_action


def delete_action(db: Session, action_id: int) -> bool:
    """Delete an action. Returns True if deleted, False if not found."""
    db_action = get_action(db, action_id)
    if not db_action:
        return False

    db.delete(db_action)
    db.commit()
    return True


def get_pending_actions(
    db: Session, contact_id: Optional[int] = None, limit: int = 100
) -> list[Action]:
    """Get pending actions, optionally filtered by contact."""
    query = db.query(Action).filter(Action.status == ActionStatus.pending)

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    return (
        query.order_by(Action.priority.desc(), Action.due_at.asc()).limit(limit).all()
    )


def get_overdue_actions(
    db: Session, contact_id: Optional[int] = None, limit: int = 100
) -> list[Action]:
    """Get overdue pending actions."""
    now = datetime.now(timezone.utc)
    query = db.query(Action).filter(
        Action.status == ActionStatus.pending, Action.due_at < now
    )

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    return (
        query.order_by(Action.priority.desc(), Action.due_at.asc()).limit(limit).all()
    )


def get_upcoming_actions(
    db: Session, days: int = 7, contact_id: Optional[int] = None, limit: int = 100
) -> list[Action]:
    """Get pending actions due within the next N days."""
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)

    query = db.query(Action).filter(
        Action.status == ActionStatus.pending,
        Action.due_at >= now,
        Action.due_at <= future_date,
    )

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    return (
        query.order_by(Action.priority.desc(), Action.due_at.asc()).limit(limit).all()
    )


def count_actions_by_status(
    db: Session, contact_id: Optional[int] = None
) -> dict[ActionStatus, int]:
    """Get count of actions grouped by status, optionally filtered by contact."""
    query = db.query(Action.status, func.count(Action.id))

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    results = query.group_by(Action.status).all()
    return {status: count for status, count in results}


def count_actions_by_type(
    db: Session, contact_id: Optional[int] = None
) -> dict[ActionStatus, int]:
    """Get count of actions grouped by status, optionally filtered by contact."""
    query = db.query(Action.status, func.count(Action.id))

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    results = query.group_by(Action.action_type).all()
    return {action_type: count for action_type, count in results}


def count_actions_by_priority(
    db: Session, contact_id: Optional[int] = None
) -> dict[ActionPriority, int]:
    """Get count of pending actions grouped by priority."""
    query = db.query(Action.priority, func.count(Action.id)).filter(
        Action.status == ActionStatus.pending
    )

    if contact_id:
        query = query.filter(Action.contact_id == contact_id)

    results = query.group_by(Action.priority).all()
    return {priority: count for priority, count in results}
