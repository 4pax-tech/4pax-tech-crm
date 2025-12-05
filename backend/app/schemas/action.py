from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.action import ActionStatus, ActionPriority, ActionType


class ActionBase(BaseModel):
    """Base schema with common fields for create/update."""

    contact_id: int
    proposal_id: Optional[int] = None
    interaction_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: ActionStatus = ActionStatus.pending
    priority: ActionPriority = ActionPriority.medium
    action_type: ActionType = ActionType.other
    due_at: Optional[datetime] = None
    assigned_to: Optional[int] = None


class ActionCreate(ActionBase):
    """Schema for creating an action."""

    pass


class ActionUpdate(BaseModel):
    """Schema for updating an action. All fields optional."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ActionStatus] = None
    priority: Optional[ActionPriority] = None
    action_type: Optional[ActionType] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    proposal_id: Optional[int] = None
    interaction_id: Optional[int] = None


class ActionResponse(ActionBase):
    """Schema for action responses."""

    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionListResponse(BaseModel):
    """Schema for paginated action list."""

    items: list[ActionResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
