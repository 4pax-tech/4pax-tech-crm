from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
)
from app.models.contact import ContactStatus
from app.crud import contact as contact_crud


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact."""
    # Check if email already exists
    if contact.email:
        existing = contact_crud.get_contact_by_email(db, contact.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    return contact_crud.create_contact(db, contact)


@router.get("/", response_model=ContactListResponse)
def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ContactStatus] = None,
    search: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: Session = Depends(get_db),
):
    """
    List contacts with optional filtering and pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by contact status
    - **search**: Search in name, email, company
    - **tags**: Filter by tags (comma-separated, must have all)
    """
    # Parse tags if provided
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    contacts, total = contact_crud.get_contacts(
        db, skip=skip, limit=limit, status=status, search=search, tags=tags_list
    )
    
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return ContactListResponse(
        items=contacts,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a specific contact by ID."""
    contact = contact_crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    db: Session = Depends(get_db)
):
    """Update a contact."""
    # Check if email is being changed and already exists
    if contact_update.email:
        existing = contact_crud.get_contact_by_email(db, contact_update.email)
        if existing and existing.id != contact_id:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    updated = contact_crud.update_contact(db, contact_id, contact_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact."""
    success = contact_crud.delete_contact(db, contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.get("/search/{search_term}", response_model=list[ContactResponse])
def search_contacts(
    search_term: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search contacts by name, email, or company."""
    return contact_crud.search_contacts(db, search_term, limit)


@router.get("/stats/by-status")
def get_contact_stats(db: Session = Depends(get_db)):
    """Get contact statistics grouped by status."""
    counts = contact_crud.count_contacts_by_status(db)
    return {
        "total": sum(counts.values()),
        "by_status": {status.value: count for status, count in counts.items()}
    }