from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.proposal import ProposalStatus


class ProposalBase(BaseModel):
    """Base schema with common fields for create/update."""
    contact_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: ProposalStatus = ProposalStatus.draft
    applied_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ProposalCreate(ProposalBase):
    """Schema for creating a proposal."""
    pass


class ProposalUpdate(BaseModel):
    """Schema for updating a proposal. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: Optional[ProposalStatus] = None
    applied_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ProposalResponse(ProposalBase):
    """Schema for proposal responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProposalListResponse(BaseModel):
    """Schema for paginated proposal list."""
    items: list[ProposalResponse]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(from_attributes=True)