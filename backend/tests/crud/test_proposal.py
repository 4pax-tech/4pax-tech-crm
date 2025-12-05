import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.crud import proposal as proposal_crud
from app.crud import contact as contact_crud
from app.schemas.proposal import ProposalCreate, ProposalUpdate
from app.schemas.contact import ContactCreate
from app.models.proposal import ProposalStatus


@pytest.fixture
def sample_contact(db_session):
    """Create a sample contact for testing."""
    contact_data = ContactCreate(first_name="John", last_name="Doe")
    return contact_crud.create_contact(db_session, contact_data)


def test_create_proposal(db_session, sample_contact):
    """Test creating a proposal."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Website Redesign",
        description="Complete website overhaul",
        value=Decimal("15000.00"),
        status=ProposalStatus.draft
    )
    
    proposal = proposal_crud.create_proposal(db_session, proposal_data)
    
    assert proposal.id is not None
    assert proposal.contact_id == sample_contact.id
    assert proposal.title == "Website Redesign"
    assert proposal.value == Decimal("15000.00")
    assert proposal.status == ProposalStatus.draft


def test_create_proposal_minimal(db_session, sample_contact):
    """Test creating a proposal with minimal fields."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Basic Proposal"
    )
    
    proposal = proposal_crud.create_proposal(db_session, proposal_data)
    
    assert proposal.id is not None
    assert proposal.status == ProposalStatus.draft
    assert proposal.value is None


def test_get_proposal(db_session, sample_contact):
    """Test getting a proposal by ID."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Test Proposal"
    )
    created = proposal_crud.create_proposal(db_session, proposal_data)
    
    fetched = proposal_crud.get_proposal(db_session, created.id)
    
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Test Proposal"


def test_get_proposal_not_found(db_session):
    """Test getting a non-existent proposal."""
    proposal = proposal_crud.get_proposal(db_session, 99999)
    assert proposal is None


def test_get_proposals_pagination(db_session, sample_contact):
    """Test getting proposals with pagination."""
    # Create 5 proposals
    for i in range(5):
        proposal_data = ProposalCreate(
            contact_id=sample_contact.id,
            title=f"Proposal {i}"
        )
        proposal_crud.create_proposal(db_session, proposal_data)
    
    # Get first page
    proposals, total = proposal_crud.get_proposals(db_session, skip=0, limit=3)
    assert len(proposals) == 3
    assert total == 5
    
    # Get second page
    proposals, total = proposal_crud.get_proposals(db_session, skip=3, limit=3)
    assert len(proposals) == 2
    assert total == 5


def test_get_proposals_filter_by_contact(db_session):
    """Test filtering proposals by contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)
    
    # Create proposals for both contacts
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(contact_id=contact1.id, title="Contact 1 - Proposal 1")
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(contact_id=contact1.id, title="Contact 1 - Proposal 2")
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(contact_id=contact2.id, title="Contact 2 - Proposal")
    )
    
    # Filter by contact1
    proposals, total = proposal_crud.get_proposals(db_session, contact_id=contact1.id)
    
    assert total == 2
    assert all(p.contact_id == contact1.id for p in proposals)


def test_get_proposals_filter_by_status(db_session, sample_contact):
    """Test filtering proposals by status."""
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft Proposal",
            status=ProposalStatus.draft
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Submitted Proposal",
            status=ProposalStatus.submitted
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Won Proposal",
            status=ProposalStatus.won
        )
    )
    
    proposals, total = proposal_crud.get_proposals(
        db_session,
        status=ProposalStatus.draft
    )
    
    assert total == 1
    assert proposals[0].title == "Draft Proposal"


def test_get_proposals_filter_by_value_range(db_session, sample_contact):
    """Test filtering proposals by value range."""
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Small Project",
            value=Decimal("5000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Medium Project",
            value=Decimal("15000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Large Project",
            value=Decimal("50000.00")
        )
    )
    
    # Get proposals between 10k and 30k
    proposals, total = proposal_crud.get_proposals(
        db_session,
        min_value=10000.00,
        max_value=30000.00
    )
    
    assert total == 1
    assert proposals[0].title == "Medium Project"


def test_get_proposals_by_contact(db_session, sample_contact):
    """Test getting all proposals for a specific contact."""
    # Create proposals
    for i in range(3):
        proposal_crud.create_proposal(
            db_session,
            ProposalCreate(
                contact_id=sample_contact.id,
                title=f"Proposal {i}"
            )
        )
    
    proposals = proposal_crud.get_proposals_by_contact(db_session, sample_contact.id)
    
    assert len(proposals) == 3
    assert all(p.contact_id == sample_contact.id for p in proposals)


def test_update_proposal(db_session, sample_contact):
    """Test updating a proposal."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Original Title",
        status=ProposalStatus.draft,
        value=Decimal("10000.00")
    )
    created = proposal_crud.create_proposal(db_session, proposal_data)
    
    # Update proposal
    update_data = ProposalUpdate(
        title="Updated Title",
        status=ProposalStatus.submitted,
        value=Decimal("12000.00")
    )
    updated = proposal_crud.update_proposal(db_session, created.id, update_data)
    
    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.status == ProposalStatus.submitted
    assert updated.value == Decimal("12000.00")


def test_update_proposal_partial(db_session, sample_contact):
    """Test partial update (only some fields)."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Original Title",
        value=Decimal("10000.00"),
        description="Original description"
    )
    created = proposal_crud.create_proposal(db_session, proposal_data)
    
    # Update only status
    update_data = ProposalUpdate(status=ProposalStatus.won)
    updated = proposal_crud.update_proposal(db_session, created.id, update_data)
    
    assert updated.status == ProposalStatus.won
    assert updated.title == "Original Title"  # Unchanged
    assert updated.value == Decimal("10000.00")  # Unchanged


def test_update_proposal_not_found(db_session):
    """Test updating a non-existent proposal."""
    update_data = ProposalUpdate(title="New Title")
    updated = proposal_crud.update_proposal(db_session, 99999, update_data)
    
    assert updated is None


def test_delete_proposal(db_session, sample_contact):
    """Test deleting a proposal."""
    proposal_data = ProposalCreate(
        contact_id=sample_contact.id,
        title="Test Proposal"
    )
    created = proposal_crud.create_proposal(db_session, proposal_data)
    
    # Delete proposal
    result = proposal_crud.delete_proposal(db_session, created.id)
    assert result is True
    
    # Verify deletion
    fetched = proposal_crud.get_proposal(db_session, created.id)
    assert fetched is None


def test_delete_proposal_not_found(db_session):
    """Test deleting a non-existent proposal."""
    result = proposal_crud.delete_proposal(db_session, 99999)
    assert result is False


def test_get_proposals_by_status(db_session, sample_contact):
    """Test getting proposals by status."""
    for i in range(3):
        proposal_crud.create_proposal(
            db_session,
            ProposalCreate(
                contact_id=sample_contact.id,
                title=f"Draft {i}",
                status=ProposalStatus.draft
            )
        )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Won",
            status=ProposalStatus.won
        )
    )
    
    drafts = proposal_crud.get_proposals_by_status(db_session, ProposalStatus.draft)
    assert len(drafts) == 3


def test_get_expired_proposals(db_session, sample_contact):
    """Test getting expired proposals."""
    now = datetime.now(timezone.utc)
    
    # Create expired proposal
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Expired Proposal",
            status=ProposalStatus.submitted,
            expires_at=now - timedelta(days=1)
        )
    )
    
    # Create active proposal
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Active Proposal",
            status=ProposalStatus.submitted,
            expires_at=now + timedelta(days=30)
        )
    )
    
    # Create expired but won proposal (should not be included)
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Expired Won",
            status=ProposalStatus.won,
            expires_at=now - timedelta(days=1)
        )
    )
    
    expired = proposal_crud.get_expired_proposals(db_session)
    
    assert len(expired) == 1
    assert expired[0].title == "Expired Proposal"


def test_count_proposals_by_status(db_session, sample_contact):
    """Test counting proposals by status."""
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft 1",
            status=ProposalStatus.draft
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft 2",
            status=ProposalStatus.draft
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Won",
            status=ProposalStatus.won
        )
    )
    
    counts = proposal_crud.count_proposals_by_status(db_session)
    
    assert counts[ProposalStatus.draft] == 2
    assert counts[ProposalStatus.won] == 1


def test_count_proposals_by_status_filtered_by_contact(db_session):
    """Test counting proposals by status for specific contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)
    
    # Create proposals for contact1
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact1.id,
            title="Draft",
            status=ProposalStatus.draft
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact1.id,
            title="Won",
            status=ProposalStatus.won
        )
    )
    
    # Create proposal for contact2
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact2.id,
            title="Draft",
            status=ProposalStatus.draft
        )
    )
    
    counts = proposal_crud.count_proposals_by_status(db_session, contact_id=contact1.id)
    
    assert counts[ProposalStatus.draft] == 1
    assert counts[ProposalStatus.won] == 1


def test_get_total_value_by_status(db_session, sample_contact):
    """Test getting total value by status."""
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft 1",
            status=ProposalStatus.draft,
            value=Decimal("5000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft 2",
            status=ProposalStatus.draft,
            value=Decimal("7000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Won",
            status=ProposalStatus.won,
            value=Decimal("15000.00")
        )
    )
    
    totals = proposal_crud.get_total_value_by_status(db_session)
    
    assert totals[ProposalStatus.draft] == 12000.00
    assert totals[ProposalStatus.won] == 15000.00


def test_get_total_value_by_status_filtered_by_contact(db_session):
    """Test getting total value by status for specific contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)
    
    # Create proposals for contact1
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact1.id,
            title="Draft",
            status=ProposalStatus.draft,
            value=Decimal("10000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact1.id,
            title="Won",
            status=ProposalStatus.won,
            value=Decimal("20000.00")
        )
    )
    
    # Create proposal for contact2
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=contact2.id,
            title="Draft",
            status=ProposalStatus.draft,
            value=Decimal("5000.00")
        )
    )
    
    totals = proposal_crud.get_total_value_by_status(db_session, contact_id=contact1.id)
    
    assert totals[ProposalStatus.draft] == 10000.00
    assert totals[ProposalStatus.won] == 20000.00


def test_combined_filters(db_session, sample_contact):
    """Test combining multiple filters."""
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft Small",
            status=ProposalStatus.draft,
            value=Decimal("5000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Draft Large",
            status=ProposalStatus.draft,
            value=Decimal("50000.00")
        )
    )
    proposal_crud.create_proposal(
        db_session,
        ProposalCreate(
            contact_id=sample_contact.id,
            title="Won Large",
            status=ProposalStatus.won,
            value=Decimal("50000.00")
        )
    )
    
    # Filter by status AND value range
    proposals, total = proposal_crud.get_proposals(
        db_session,
        contact_id=sample_contact.id,
        status=ProposalStatus.draft,
        min_value=10000.00
    )
    
    assert total == 1
    assert proposals[0].title == "Draft Large"