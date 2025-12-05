from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from app.models.contact import Contact, ContactStatus
from app.schemas.contact import ContactCreate, ContactUpdate


def create_contact(db: Session, contact: ContactCreate) -> Contact:
    """Create a new contact."""
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_contact(db: Session, contact_id: int) -> Optional[Contact]:
    """Get a contact by ID."""
    return db.query(Contact).filter(Contact.id == contact_id).first()


def get_contact_by_email(db: Session, email: str) -> Optional[Contact]:
    """Get a contact by email."""
    return db.query(Contact).filter(Contact.email == email).first()


def get_contacts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ContactStatus] = None,
    search: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> tuple[list[Contact], int]:
    """
    Get contacts with optional filtering and pagination.
    Returns tuple of (contacts, total_count).
    """
    query = db.query(Contact)
    
    # Filter by status
    if status:
        query = query.filter(Contact.status == status)
    
    # Search in name, email, company
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Contact.first_name.ilike(search_pattern)) |
            (Contact.last_name.ilike(search_pattern)) |
            (Contact.email.ilike(search_pattern)) |
            (Contact.company.ilike(search_pattern))
        )
    
    # Filter by tags (contact must have all specified tags)
    if tags:
        query = query.filter(Contact.tags.contains(tags))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    contacts = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
    
    return contacts, total


def update_contact(
    db: Session, contact_id: int, contact_update: ContactUpdate
) -> Optional[Contact]:
    """Update a contact."""
    db_contact = get_contact(db, contact_id)
    if not db_contact:
        return None
    
    # Update only provided fields
    update_data = contact_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contact, field, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int) -> bool:
    """Delete a contact. Returns True if deleted, False if not found."""
    db_contact = get_contact(db, contact_id)
    if not db_contact:
        return False
    
    db.delete(db_contact)
    db.commit()
    return True


def get_contacts_by_status(
    db: Session, status: ContactStatus, skip: int = 0, limit: int = 100
) -> list[Contact]:
    """Get contacts by status."""
    return (
        db.query(Contact)
        .filter(Contact.status == status)
        .order_by(Contact.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def search_contacts(db: Session, search_term: str, limit: int = 50) -> list[Contact]:
    """Search contacts by name, email, or company."""
    search_pattern = f"%{search_term}%"
    return (
        db.query(Contact)
        .filter(
            (Contact.first_name.ilike(search_pattern)) |
            (Contact.last_name.ilike(search_pattern)) |
            (Contact.email.ilike(search_pattern)) |
            (Contact.company.ilike(search_pattern))
        )
        .order_by(Contact.updated_at.desc())
        .limit(limit)
        .all()
    )


def count_contacts_by_status(db: Session) -> dict[ContactStatus, int]:
    """Get count of contacts grouped by status."""
    results = (
        db.query(Contact.status, func.count(Contact.id))
        .group_by(Contact.status)
        .all()
    )
    return {status: count for status, count in results}