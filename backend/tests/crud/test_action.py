import pytest
from datetime import datetime, timedelta, timezone
from app.crud import action as action_crud
from app.crud import contact as contact_crud
from app.crud import proposal as proposal_crud
from app.crud import interaction as interaction_crud
from app.schemas.action import ActionCreate, ActionUpdate
from app.schemas.contact import ContactCreate
from app.schemas.proposal import ProposalCreate
from app.schemas.interaction import InteractionCreate
from app.models.action import ActionStatus, ActionPriority, ActionType


@pytest.fixture
def sample_contact(db_session):
    """Create a sample contact for testing."""
    contact_data = ContactCreate(first_name="John", last_name="Doe")
    return contact_crud.create_contact(db_session, contact_data)


def test_create_action(db_session, sample_contact):
    """Test creating an action."""
    due_date = datetime.now(timezone.utc) + timedelta(days=7)
    action_data = ActionCreate(
        contact_id=sample_contact.id,
        title="Call client",
        description="Follow up on proposal",
        priority=ActionPriority.high,
        action_type=ActionType.call,
        due_at=due_date,
    )

    action = action_crud.create_action(db_session, action_data)

    assert action.id is not None
    assert action.contact_id == sample_contact.id
    assert action.title == "Call client"
    assert action.priority == ActionPriority.high
    assert action.status == ActionStatus.pending


def test_create_action_minimal(db_session, sample_contact):
    """Test creating an action with minimal fields."""
    action_data = ActionCreate(contact_id=sample_contact.id, title="Quick task")

    action = action_crud.create_action(db_session, action_data)

    assert action.id is not None
    assert action.status == ActionStatus.pending
    assert action.priority == ActionPriority.medium
    assert action.action_type == ActionType.other


def test_get_action(db_session, sample_contact):
    """Test getting an action by ID."""
    action_data = ActionCreate(contact_id=sample_contact.id, title="Test action")
    created = action_crud.create_action(db_session, action_data)

    fetched = action_crud.get_action(db_session, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Test action"


def test_get_action_not_found(db_session):
    """Test getting a non-existent action."""
    action = action_crud.get_action(db_session, 99999)
    assert action is None


def test_get_actions_pagination(db_session, sample_contact):
    """Test getting actions with pagination."""
    # Create 5 actions
    for i in range(5):
        action_data = ActionCreate(contact_id=sample_contact.id, title=f"Action {i}")
        action_crud.create_action(db_session, action_data)

    # Get first page
    actions, total = action_crud.get_actions(db_session, skip=0, limit=3)
    assert len(actions) == 3
    assert total == 5

    # Get second page
    actions, total = action_crud.get_actions(db_session, skip=3, limit=3)
    assert len(actions) == 2
    assert total == 5


def test_get_actions_filter_by_contact(db_session):
    """Test filtering actions by contact."""
    contact1_data = ContactCreate(first_name="Alice", last_name="Smith")
    contact2_data = ContactCreate(first_name="Bob", last_name="Jones")
    contact1 = contact_crud.create_contact(db_session, contact1_data)
    contact2 = contact_crud.create_contact(db_session, contact2_data)

    # Create actions for both contacts
    action_crud.create_action(
        db_session, ActionCreate(contact_id=contact1.id, title="Contact 1 - Action 1")
    )
    action_crud.create_action(
        db_session, ActionCreate(contact_id=contact1.id, title="Contact 1 - Action 2")
    )
    action_crud.create_action(
        db_session, ActionCreate(contact_id=contact2.id, title="Contact 2 - Action")
    )

    # Filter by contact1
    actions, total = action_crud.get_actions(db_session, contact_id=contact1.id)

    assert total == 2
    assert all(a.contact_id == contact1.id for a in actions)


def test_get_actions_filter_by_status(db_session, sample_contact):
    """Test filtering actions by status."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 1", status=ActionStatus.pending
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Completed",
            status=ActionStatus.completed,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 2", status=ActionStatus.pending
        ),
    )

    actions, total = action_crud.get_actions(db_session, status=ActionStatus.pending)

    assert total == 2
    assert all(a.status == ActionStatus.pending for a in actions)


def test_get_actions_filter_by_priority(db_session, sample_contact):
    """Test filtering actions by priority."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Low Priority",
            priority=ActionPriority.low,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High Priority",
            priority=ActionPriority.high,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Urgent", priority=ActionPriority.urgent
        ),
    )

    actions, total = action_crud.get_actions(db_session, priority=ActionPriority.urgent)

    assert total == 1
    assert actions[0].priority == ActionPriority.urgent


def test_get_actions_filter_by_type(db_session, sample_contact):
    """Test filtering actions by type."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Call", action_type=ActionType.call
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Email", action_type=ActionType.email
        ),
    )

    actions, total = action_crud.get_actions(db_session, action_type=ActionType.call)

    assert total == 1
    assert actions[0].action_type == ActionType.call


def test_get_actions_overdue_only(db_session, sample_contact):
    """Test filtering overdue actions."""
    now = datetime.now(timezone.utc)

    # Create overdue action
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Overdue",
            due_at=now - timedelta(days=1),
        ),
    )

    # Create future action
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Future", due_at=now + timedelta(days=7)
        ),
    )

    actions, total = action_crud.get_actions(db_session, overdue_only=True)

    assert total == 1
    assert actions[0].title == "Overdue"


def test_get_actions_by_contact(db_session, sample_contact):
    """Test getting all actions for a specific contact."""
    # Create actions
    for i in range(3):
        action_crud.create_action(
            db_session, ActionCreate(contact_id=sample_contact.id, title=f"Action {i}")
        )

    actions = action_crud.get_actions_by_contact(db_session, sample_contact.id)

    assert len(actions) == 3
    assert all(a.contact_id == sample_contact.id for a in actions)


def test_update_action(db_session, sample_contact):
    """Test updating an action."""
    action_data = ActionCreate(
        contact_id=sample_contact.id,
        title="Original Title",
        status=ActionStatus.pending,
        priority=ActionPriority.low,
    )
    created = action_crud.create_action(db_session, action_data)

    # Update action
    update_data = ActionUpdate(
        title="Updated Title",
        priority=ActionPriority.high,
        description="Added description",
    )
    updated = action_crud.update_action(db_session, created.id, update_data)

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.priority == ActionPriority.high
    assert updated.description == "Added description"


def test_update_action_to_completed(db_session, sample_contact):
    """Test updating action to completed status auto-sets completed_at."""
    action_data = ActionCreate(
        contact_id=sample_contact.id, title="Task", status=ActionStatus.pending
    )
    created = action_crud.create_action(db_session, action_data)

    # Update to completed
    update_data = ActionUpdate(status=ActionStatus.completed)
    updated = action_crud.update_action(db_session, created.id, update_data)

    assert updated.status == ActionStatus.completed
    assert updated.completed_at is not None


def test_update_action_partial(db_session, sample_contact):
    """Test partial update (only some fields)."""
    action_data = ActionCreate(
        contact_id=sample_contact.id,
        title="Original Title",
        priority=ActionPriority.low,
        description="Original description",
    )
    created = action_crud.create_action(db_session, action_data)

    # Update only priority
    update_data = ActionUpdate(priority=ActionPriority.urgent)
    updated = action_crud.update_action(db_session, created.id, update_data)

    assert updated.priority == ActionPriority.urgent
    assert updated.title == "Original Title"  # Unchanged


def test_update_action_not_found(db_session):
    """Test updating a non-existent action."""
    update_data = ActionUpdate(title="New Title")
    updated = action_crud.update_action(db_session, 99999, update_data)

    assert updated is None


def test_delete_action(db_session, sample_contact):
    """Test deleting an action."""
    action_data = ActionCreate(contact_id=sample_contact.id, title="Test Action")
    created = action_crud.create_action(db_session, action_data)

    # Delete action
    result = action_crud.delete_action(db_session, created.id)
    assert result is True

    # Verify deletion
    fetched = action_crud.get_action(db_session, created.id)
    assert fetched is None


def test_delete_action_not_found(db_session):
    """Test deleting a non-existent action."""
    result = action_crud.delete_action(db_session, 99999)
    assert result is False


def test_get_pending_actions(db_session, sample_contact):
    """Test getting pending actions."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 1", status=ActionStatus.pending
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Completed",
            status=ActionStatus.completed,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 2", status=ActionStatus.pending
        ),
    )

    pending = action_crud.get_pending_actions(db_session)

    assert len(pending) == 2
    assert all(a.status == ActionStatus.pending for a in pending)


def test_get_overdue_actions(db_session, sample_contact):
    """Test getting overdue actions."""
    now = datetime.now(timezone.utc)

    # Create overdue actions
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Overdue 1",
            due_at=now - timedelta(days=1),
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Overdue 2",
            due_at=now - timedelta(days=5),
        ),
    )

    # Create future action
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Future", due_at=now + timedelta(days=7)
        ),
    )

    overdue = action_crud.get_overdue_actions(db_session)

    assert len(overdue) == 2


def test_get_upcoming_actions(db_session, sample_contact):
    """Test getting upcoming actions within next N days."""
    now = datetime.now(timezone.utc)

    # Create action due in 3 days
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Due Soon",
            due_at=now + timedelta(days=3),
        ),
    )

    # Create action due in 15 days
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Due Later",
            due_at=now + timedelta(days=15),
        ),
    )

    # Get actions due in next 7 days
    upcoming = action_crud.get_upcoming_actions(db_session, days=7)

    assert len(upcoming) == 1
    assert upcoming[0].title == "Due Soon"


def test_count_actions_by_status(db_session, sample_contact):
    """Test counting actions by status."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 1", status=ActionStatus.pending
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Pending 2", status=ActionStatus.pending
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Completed",
            status=ActionStatus.completed,
        ),
    )

    counts = action_crud.count_actions_by_status(db_session)

    assert counts[ActionStatus.pending] == 2
    assert counts[ActionStatus.completed] == 1


def test_count_actions_by_type(db_session, sample_contact):
    """Test counting actions by status."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Call 1", action_type=ActionType.call
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Call 2", action_type=ActionType.call
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id, title="Email", action_type=ActionType.email
        ),
    )

    counts = action_crud.count_actions_by_type(db_session)

    assert counts[ActionType.call] == 2
    assert counts[ActionType.email] == 1


def test_count_actions_by_priority(db_session, sample_contact):
    """Test counting pending actions by priority."""
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High 1",
            priority=ActionPriority.high,
            status=ActionStatus.pending,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High 2",
            priority=ActionPriority.high,
            status=ActionStatus.pending,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Low",
            priority=ActionPriority.low,
            status=ActionStatus.pending,
        ),
    )
    # This should not be counted (completed)
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High Completed",
            priority=ActionPriority.high,
            status=ActionStatus.completed,
        ),
    )

    counts = action_crud.count_actions_by_priority(db_session)

    assert counts[ActionPriority.high] == 2
    assert counts[ActionPriority.low] == 1


def test_action_with_proposal(db_session, sample_contact):
    """Test creating action linked to proposal."""
    proposal_data = ProposalCreate(contact_id=sample_contact.id, title="Test Proposal")
    proposal = proposal_crud.create_proposal(db_session, proposal_data)

    action_data = ActionCreate(
        contact_id=sample_contact.id,
        proposal_id=proposal.id,
        title="Follow up on proposal",
    )
    action = action_crud.create_action(db_session, action_data)

    assert action.proposal_id == proposal.id


def test_action_with_interaction(db_session, sample_contact):
    """Test creating action linked to interaction."""
    interaction_data = InteractionCreate(
        contact_id=sample_contact.id,
        occurred_at=datetime.now(timezone.utc),
        summary="Had a call",
    )
    interaction = interaction_crud.create_interaction(db_session, interaction_data)

    action_data = ActionCreate(
        contact_id=sample_contact.id,
        interaction_id=interaction.id,
        title="Send follow-up email",
    )
    action = action_crud.create_action(db_session, action_data)

    assert action.interaction_id == interaction.id


def test_combined_filters(db_session, sample_contact):
    """Test combining multiple filters."""
    now = datetime.now(timezone.utc)

    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High Priority Pending",
            status=ActionStatus.pending,
            priority=ActionPriority.high,
            action_type=ActionType.call,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="Low Priority Pending",
            status=ActionStatus.pending,
            priority=ActionPriority.low,
            action_type=ActionType.call,
        ),
    )
    action_crud.create_action(
        db_session,
        ActionCreate(
            contact_id=sample_contact.id,
            title="High Priority Completed",
            status=ActionStatus.completed,
            priority=ActionPriority.high,
            action_type=ActionType.call,
        ),
    )

    # Filter by status AND priority AND type
    actions, total = action_crud.get_actions(
        db_session,
        contact_id=sample_contact.id,
        status=ActionStatus.pending,
        priority=ActionPriority.high,
        action_type=ActionType.call,
    )

    assert total == 1
    assert actions[0].title == "High Priority Pending"
