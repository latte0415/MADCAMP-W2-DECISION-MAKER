import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Boolean, Integer, DateTime, ForeignKey, Text, CheckConstraint,
    UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EventStatusType(PyEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class MembershipStatusType(PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("entrance_code", name="uq_events_entrance_code"),
        CheckConstraint("LENGTH(entrance_code) = 6", name="ck_events_entrance_code_length"),
        CheckConstraint(
            "entrance_code ~ '^[A-Z0-9]{6}$'",
            name="ck_events_entrance_code_format"
        ),
        CheckConstraint("max_membership > 0", name="ck_events_max_membership_positive"),
        CheckConstraint(
            "(assumption_is_auto_approved_by_votes = false) OR (assumption_min_votes_required IS NOT NULL)",
            name="ck_events_assumption_votes_required"
        ),
        CheckConstraint(
            "(criteria_is_auto_approved_by_votes = false) OR (criteria_min_votes_required IS NOT NULL)",
            name="ck_events_criteria_votes_required"
        ),
        CheckConstraint(
            "(conclusion_is_auto_approved_by_votes = false) OR (conclusion_approval_threshold_percent IS NOT NULL)",
            name="ck_events_conclusion_threshold_required"
        ),
        CheckConstraint(
            "conclusion_approval_threshold_percent IS NULL OR (conclusion_approval_threshold_percent >= 1 AND conclusion_approval_threshold_percent <= 100)",
            name="ck_events_conclusion_threshold_range"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    decision_subject: Mapped[str] = mapped_column(Text, nullable=False)
    entrance_code: Mapped[str] = mapped_column(String(6), nullable=False)
    
    assumption_is_auto_approved_by_votes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    criteria_is_auto_approved_by_votes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    membership_is_auto_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    conclusion_is_auto_approved_by_votes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    
    assumption_min_votes_required: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criteria_min_votes_required: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conclusion_approval_threshold_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    event_status: Mapped[EventStatusType] = mapped_column(
        ENUM(EventStatusType, name="event_status_type", create_type=False),
        nullable=False
    )
    max_membership: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    memberships = relationship(
        "EventMembership", back_populates="event", cascade="all, delete-orphan"
    )
    options = relationship(
        "Option", back_populates="event", cascade="all, delete-orphan"
    )
    assumptions = relationship(
        "Assumption", back_populates="event", cascade="all, delete-orphan"
    )
    criteria = relationship(
        "Criterion", back_populates="event", cascade="all, delete-orphan"
    )
    assumption_proposals = relationship(
        "AssumptionProposal", back_populates="event", cascade="all, delete-orphan"
    )
    criteria_proposals = relationship(
        "CriteriaProposal", back_populates="event", cascade="all, delete-orphan"
    )


class EventMembership(Base):
    __tablename__ = "event_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_event_memberships_user_event"),
        Index("idx_event_memberships_event_id", "event_id"),
        Index("idx_event_memberships_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    membership_status: Mapped[MembershipStatusType] = mapped_column(
        ENUM(MembershipStatusType, name="membership_status_type", create_type=False),
        nullable=False,
        server_default="PENDING"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    event = relationship("Event", back_populates="memberships")


class Option(Base):
    __tablename__ = "options"
    __table_args__ = (
        Index("idx_options_event_id", "event_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    event = relationship("Event", back_populates="options")
    creator = relationship("User", foreign_keys=[created_by])
    votes = relationship(
        "OptionVote", back_populates="option", cascade="all, delete-orphan"
    )
