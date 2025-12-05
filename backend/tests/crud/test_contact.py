import pytest
from app.crud import contact as contact_crud
from app.schemas.contact import ContactCreate, ContactUpdate
from app.models.contact import ContactStatus


def test_create_contact(db_session):
    """Test creating a contact."""
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1234567890",
        company="Acme Corp",
        tags=["vip", "tech"]
    )
    
    contact = contact_crud.create_contact(db_session, contact_data)
    
    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.email == "john@example.com"
    assert contact.status == ContactStatus.lead
    assert contact.tags == ["vip", "tech"]


def test_get_contact(db_session):
    """Test getting a contact by ID."""
    contact_data = ContactCreate(first_name="Jane", last_name="Smith")
    created = contact_crud.create_contact(db_session, contact_data)
    
    fetched = contact_crud.get_contact(db_session, created.id)
    
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.first_name == "Jane"


def test_get_contact_not_found(db_session):
    """Test getting a non-existent contact."""
    contact = contact_crud.get_contact(db_session, 99999)
    assert contact is None


def test_get_contact_by_email(db_session):
    """Test getting a contact by email."""
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="unique@example.com"
    )
    created = contact_crud.create_contact(db_session, contact_data)
    
    fetched = contact_crud.get_contact_by_email(db_session, "unique@example.com")
    
    assert fetched is not None
    assert fetched.id == created.id


def test_get_contacts_pagination(db_session):
    """Test getting contacts with pagination."""
    # Create 5 contacts
    for i in range(5):
        contact_data = ContactCreate(
            first_name=f"User{i}",
            last_name="Test"
        )
        contact_crud.create_contact(db_session, contact_data)
    
    # Get first page
    contacts, total = contact_crud.get_contacts(db_session, skip=0, limit=3)
    assert len(contacts) == 3
    assert total == 5
    
    # Get second page
    contacts, total = contact_crud.get_contacts(db_session, skip=3, limit=3)
    assert len(contacts) == 2
    assert total == 5


def test_get_contacts_filter_by_status(db_session):
    """Test filtering contacts by status."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Lead", last_name="User", status=ContactStatus.lead)
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Client", last_name="User", status=ContactStatus.client)
    )
    
    leads, total = contact_crud.get_contacts(db_session, status=ContactStatus.lead)
    
    assert total == 1
    assert leads[0].first_name == "Lead"


def test_get_contacts_search(db_session):
    """Test searching contacts."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Alice", last_name="Johnson", email="alice@example.com")
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Bob", last_name="Smith", company="Alice Corp")
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Charlie", last_name="Brown")
    )
    
    # Search by first name
    results, total = contact_crud.get_contacts(db_session, search="alice")
    assert total == 2  # Alice and Bob (Alice Corp)
    
    # Search by email
    results, total = contact_crud.get_contacts(db_session, search="alice@example")
    assert total == 1
    assert results[0].first_name == "Alice"


def test_get_contacts_filter_by_tags(db_session):
    """Test filtering contacts by tags."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="VIP", last_name="User", tags=["vip", "tech"])
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Tech", last_name="User", tags=["tech"])
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Normal", last_name="User", tags=[])
    )
    
    # Filter by single tag
    results, total = contact_crud.get_contacts(db_session, tags=["vip"])
    assert total == 1
    assert results[0].first_name == "VIP"
    
    # Filter by multiple tags (must have all)
    results, total = contact_crud.get_contacts(db_session, tags=["vip", "tech"])
    assert total == 1
    assert results[0].first_name == "VIP"


def test_update_contact(db_session):
    """Test updating a contact."""
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        status=ContactStatus.lead
    )
    created = contact_crud.create_contact(db_session, contact_data)
    
    # Update contact
    update_data = ContactUpdate(
        first_name="Jane",
        status=ContactStatus.client,
        company="New Corp"
    )
    updated = contact_crud.update_contact(db_session, created.id, update_data)
    
    assert updated is not None
    assert updated.first_name == "Jane"
    assert updated.last_name == "Doe"  # Unchanged
    assert updated.status == ContactStatus.client
    assert updated.company == "New Corp"


def test_update_contact_partial(db_session):
    """Test partial update (only some fields)."""
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        company="Old Corp"
    )
    created = contact_crud.create_contact(db_session, contact_data)
    
    # Update only company
    update_data = ContactUpdate(company="New Corp")
    updated = contact_crud.update_contact(db_session, created.id, update_data)
    
    assert updated.company == "New Corp"
    assert updated.first_name == "John"  # Unchanged
    assert updated.email == "john@example.com"  # Unchanged


def test_update_contact_not_found(db_session):
    """Test updating a non-existent contact."""
    update_data = ContactUpdate(first_name="Jane")
    updated = contact_crud.update_contact(db_session, 99999, update_data)
    
    assert updated is None


def test_delete_contact(db_session):
    """Test deleting a contact."""
    contact_data = ContactCreate(first_name="John", last_name="Doe")
    created = contact_crud.create_contact(db_session, contact_data)
    
    # Delete contact
    result = contact_crud.delete_contact(db_session, created.id)
    assert result is True
    
    # Verify deletion
    fetched = contact_crud.get_contact(db_session, created.id)
    assert fetched is None


def test_delete_contact_not_found(db_session):
    """Test deleting a non-existent contact."""
    result = contact_crud.delete_contact(db_session, 99999)
    assert result is False


def test_get_contacts_by_status(db_session):
    """Test getting contacts by status."""
    for i in range(3):
        contact_crud.create_contact(
            db_session,
            ContactCreate(first_name=f"Lead{i}", last_name="User", status=ContactStatus.lead)
        )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Client", last_name="User", status=ContactStatus.client)
    )
    
    leads = contact_crud.get_contacts_by_status(db_session, ContactStatus.lead)
    assert len(leads) == 3


def test_search_contacts(db_session):
    """Test searching contacts."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Alice", last_name="Anderson")
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Bob", last_name="Alison")
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Charlie", last_name="Brown")
    )
    
    results = contact_crud.search_contacts(db_session, "ali")
    assert len(results) == 2  # Alice and Alison


def test_count_contacts_by_status(db_session):
    """Test counting contacts by status."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Lead1", last_name="User", status=ContactStatus.lead)
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Lead2", last_name="User", status=ContactStatus.lead)
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(first_name="Client", last_name="User", status=ContactStatus.client)
    )
    
    counts = contact_crud.count_contacts_by_status(db_session)
    
    assert counts[ContactStatus.lead] == 2
    assert counts[ContactStatus.client] == 1
    assert ContactStatus.lost not in counts


def test_update_contact_tags(db_session):
    """Test updating contact tags."""
    from sqlalchemy.orm.attributes import flag_modified
    
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        tags=["initial"]
    )
    created = contact_crud.create_contact(db_session, contact_data)
    
    # Update tags
    update_data = ContactUpdate(tags=["vip", "urgent"])
    updated = contact_crud.update_contact(db_session, created.id, update_data)
    
    assert updated.tags == ["vip", "urgent"]


def test_combined_filters(db_session):
    """Test combining multiple filters."""
    contact_crud.create_contact(
        db_session,
        ContactCreate(
            first_name="Alice",
            last_name="VIP",
            status=ContactStatus.client,
            tags=["vip"]
        )
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(
            first_name="Bob",
            last_name="VIP",
            status=ContactStatus.lead,
            tags=["vip"]
        )
    )
    contact_crud.create_contact(
        db_session,
        ContactCreate(
            first_name="Charlie",
            last_name="Normal",
            status=ContactStatus.client,
            tags=[]
        )
    )
    
    # Filter by status AND tags
    results, total = contact_crud.get_contacts(
        db_session,
        status=ContactStatus.client,
        tags=["vip"]
    )
    
    assert total == 1
    assert results[0].first_name == "Alice"