import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Text, DateTime, ForeignKey, CheckConstraint,
    # UniqueConstraint, 
    Index, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ProposalStatusType(PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DELETED = "DELETED"


class ProposalCategoryType(PyEnum):
    CREATION = "CREATION"
    MODIFICATION = "MODIFICATION"
    DELETION = "DELETION"


class ProposalBase:
    """Proposal 모델의 공통 필드를 정의하는 Mixin"""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proposal_status: Mapped[ProposalStatusType] = mapped_column(
        ENUM(ProposalStatusType, name="proposal_status_type", create_type=False),
        nullable=False,
        server_default="PENDING"
    )
    proposal_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AssumptionProposal(Base, ProposalBase):
    __tablename__ = "assumption_proposals"
    __table_args__ = (
        # UniqueConstraint("assumption_id", "created_by", name="uq_assumption_proposals_assumption_user"),
        CheckConstraint(
            "(proposal_category = 'CREATION' AND assumption_id IS NULL) OR (proposal_category != 'CREATION' AND assumption_id IS NOT NULL)",
            name="ck_assumption_proposals_category_assumption_id"
        ),
        CheckConstraint(
            "(proposal_category = 'DELETION' AND proposal_content IS NULL) OR (proposal_category != 'DELETION' AND proposal_content IS NOT NULL)",
            name="ck_assumption_proposals_category_content"
        ),
        Index("idx_assumption_proposals_event_id", "event_id"),
        Index("idx_assumption_proposals_assumption_id", "assumption_id"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    assumption_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assumptions.id", ondelete="CASCADE"),
        nullable=True,
    )
    proposal_category: Mapped[ProposalCategoryType] = mapped_column(
        ENUM(ProposalCategoryType, name="proposal_category_type", create_type=False),
        nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assumptions.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Relationships
    event = relationship("Event", back_populates="assumption_proposals")
    assumption = relationship("Assumption", foreign_keys=[assumption_id], back_populates="proposals")
    creator = relationship("User", foreign_keys="AssumptionProposal.created_by")
    votes = relationship(
        "AssumptionProposalVote", back_populates="proposal", cascade="all, delete-orphan"
    )


class CriteriaProposal(Base, ProposalBase):
    __tablename__ = "criteria_proposals"
    __table_args__ = (
        # UniqueConstraint("criteria_id", "created_by", name="uq_criteria_proposals_criteria_user"),
        CheckConstraint(
            "(proposal_category = 'CREATION' AND criteria_id IS NULL) OR (proposal_category != 'CREATION' AND criteria_id IS NOT NULL)",
            name="ck_criteria_proposals_category_criteria_id"
        ),
        CheckConstraint(
            "(proposal_category = 'DELETION' AND proposal_content IS NULL) OR (proposal_category != 'DELETION' AND proposal_content IS NOT NULL)",
            name="ck_criteria_proposals_category_content"
        ),
        Index("idx_criteria_proposals_event_id", "event_id"),
        Index("idx_criteria_proposals_criteria_id", "criteria_id"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    criteria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=True,
    )
    proposal_category: Mapped[ProposalCategoryType] = mapped_column(
        ENUM(ProposalCategoryType, name="proposal_category_type", create_type=False),
        nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Relationships
    event = relationship("Event", back_populates="criteria_proposals")
    criterion = relationship("Criterion", foreign_keys=[criteria_id], back_populates="proposals")
    creator = relationship("User", foreign_keys="CriteriaProposal.created_by")
    votes = relationship(
        "CriterionProposalVote", back_populates="proposal", cascade="all, delete-orphan"
    )


class ConclusionProposal(Base, ProposalBase):
    __tablename__ = "conclusion_proposals"
    __table_args__ = (
        # UniqueConstraint("criterion_id", "created_by", name="uq_conclusion_proposals_criterion_user"),
        Index("idx_conclusion_proposals_criterion_id", "criterion_id"),
    )

    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=False,
    )
    # proposal_content를 nullable=False로 오버라이드
    proposal_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    criterion = relationship("Criterion", back_populates="conclusion_proposals")
    creator = relationship("User", foreign_keys="ConclusionProposal.created_by")
    votes = relationship(
        "ConclusionProposalVote", back_populates="proposal", cascade="all, delete-orphan"
    )
