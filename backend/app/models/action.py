from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.models import Base


class ActionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class ActionPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ActionType(str, enum.Enum):
    call = "call"
    meeting = "meeting"
    follow_up = "follow_up"
    email = "email"
    other = "other"


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposal_id = Column(
        Integer,
        ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=True,
        index=False,
    )
    interaction_id = Column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=True,
        index=False,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(ActionStatus), default=ActionStatus.pending, nullable=False, index=True
    )
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    due_at = Column(DateTime, nullable=True, index=True)
    action_type = Column(
        Enum(ActionType), default=ActionType.other, nullable=False, index=True
    )
    assigned_to = Column(Integer, nullable=True)  # could link to users later
    priority = Column(
        Enum(ActionPriority), default=ActionPriority.medium, nullable=False, index=True
    )

    contact = relationship("Contact", back_populates="actions", lazy="selectin")
    interaction = relationship("Interaction", back_populates="actions", lazy="selectin")
    proposal = relationship("Proposal", back_populates="actions", lazy="selectin")


__table_args__ = (Index("ix_actions_status_due", "status", "due_at"),)
