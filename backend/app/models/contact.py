from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum
from app.models import Base


class ContactStatus(str, enum.Enum):
    lead = "lead"
    prospect = "prospect"
    client = "client"
    lost = "lost"
    archived = "archived"


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=True, index=True, unique=True)
    phone = Column(String(64), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    status = Column(
        Enum(ContactStatus), default=ContactStatus.lead, nullable=False, index=True
    )
    source = Column(String(100), nullable=True)  # e.g. linkedin, referral
    owner_id = Column(Integer, nullable=True)  # could link to users later
    tags = Column(MutableList.as_mutable(ARRAY(String(10))), nullable=True, default=list)
    notes = Column(Text, nullable=True)
    next_action = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    interactions = relationship(
        "Interaction",
        back_populates="contact",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    proposals = relationship(
        "Proposal",
        back_populates="contact",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    actions = relationship(
        "Action",
        back_populates="contact",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
