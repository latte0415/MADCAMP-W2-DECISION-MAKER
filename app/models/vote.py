import uuid
from datetime import datetime
from sqlalchemy import (
    Integer, DateTime, ForeignKey, CheckConstraint,
    UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AssumptionProposalVote(Base):
    __tablename__ = "assumption_proposal_votes"
    __table_args__ = (
        UniqueConstraint("assumption_proposal_id", "created_by", name="uq_assumption_proposal_votes_proposal_user"),
        Index("idx_assumption_proposal_votes_proposal_id", "assumption_proposal_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assumption_proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assumption_proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    proposal = relationship("AssumptionProposal", back_populates="votes")
    voter = relationship("User", foreign_keys=[created_by])


class CriterionProposalVote(Base):
    __tablename__ = "criterion_proposal_votes"
    __table_args__ = (
        UniqueConstraint("criterion_proposal_id", "created_by", name="uq_criterion_proposal_votes_proposal_user"),
        Index("idx_criterion_proposal_votes_proposal_id", "criterion_proposal_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    criterion_proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criteria_proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    proposal = relationship("CriteriaProposal", back_populates="votes")
    voter = relationship("User", foreign_keys=[created_by])


class ConclusionProposalVote(Base):
    __tablename__ = "conclusion_proposal_votes"
    __table_args__ = (
        UniqueConstraint("conclusion_proposal_id", "created_by", name="uq_conclusion_proposal_votes_proposal_user"),
        Index("idx_conclusion_proposal_votes_proposal_id", "conclusion_proposal_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conclusion_proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conclusion_proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    proposal = relationship("ConclusionProposal", back_populates="votes")
    voter = relationship("User", foreign_keys=[created_by])


class OptionVote(Base):
    __tablename__ = "option_votes"
    __table_args__ = (
        UniqueConstraint("option_id", "created_by", name="uq_option_votes_option_user"),
        Index("idx_option_votes_option_id", "option_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("options.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    option = relationship("Option", back_populates="votes")
    voter = relationship("User", foreign_keys=[created_by])


class CriterionPriority(Base):
    __tablename__ = "criterion_priorities"
    __table_args__ = (
        UniqueConstraint("criterion_id", "created_by", name="uq_criterion_priorities_criterion_user"),
        CheckConstraint("priority_rank > 0", name="ck_criterion_priorities_rank_positive"),
        Index("idx_criterion_priorities_criterion_id", "criterion_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criterion.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    criterion = relationship("Criterion", back_populates="priorities")
    user = relationship("User", foreign_keys=[created_by])
