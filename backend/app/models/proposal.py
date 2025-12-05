from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.models import Base


class ProposalStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    won = "won"
    lost = "lost"
    ignored = "ignored"
    expired = "expired"


class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    value = Column(Numeric(10, 2), nullable=True)
    status = Column(
        Enum(ProposalStatus), default=ProposalStatus.draft, nullable=False, index=True
    )
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    expires_at = Column(DateTime, nullable=True)
    contact = relationship("Contact", back_populates="proposals", lazy="selectin")
    actions = relationship(
        "Action", back_populates="proposal", cascade="all, delete-orphan"
    )
