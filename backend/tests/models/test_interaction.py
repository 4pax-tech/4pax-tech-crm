import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app.models.contact import Contact, ContactStatus
from app.models.interaction import Interaction, InteractionType

DEFAULT_OCCURED_AT = datetime(year=2025, month=4, day=12)

def test_interaction_creation_minimal(db_session):
    """Test creating an interaction with minimal required fields."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    interaction = Interaction(contact_id=contact.id, summary="Initial call", occurred_at=DEFAULT_OCCURED_AT)
    db_session.add(interaction)
    db_session.commit()

    assert interaction.id is not None
    assert interaction.contact_id == contact.id
    assert interaction.summary == "Initial call"
    assert interaction.type == InteractionType.note
    assert interaction.created_at is not None


def test_interaction_creation_full(db_session):
    """Test creating an interaction with all fields."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    interaction = Interaction(
        contact_id=contact.id,
        type=InteractionType.meeting,
        occurred_at=DEFAULT_OCCURED_AT,
        summary="Product demo meeting",
        outcome="Interested in Q1 2025",
        created_by="sales_rep_1",
    )
    db_session.add(interaction)
    db_session.commit()

    assert interaction.type == InteractionType.meeting
    assert interaction.outcome == "Interested in Q1 2025"
    assert interaction.created_by == "sales_rep_1"


def test_interaction_type_enum_valid(db_session):
    """Test that all valid interaction types work correctly."""
    contact = Contact(first_name="Test", last_name="User")
    db_session.add(contact)
    db_session.commit()

    for interaction_type in InteractionType:
        interaction = Interaction(
            contact_id=contact.id,
            type=interaction_type,
            summary=f"Test {interaction_type.value}", occurred_at=DEFAULT_OCCURED_AT
        )
        db_session.add(interaction)
        db_session.commit()
        assert interaction.type == interaction_type
        db_session.delete(interaction)
        db_session.commit()


def test_interaction_missing_contact_id(db_session):
    """Test that missing contact_id raises an error."""
    with pytest.raises(IntegrityError):
        interaction = Interaction(summary="Test interaction", occurred_at=DEFAULT_OCCURED_AT)
        db_session.add(interaction)
        db_session.commit()


def test_interaction_missing_summary(db_session):
    """Test that missing summary raises an error."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    with pytest.raises(IntegrityError):
        interaction = Interaction(contact_id=contact.id, occurred_at=DEFAULT_OCCURED_AT)
        db_session.add(interaction)
        db_session.commit()


def test_interaction_invalid_contact_id(db_session):
    """Test that invalid contact_id raises an error."""
    with pytest.raises(IntegrityError):
        interaction = Interaction(
            contact_id=99999,
            summary="Test interaction",  # Non-existent contact
            occurred_at=DEFAULT_OCCURED_AT
        )
        db_session.add(interaction)
        db_session.commit()


def test_interaction_relationship_with_contact(db_session):
    """Test the relationship between Interaction and Contact."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    interaction = Interaction(contact_id=contact.id, summary="Follow-up call", occurred_at=DEFAULT_OCCURED_AT)
    db_session.add(interaction)
    db_session.commit()

    # Test forward relationship
    assert interaction.contact.id == contact.id
    assert interaction.contact.first_name == "John"

    # Test reverse relationship
    assert len(contact.interactions) == 1
    assert contact.interactions[0].summary == "Follow-up call"


def test_interaction_cascade_delete(db_session):
    """Test that deleting a contact deletes associated interactions."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    interaction1 = Interaction(contact_id=contact.id, summary="Call 1", occurred_at=DEFAULT_OCCURED_AT)
    interaction2 = Interaction(contact_id=contact.id, summary="Call 2", occurred_at=DEFAULT_OCCURED_AT)
    db_session.add_all([interaction1, interaction2])
    db_session.commit()

    contact_id = contact.id
    db_session.delete(contact)
    db_session.commit()

    # Verify interactions were deleted
    remaining = (
        db_session.query(Interaction).filter(Interaction.contact_id == contact_id).all()
    )
    assert len(remaining) == 0


def test_interaction_multiple_per_contact(db_session):
    """Test that a contact can have multiple interactions."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    interactions = [
        Interaction(
            contact_id=contact.id, type=InteractionType.call, summary="Initial call", occurred_at=DEFAULT_OCCURED_AT
        ),
        Interaction(
            contact_id=contact.id, type=InteractionType.email, summary="Sent proposal", occurred_at=DEFAULT_OCCURED_AT
        ),
        Interaction(
            contact_id=contact.id, type=InteractionType.meeting, summary="Demo meeting", occurred_at=DEFAULT_OCCURED_AT
        ),
    ]
    db_session.add_all(interactions)
    db_session.commit()

    assert len(contact.interactions) == 3
    assert {i.type for i in contact.interactions} == {
        InteractionType.call,
        InteractionType.email,
        InteractionType.meeting,
    }


def test_interaction_occurred_at_indexing(db_session):
    """Test querying interactions by occurred_at (verify index works)."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    past_date = datetime.now() - timedelta(days=30)
    interaction = Interaction(
        contact_id=contact.id, occurred_at=past_date, summary="Old interaction"
    )
    db_session.add(interaction)
    db_session.commit()

    # Query by date range
    cutoff = datetime.now() - timedelta(days=7)
    old_interactions = (
        db_session.query(Interaction).filter(Interaction.occurred_at < cutoff).all()
    )

    assert len(old_interactions) == 1
    assert old_interactions[0].summary == "Old interaction"
