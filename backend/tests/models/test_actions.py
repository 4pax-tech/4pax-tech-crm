import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.contact import Contact, ContactStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.interaction import Interaction, InteractionType
from app.models.action import Action, ActionStatus, ActionPriority, ActionType


def test_action_creation_minimal(db_session):
    """Test creating an action with minimal required fields."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    action = Action(contact_id=contact.id, title="Call client")
    db_session.add(action)
    db_session.commit()

    assert action.id is not None
    assert action.contact_id == contact.id
    assert action.title == "Call client"
    assert action.status == ActionStatus.pending
    assert action.priority == ActionPriority.medium
    assert action.action_type == ActionType.other
    assert action.created_at is not None


def test_action_creation_full(db_session):
    """Test creating an action with all fields."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    due_date = datetime.now() + timedelta(days=7)
    action = Action(
        contact_id=contact.id,
        title="Follow up on proposal",
        description="Discuss technical requirements",
        status=ActionStatus.pending,
        priority=ActionPriority.high,
        action_type=ActionType.follow_up,
        due_at=due_date,
        assigned_to=1,
    )
    db_session.add(action)
    db_session.commit()

    assert action.title == "Follow up on proposal"
    assert action.description == "Discuss technical requirements"
    assert action.priority == ActionPriority.high
    assert action.action_type == ActionType.follow_up
    assert action.due_at == due_date
    assert action.assigned_to == 1


def test_action_status_enum_valid(db_session):
    """Test that all valid action statuses work correctly."""
    contact = Contact(first_name="Test", last_name="User")
    db_session.add(contact)
    db_session.commit()

    for status in ActionStatus:
        action = Action(
            contact_id=contact.id, title=f"Test Action {status.value}", status=status
        )
        db_session.add(action)
        db_session.commit()
        assert action.status == status
        db_session.delete(action)
        db_session.commit()


def test_action_priority_enum_valid(db_session):
    """Test that all valid action priorities work correctly."""
    contact = Contact(first_name="Test", last_name="User")
    db_session.add(contact)
    db_session.commit()

    for priority in ActionPriority:
        action = Action(
            contact_id=contact.id,
            title=f"Test Action {priority.value}",
            priority=priority,
        )
        db_session.add(action)
        db_session.commit()
        assert action.priority == priority
        db_session.delete(action)
        db_session.commit()


def test_action_type_enum_valid(db_session):
    """Test that all valid action types work correctly."""
    contact = Contact(first_name="Test", last_name="User")
    db_session.add(contact)
    db_session.commit()

    for action_type in ActionType:
        action = Action(
            contact_id=contact.id,
            title=f"Test Action {action_type.value}",
            action_type=action_type,
        )
        db_session.add(action)
        db_session.commit()
        assert action.action_type == action_type
        db_session.delete(action)
        db_session.commit()


def test_action_missing_contact_id(db_session):
    """Test that missing contact_id raises an error."""
    with pytest.raises(IntegrityError):
        action = Action(title="Test Action")
        db_session.add(action)
        db_session.commit()


def test_action_missing_title(db_session):
    """Test that missing title raises an error."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    with pytest.raises(IntegrityError):
        action = Action(contact_id=contact.id)
        db_session.add(action)
        db_session.commit()


def test_action_relationship_with_contact(db_session):
    """Test the relationship between Action and Contact."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    action = Action(
        contact_id=contact.id, title="Schedule meeting", action_type=ActionType.meeting
    )
    db_session.add(action)
    db_session.commit()

    # Test forward relationship
    assert action.contact.id == contact.id
    assert action.contact.first_name == "John"

    # Test reverse relationship
    assert len(contact.actions) == 1
    assert contact.actions[0].title == "Schedule meeting"


def test_action_relationship_with_proposal(db_session):
    """Test the relationship between Action and Proposal."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(contact_id=contact.id, title="Website Redesign")
    db_session.add(proposal)
    db_session.commit()

    action = Action(
        contact_id=contact.id,
        proposal_id=proposal.id,
        title="Follow up on proposal",
    )
    db_session.add(action)
    db_session.commit()

    # Test forward relationship
    assert action.proposal.id == proposal.id
    assert action.proposal.title == "Website Redesign"

    # Test reverse relationship
    assert len(proposal.actions) == 1
    assert proposal.actions[0].title == "Follow up on proposal"


def test_action_relationship_with_interaction(db_session):
    """Test the relationship between Action and Interaction."""
    occurred_at = datetime(year=2025, month=12, day=4)
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    interaction = Interaction(contact_id=contact.id, summary="Initial discussion", occurred_at=occurred_at)
    db_session.add(interaction)
    db_session.commit()

    action = Action(
        contact_id=contact.id,
        interaction_id=interaction.id,
        title="Send follow-up email",
    )
    db_session.add(action)
    db_session.commit()

    # Test forward relationship
    assert action.interaction.id == interaction.id
    assert action.interaction.summary == "Initial discussion"

    # Test reverse relationship
    assert len(interaction.actions) == 1
    assert interaction.actions[0].title == "Send follow-up email"


def test_action_cascade_delete_contact(db_session):
    """Test that deleting a contact deletes associated actions."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    action1 = Action(contact_id=contact.id, title="Action 1")
    action2 = Action(contact_id=contact.id, title="Action 2")
    db_session.add_all([action1, action2])
    db_session.commit()

    contact_id = contact.id
    db_session.delete(contact)
    db_session.commit()

    # Verify actions were deleted
    remaining = db_session.query(Action).filter(Action.contact_id == contact_id).all()
    assert len(remaining) == 0


def test_action_cascade_delete_proposal(db_session):
    """Test that deleting a proposal deletes associated actions."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    proposal = Proposal(contact_id=contact.id, title="Test Proposal")
    db_session.add(proposal)
    db_session.commit()

    action = Action(
        contact_id=contact.id, proposal_id=proposal.id, title="Follow up"
    )
    db_session.add(action)
    db_session.commit()

    proposal_id = proposal.id
    db_session.delete(proposal)
    db_session.commit()

    # Verify action was deleted
    remaining = (
        db_session.query(Action).filter(Action.proposal_id == proposal_id).all()
    )
    assert len(remaining) == 0


def test_action_complete_workflow(db_session):
    """Test typical action completion workflow."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    action = Action(
        contact_id=contact.id,
        title="Call client",
        status=ActionStatus.pending,
        priority=ActionPriority.high,
    )
    db_session.add(action)
    db_session.commit()

    # Complete the action
    action.status = ActionStatus.completed
    action.completed_at = datetime.now()
    db_session.commit()

    assert action.status == ActionStatus.completed
    assert action.completed_at is not None


def test_action_query_pending_by_priority(db_session):
    """Test querying pending actions by priority."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    actions = [
        Action(contact_id=contact.id, title="Low 1", priority=ActionPriority.low),
        Action(contact_id=contact.id, title="High 1", priority=ActionPriority.high),
        Action(contact_id=contact.id, title="Urgent 1", priority=ActionPriority.urgent),
    ]
    db_session.add_all(actions)
    db_session.commit()

    # Query high priority actions
    high_priority = (
        db_session.query(Action)
        .filter(
            Action.status == ActionStatus.pending,
            Action.priority.in_([ActionPriority.high, ActionPriority.urgent]),
        )
        .all()
    )

    assert len(high_priority) == 2


def test_action_query_overdue(db_session):
    """Test querying overdue actions."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    # Overdue action
    overdue = Action(
        contact_id=contact.id,
        title="Overdue task",
        due_at=datetime.now() - timedelta(days=1),
        status=ActionStatus.pending,
    )

    # Future action
    future = Action(
        contact_id=contact.id,
        title="Future task",
        due_at=datetime.now() + timedelta(days=7),
        status=ActionStatus.pending,
    )

    db_session.add_all([overdue, future])
    db_session.commit()

    # Query overdue actions
    now = datetime.now()
    overdue_actions = (
        db_session.query(Action)
        .filter(Action.status == ActionStatus.pending, Action.due_at < now)
        .all()
    )

    assert len(overdue_actions) == 1
    assert overdue_actions[0].title == "Overdue task"


def test_action_query_by_status_and_due_date(db_session):
    """Test composite query on status and due date (index usage)."""
    contact = Contact(first_name="John", last_name="Doe")
    db_session.add(contact)
    db_session.commit()

    upcoming_date = datetime.now() + timedelta(days=3)

    actions = [
        Action(
            contact_id=contact.id,
            title="Pending Soon",
            status=ActionStatus.pending,
            due_at=upcoming_date,
        ),
        Action(
            contact_id=contact.id,
            title="Completed Soon",
            status=ActionStatus.completed,
            due_at=upcoming_date,
        ),
        Action(
            contact_id=contact.id,
            title="Pending Later",
            status=ActionStatus.pending,
            due_at=datetime.now() + timedelta(days=30),
        ),
    ]
    db_session.add_all(actions)
    db_session.commit()

    # Query pending actions due within 7 days
    cutoff = datetime.now() + timedelta(days=7)
    upcoming_pending = (
        db_session.query(Action)
        .filter(Action.status == ActionStatus.pending, Action.due_at <= cutoff)
        .all()
    )

    assert len(upcoming_pending) == 1
    assert upcoming_pending[0].title == "Pending Soon"


def test_action_multiple_per_contact(db_session):
    """Test that a contact can have multiple actions."""
    contact = Contact(first_name="Jane", last_name="Smith")
    db_session.add(contact)
    db_session.commit()

    actions = [
        Action(contact_id=contact.id, title="Call", action_type=ActionType.call),
        Action(contact_id=contact.id, title="Email", action_type=ActionType.email),
        Action(contact_id=contact.id, title="Meeting", action_type=ActionType.meeting),
    ]
    db_session.add_all(actions)
    db_session.commit()

    assert len(contact.actions) == 3
    assert {a.action_type for a in contact.actions} == {
        ActionType.call,
        ActionType.email,
        ActionType.meeting,
    }
