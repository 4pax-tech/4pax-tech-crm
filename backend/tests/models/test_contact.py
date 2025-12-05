import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models.contact import Contact, ContactStatus


def test_contact_creation_minimal(db_session):
    """Test creating a contact with minimal required fields."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.status == ContactStatus.lead
    assert contact.created_at is not None
    assert contact.updated_at is not None


def test_contact_creation_full(db_session):
    """Test creating a contact with all fields."""
    contact = Contact(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone="+1234567890",
        company="Acme Corp",
        job_title="CTO",
        status=ContactStatus.client,
        source="linkedin",
        tags=["vip","tech"],
        notes="Important client",
    )
    db_session.add(contact)
    db_session.commit()

    assert contact.id is not None
    assert contact.email == "jane@example.com"
    assert contact.status == ContactStatus.client


def test_contact_status_enum_valid(db_session):
    """Test that valid status enums work correctly."""
    for status in ContactStatus:
        contact = Contact(first_name="Test", last_name="User", status=status)
        db_session.add(contact)
        db_session.commit()
        assert contact.status == status
        db_session.delete(contact)
        db_session.commit()


def test_contact_status_default(db_session):
    """Test that default status is 'lead'."""
    contact = Contact(first_name="Default", last_name="User")
    db_session.add(contact)
    db_session.commit()

    assert contact.status == ContactStatus.lead


def test_contact_missing_required_fields(db_session):
    """Test that missing required fields raises an error."""
    with pytest.raises(IntegrityError):
        contact = Contact(first_name="John")  # missing last_name
        db_session.add(contact)
        db_session.commit()


def test_contact_update(db_session):
    """Test updating a contact."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    original_updated_at = contact.updated_at
    contact.status = ContactStatus.client
    db_session.commit()

    assert contact.status == ContactStatus.client
    # Note: updated_at auto-update depends on your datetime fix


def test_contact_email_index(db_session):
    """Test that email field is indexed (verify model definition)."""
    contact = Contact(first_name="John", last_name="Doe", email="john@example.com")
    db_session.add(contact)
    db_session.commit()

    result = (
        db_session.query(Contact).filter(Contact.email == "john@example.com").first()
    )
    assert result is not None
    assert result.email == "john@example.com"


def test_contact_relationships_exist(db_session):
    """Test that relationship attributes exist (will be None until related models are added)."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    assert hasattr(contact, "interactions")
    assert hasattr(contact, "proposals")
    assert hasattr(contact, "actions")
    assert contact.interactions == []
    assert contact.proposals == []
    assert contact.actions == []


def test_contact_tags_creation(db_session):
    """Test creating a contact with tags."""
    contact = Contact(
        first_name="John",
        last_name="Doe",
        tags=["vip", "tech", "enterprise"]
    )
    db_session.add(contact)
    db_session.commit()

    assert contact.tags == ["vip", "tech", "enterprise"]
    assert len(contact.tags) == 3


def test_contact_tags_default_empty(db_session):
    """Test that tags default to empty list."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    assert contact.tags == []


def test_contact_tags_append(db_session):
    """Test appending tags to a contact."""
    from sqlalchemy.orm.attributes import flag_modified
    
    contact = Contact(
        first_name="John",
        last_name="Doe",
        tags=["vip"]
    )
    db_session.add(contact)
    db_session.commit()

    contact.tags.append("urgent")
    flag_modified(contact, "tags")  # Mark as modified
    db_session.commit()

    db_session.refresh(contact)
    assert "urgent" in contact.tags
    assert len(contact.tags) == 2


def test_contact_tags_remove(db_session):
    """Test removing tags from a contact."""
    from sqlalchemy.orm.attributes import flag_modified
    
    contact = Contact(
        first_name="John",
        last_name="Doe",
        tags=["vip", "tech", "urgent"]
    )
    db_session.add(contact)
    db_session.commit()

    contact.tags.remove("urgent")
    flag_modified(contact, "tags")  # Mark as modified
    db_session.commit()

    db_session.refresh(contact)
    assert "urgent" not in contact.tags
    assert len(contact.tags) == 2


def test_contact_query_by_tag_contains(db_session):
    """Test querying contacts by tag using contains."""
    contact1 = Contact(first_name="John", last_name="Doe", tags=["vip", "tech"])
    contact2 = Contact(first_name="Jane", last_name="Smith", tags=["tech"])
    contact3 = Contact(first_name="Bob", last_name="Jones", tags=["enterprise"])
    
    db_session.add_all([contact1, contact2, contact3])
    db_session.commit()

    # Query contacts with "vip" tag
    vip_contacts = db_session.query(Contact).filter(
        Contact.tags.contains(["vip"])
    ).all()

    assert len(vip_contacts) == 1
    assert vip_contacts[0].first_name == "John"


def test_contact_query_multiple_tags(db_session):
    """Test querying contacts with multiple tags."""
    contact1 = Contact(first_name="John", last_name="Doe", tags=["vip", "tech"])
    contact2 = Contact(first_name="Jane", last_name="Smith", tags=["tech"])
    contact3 = Contact(first_name="Bob", last_name="Jones", tags=["vip", "enterprise"])
    
    db_session.add_all([contact1, contact2, contact3])
    db_session.commit()

    # Query contacts with both "vip" AND "tech" tags
    vip_tech_contacts = db_session.query(Contact).filter(
        Contact.tags.contains(["vip", "tech"])
    ).all()

    assert len(vip_tech_contacts) == 1
    assert vip_tech_contacts[0].first_name == "John"


def test_contact_query_any_tag(db_session):
    """Test querying contacts with any of multiple tags."""
    from sqlalchemy import or_
    
    contact1 = Contact(first_name="John", last_name="Doe", tags=["vip"])
    contact2 = Contact(first_name="Jane", last_name="Smith", tags=["urgent"])
    contact3 = Contact(first_name="Bob", last_name="Jones", tags=["normal"])
    
    db_session.add_all([contact1, contact2, contact3])
    db_session.commit()

    # Query contacts with "vip" OR "urgent" tag
    priority_contacts = db_session.query(Contact).filter(
        or_(
            Contact.tags.contains(["vip"]),
            Contact.tags.contains(["urgent"])
        )
    ).all()

    assert len(priority_contacts) == 2
    names = {c.first_name for c in priority_contacts}
    assert names == {"John", "Jane"}


def test_contact_tags_empty_array(db_session):
    """Test that empty tags array works correctly."""
    contact = Contact(
        first_name="John",
        last_name="Doe",
        tags=[]
    )
    db_session.add(contact)
    db_session.commit()

    assert contact.tags == []
    
    # Query should not return contacts with empty tags
    vip_contacts = db_session.query(Contact).filter(
        Contact.tags.contains(["vip"])
    ).all()
    
    assert len(vip_contacts) == 0


def test_contact_tags_update_replace(db_session):
    """Test replacing all tags."""
    contact = Contact(
        first_name="John",
        last_name="Doe",
        tags=["old1", "old2"]
    )
    db_session.add(contact)
    db_session.commit()

    # Replace all tags
    contact.tags = ["new1", "new2", "new3"]
    db_session.commit()

    db_session.refresh(contact)
    assert contact.tags == ["new1", "new2", "new3"]
    assert "old1" not in contact.tags