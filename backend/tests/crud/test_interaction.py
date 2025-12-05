import pytest
from datetime import datetime, timedelta
from app.crud import interaction as interaction_crud
from app.crud import contact as contact_crud
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.schemas.contact import ContactCreate
from app.models.interaction import InteractionType

DEFAULT_OCCURED_AT = datetime(year=2025, month=12, day=4)

@pytest.fixture
def sample_contact(db_session):
    """Create a sample contact for testing."""
    contact_data = ContactCreate(first_name="John", last_name="Doe")
    return contact_crud.create_contact(db_session, contact_data)


def test_create_interaction(db_session, sample_contact):
    """Test creating an interaction."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        type=InteractionType.call,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Initial call to discuss project",
        outcome="Interested in proposal"
    )
    
    interaction = interaction_crud.create_interaction(db_session, interaction_data)
    
    assert interaction.id is not None
    assert interaction.contact_id == sample_contact.id
    assert interaction.type == InteractionType.call
    assert interaction.summary == "Initial call to discuss project"
    assert interaction.outcome == "Interested in proposal"


def test_create_interaction_minimal(db_session, sample_contact):
    """Test creating an interaction with minimal fields."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Quick note"
    )
    
    interaction = interaction_crud.create_interaction(db_session, interaction_data)
    
    assert interaction.id is not None
    assert interaction.type == InteractionType.note
    assert interaction.outcome is None


def test_get_interaction(db_session, sample_contact):
    """Test getting an interaction by ID."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Test interaction"
    )
    created = interaction_crud.create_interaction(db_session, interaction_data)
    
    fetched = interaction_crud.get_interaction(db_session, created.id)
    
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.summary == "Test interaction"


def test_get_interaction_not_found(db_session):
    """Test getting a non-existent interaction."""
    interaction = interaction_crud.get_interaction(db_session, 99999)
    assert interaction is None


def test_get_interactions_pagination(db_session, sample_contact):
    """Test getting interactions with pagination."""
    # Create 5 interactions
    for i in range(5):
        interaction_data = InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=DEFAULT_OCCURED_AT - timedelta(days=i),
            summary=f"Interaction {i}"
        )
        interaction_crud.create_interaction(db_session, interaction_data)
    
    # Get first page
    interactions, total = interaction_crud.get_interactions(db_session, skip=0, limit=3)
    assert len(interactions) == 3
    assert total == 5
    
    # Get second page
    interactions, total = interaction_crud.get_interactions(db_session, skip=3, limit=3)
    assert len(interactions) == 2
    assert total == 5


def test_get_interactions_filter_by_contact(db_session):
    """Test filtering interactions by contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)
    
    # Create interactions for both contacts
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(contact_id=contact1.id, occurred_at=DEFAULT_OCCURED_AT, summary="Contact 1 - Call 1")
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(contact_id=contact1.id, occurred_at=DEFAULT_OCCURED_AT, summary="Contact 1 - Call 2")
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(contact_id=contact2.id, occurred_at=DEFAULT_OCCURED_AT, summary="Contact 2 - Call")
    )
    
    # Filter by contact1
    interactions, total = interaction_crud.get_interactions(db_session, contact_id=contact1.id)
    
    assert total == 2
    assert all(i.contact_id == contact1.id for i in interactions)


def test_get_interactions_filter_by_type(db_session, sample_contact):
    """Test filtering interactions by type."""
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.email,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Email"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Another call"
        )
    )
    
    interactions, total = interaction_crud.get_interactions(
        db_session,
        interaction_type=InteractionType.call
    )
    
    assert total == 2
    assert all(i.type == InteractionType.call for i in interactions)


def test_get_interactions_filter_by_date_range(db_session, sample_contact):
    """Test filtering interactions by date range."""
    now = datetime.now()
    
    # Create interactions at different times
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=now - timedelta(days=10),
            summary="Old interaction"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=now - timedelta(days=3),
            summary="Recent interaction"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=now,
            summary="Today interaction"
        )
    )
    
    # Get interactions from last 7 days
    start_date = now - timedelta(days=7)
    interactions, total = interaction_crud.get_interactions(
        db_session,
        start_date=start_date
    )
    
    assert total == 2


def test_get_interactions_by_contact(db_session, sample_contact):
    """Test getting all interactions for a specific contact."""
    # Create interactions
    for i in range(3):
        interaction_crud.create_interaction(
            db_session,
            InteractionCreate(
                contact_id=sample_contact.id,
                occurred_at=DEFAULT_OCCURED_AT,
                summary=f"Interaction {i}"
            )
        )
    
    interactions = interaction_crud.get_interactions_by_contact(db_session, sample_contact.id)
    
    assert len(interactions) == 3
    assert all(i.contact_id == sample_contact.id for i in interactions)


def test_update_interaction(db_session, sample_contact):
    """Test updating an interaction."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        type=InteractionType.note,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Original summary"
    )
    created = interaction_crud.create_interaction(db_session, interaction_data)
    
    # Update interaction
    update_data = InteractionUpdate(
        type=InteractionType.call,
        summary="Updated summary",
        outcome="Successful"
    )
    updated = interaction_crud.update_interaction(db_session, created.id, update_data)
    
    assert updated is not None
    assert updated.type == InteractionType.call
    assert updated.summary == "Updated summary"
    assert updated.outcome == "Successful"


def test_update_interaction_partial(db_session, sample_contact):
    """Test partial update (only some fields)."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Original summary",
        outcome="Original outcome"
    )
    created = interaction_crud.create_interaction(db_session, interaction_data)
    
    # Update only outcome
    update_data = InteractionUpdate(outcome="New outcome")
    updated = interaction_crud.update_interaction(db_session, created.id, update_data)
    
    assert updated.outcome == "New outcome"
    assert updated.summary == "Original summary"  # Unchanged


def test_update_interaction_not_found(db_session):
    """Test updating a non-existent interaction."""
    update_data = InteractionUpdate(summary="New summary")
    updated = interaction_crud.update_interaction(db_session, 99999, update_data)
    
    assert updated is None


def test_delete_interaction(db_session, sample_contact):
    """Test deleting an interaction."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Test interaction"
    )
    created = interaction_crud.create_interaction(db_session, interaction_data)
    
    # Delete interaction
    result = interaction_crud.delete_interaction(db_session, created.id)
    assert result is True
    
    # Verify deletion
    fetched = interaction_crud.get_interaction(db_session, created.id)
    assert fetched is None


def test_delete_interaction_not_found(db_session):
    """Test deleting a non-existent interaction."""
    result = interaction_crud.delete_interaction(db_session, 99999)
    assert result is False


def test_get_recent_interactions(db_session, sample_contact):
    """Test getting recent interactions."""
    now = datetime.now()
    
    # Create interactions at different times
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=now - timedelta(days=2),
            summary="Recent"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            occurred_at=now - timedelta(days=10),
            summary="Old"
        )
    )
    
    # Get interactions from last 7 days
    recent = interaction_crud.get_recent_interactions(db_session, days=7)
    
    assert len(recent) == 1
    assert recent[0].summary == "Recent"


def test_count_interactions_by_type(db_session, sample_contact):
    """Test counting interactions by type."""
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call 1"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call 2"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.email,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Email"
        )
    )
    
    counts = interaction_crud.count_interactions_by_type(db_session)
    
    assert counts[InteractionType.call] == 2
    assert counts[InteractionType.email] == 1


def test_count_interactions_by_type_filtered_by_contact(db_session):
    """Test counting interactions by type for specific contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)
    
    # Create interactions for contact1
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=contact1.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=contact1.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call 2"
        )
    )
    
    # Create interaction for contact2
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=contact2.id,
            type=InteractionType.call,
            occurred_at=DEFAULT_OCCURED_AT,
            summary="Call"
        )
    )
    
    counts = interaction_crud.count_interactions_by_type(db_session, contact_id=contact1.id)
    
    assert counts[InteractionType.call] == 2


def test_combined_filters(db_session, sample_contact):
    """Test combining multiple filters."""
    now = datetime.now()
    
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=now - timedelta(days=2),
            summary="Recent call"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.email,
            occurred_at=now - timedelta(days=2),
            summary="Recent email"
        )
    )
    interaction_crud.create_interaction(
        db_session,
        InteractionCreate(
            contact_id=sample_contact.id,
            type=InteractionType.call,
            occurred_at=now - timedelta(days=10),
            summary="Old call"
        )
    )
    
    # Filter by type AND date range
    start_date = now - timedelta(days=7)
    interactions, total = interaction_crud.get_interactions(
        db_session,
        contact_id=sample_contact.id,
        interaction_type=InteractionType.call,
        start_date=start_date
    )
    
    assert total == 1
    assert interactions[0].summary == "Recent call"