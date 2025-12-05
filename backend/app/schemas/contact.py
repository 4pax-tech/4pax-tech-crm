from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.contact import ContactStatus


class ContactBase(BaseModel):
    """Base schema with common fields for create/update."""
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=64)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    status: ContactStatus = ContactStatus.lead
    source: Optional[str] = Field(None, max_length=100)
    owner_id: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    next_action: Optional[datetime] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact. All fields optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=64)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    status: Optional[ContactStatus] = None
    source: Optional[str] = Field(None, max_length=100)
    owner_id: Optional[int] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    next_action: Optional[datetime] = None


class ContactResponse(ContactBase):
    """Schema for contact responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    """Schema for paginated contact list."""
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(from_attributes=True)