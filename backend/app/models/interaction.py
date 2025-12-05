from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.models import Base


class InteractionType(str, enum.Enum):
    call = "call"
    email = "email"
    meeting = "meeting"
    note = "note"
    other = "other"


class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(Enum(InteractionType), default=InteractionType.note, nullable=False)
    occurred_at = Column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
    summary = Column(Text, nullable=False)
    outcome = Column(String(255), nullable=True)
    created_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    occurred_at = Column(DateTime, nullable=False)

    contact = relationship("Contact", back_populates="interactions", lazy="selectin")
    actions = relationship(
        "Action", back_populates="interaction", cascade="all, delete-orphan"
    )
