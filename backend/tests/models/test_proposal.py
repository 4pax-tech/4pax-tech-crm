import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.contact import Contact, ContactStatus
from app.models.proposal import Proposal, ProposalStatus


def test_proposal_creation_minimal(db_session):
    """Test creating a proposal with minimal required fields."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(contact_id=contact.id, title="Website Redesign")
    db_session.add(proposal)
    db_session.commit()

    assert proposal.id is not None
    assert proposal.contact_id == contact.id
    assert proposal.title == "Website Redesign"
    assert proposal.status == ProposalStatus.draft
    assert proposal.created_at is not None
    assert proposal.updated_at is not None


def test_proposal_creation_full(db_session):
    """Test creating a proposal with all fields."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    applied_date = datetime.now()
    expires_date = datetime.now() + timedelta(days=30)

    proposal = Proposal(
        contact_id=contact.id,
        title="Mobile App Development",
        description="Full-stack mobile app for iOS and Android",
        value=Decimal("15000.50"),
        status=ProposalStatus.submitted,
        applied_at=applied_date,
        expires_at=expires_date,
    )
    db_session.add(proposal)
    db_session.commit()

    assert proposal.title == "Mobile App Development"
    assert proposal.description == "Full-stack mobile app for iOS and Android"
    assert proposal.value == Decimal("15000.50")
    assert proposal.status == ProposalStatus.submitted
    assert proposal.applied_at == applied_date
    assert proposal.expires_at == expires_date


def test_proposal_status_enum_valid(db_session):
    """Test that all valid proposal statuses work correctly."""
    contact = Contact(first_name="Test", last_name="User")
    db_session.add(contact)
    db_session.commit()

    for status in ProposalStatus:
        proposal = Proposal(
            contact_id=contact.id, title=f"Test Proposal {status.value}", status=status
        )
        db_session.add(proposal)
        db_session.commit()
        assert proposal.status == status
        db_session.delete(proposal)
        db_session.commit()


def test_proposal_status_default(db_session):
    """Test that default status is 'draft'."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(contact_id=contact.id, title="Test Proposal")
    db_session.add(proposal)
    db_session.commit()

    assert proposal.status == ProposalStatus.draft


def test_proposal_missing_contact_id(db_session):
    """Test that missing contact_id raises an error."""
    with pytest.raises(IntegrityError):
        proposal = Proposal(title="Test Proposal")
        db_session.add(proposal)
        db_session.commit()


def test_proposal_missing_title(db_session):
    """Test that missing title raises an error."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    with pytest.raises(IntegrityError):
        proposal = Proposal(contact_id=contact.id)
        db_session.add(proposal)
        db_session.commit()


def test_proposal_invalid_contact_id(db_session):
    """Test that invalid contact_id raises an error."""
    with pytest.raises(IntegrityError):
        proposal = Proposal(contact_id=99999, title="Test Proposal")
        db_session.add(proposal)
        db_session.commit()


def test_proposal_relationship_with_contact(db_session):
    """Test the relationship between Proposal and Contact."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(
        contact_id=contact.id, title="SEO Optimization", value=Decimal("5000.00")
    )
    db_session.add(proposal)
    db_session.commit()

    # Test forward relationship
    assert proposal.contact.id == contact.id
    assert proposal.contact.first_name == "John"

    # Test reverse relationship
    assert len(contact.proposals) == 1
    assert contact.proposals[0].title == "SEO Optimization"


def test_proposal_cascade_delete(db_session):
    """Test that deleting a contact deletes associated proposals."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal1 = Proposal(contact_id=contact.id, title="Proposal 1")
    proposal2 = Proposal(contact_id=contact.id, title="Proposal 2")
    db_session.add_all([proposal1, proposal2])
    db_session.commit()

    contact_id = contact.id
    db_session.delete(contact)
    db_session.commit()

    # Verify proposals were deleted
    remaining = (
        db_session.query(Proposal).filter(Proposal.contact_id == contact_id).all()
    )
    assert len(remaining) == 0


def test_proposal_multiple_per_contact(db_session):
    """Test that a contact can have multiple proposals."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    proposals = [
        Proposal(contact_id=contact.id, title="Web Dev", status=ProposalStatus.draft),
        Proposal(
            contact_id=contact.id, title="Mobile App", status=ProposalStatus.submitted
        ),
        Proposal(contact_id=contact.id, title="Consulting", status=ProposalStatus.won),
    ]
    db_session.add_all(proposals)
    db_session.commit()

    assert len(contact.proposals) == 3
    assert {p.status for p in contact.proposals} == {
        ProposalStatus.draft,
        ProposalStatus.submitted,
        ProposalStatus.won,
    }


def test_proposal_decimal_value_precision(db_session):
    """Test that decimal values maintain precision."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(
        contact_id=contact.id, title="Test Proposal", value=Decimal("12345.67")
    )
    db_session.add(proposal)
    db_session.commit()

    db_session.refresh(proposal)
    assert proposal.value == Decimal("12345.67")
    assert isinstance(proposal.value, Decimal)


def test_proposal_status_workflow(db_session):
    """Test typical proposal status workflow."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(
        contact_id=contact.id, title="Test Project", status=ProposalStatus.draft
    )
    db_session.add(proposal)
    db_session.commit()

    # Submit proposal
    proposal.status = ProposalStatus.submitted
    proposal.applied_at = datetime.now()
    db_session.commit()
    assert proposal.status == ProposalStatus.submitted
    assert proposal.applied_at is not None

    # Win proposal
    proposal.status = ProposalStatus.won
    db_session.commit()
    assert proposal.status == ProposalStatus.won


def test_proposal_expires_at_query(db_session):
    """Test querying proposals by expiration date."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    # Expired proposal
    expired_proposal = Proposal(
        contact_id=contact.id,
        title="Expired Proposal",
        expires_at=datetime.now() - timedelta(days=1),
    )

    # Active proposal
    active_proposal = Proposal(
        contact_id=contact.id,
        title="Active Proposal",
        expires_at=datetime.now() + timedelta(days=30),
    )

    db_session.add_all([expired_proposal, active_proposal])
    db_session.commit()

    # Query expired proposals
    now = datetime.now()
    expired = db_session.query(Proposal).filter(Proposal.expires_at < now).all()

    assert len(expired) == 1
    assert expired[0].title == "Expired Proposal"


def test_proposal_status_index_query(db_session):
    """Test querying proposals by status (verify index works)."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposals = [
        Proposal(contact_id=contact.id, title="Draft 1", status=ProposalStatus.draft),
        Proposal(contact_id=contact.id, title="Draft 2", status=ProposalStatus.draft),
        Proposal(contact_id=contact.id, title="Won 1", status=ProposalStatus.won),
    ]
    db_session.add_all(proposals)
    db_session.commit()

    # Query by status
    drafts = (
        db_session.query(Proposal).filter(Proposal.status == ProposalStatus.draft).all()
    )

    assert len(drafts) == 2
    assert all(p.status == ProposalStatus.draft for p in drafts)
