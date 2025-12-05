from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.interaction import InteractionType


class InteractionBase(BaseModel):
    """Base schema with common fields for create/update."""
    contact_id: int
    type: InteractionType = InteractionType.note
    occurred_at: datetime
    summary: str = Field(..., min_length=1)
    outcome: Optional[str] = Field(None, max_length=255)
    created_by: Optional[str] = Field(None, max_length=120)


class InteractionCreate(InteractionBase):
    """Schema for creating an interaction."""
    pass


class InteractionUpdate(BaseModel):
    """Schema for updating an interaction. All fields optional except contact_id."""
    type: Optional[InteractionType] = None
    occurred_at: Optional[datetime] = None
    summary: Optional[str] = Field(None, min_length=1)
    outcome: Optional[str] = Field(None, max_length=255)
    created_by: Optional[str] = Field(None, max_length=120)


class InteractionResponse(InteractionBase):
    """Schema for interaction responses."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InteractionListResponse(BaseModel):
    """Schema for paginated interaction list."""
    items: list[InteractionResponse]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(from_attributes=True)