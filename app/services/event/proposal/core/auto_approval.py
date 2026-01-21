"""자동 승인 로직 공통화"""
from typing import Callable, TypeVar
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.proposal import ProposalStatusType

TProposal = TypeVar('TProposal')


class AutoApprovalChecker:
    """자동 승인 로직 공통화"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_and_auto_approve(
        self,
        proposal: TProposal,
        event: Event,
        vote_count: int,
        # 타입별 설정
        min_votes_required: int | None,  # Assumption/Criteria용
        approval_threshold_percent: float | None,  # Conclusion용
        total_members: int | None,  # Conclusion용
        is_auto_approved: bool,  # 자동 승인 활성화 여부
        # 타입별 함수
        approve_if_pending_fn: Callable[[UUID, datetime], TProposal | None],
        apply_proposal_fn: Callable[[TProposal, Event], None],
        create_outbox_event_fn: Callable[[TProposal, Event], None] | None = None,
    ) -> None:
        """
        자동 승인 체크 공통 로직
        
        Args:
            proposal: Proposal 객체
            event: Event 객체
            vote_count: 현재 투표 수
            min_votes_required: 최소 투표 수 (Assumption/Criteria용)
            approval_threshold_percent: 승인 임계값 퍼센트 (Conclusion용)
            total_members: 전체 멤버 수 (Conclusion용)
            is_auto_approved: 자동 승인 활성화 여부
            approve_if_pending_fn: 조건부 승인 함수 (repository 레벨)
            apply_proposal_fn: 제안 적용 함수 (타입별)
            create_outbox_event_fn: Outbox 이벤트 생성 함수 (선택)
        """
        # PENDING 상태가 아니면 자동 승인 로직 적용하지 않음
        if proposal.proposal_status != ProposalStatusType.PENDING:
            return
        
        if not is_auto_approved:
            return
        
        # Assumption/Criteria: 투표 수 기반
        if min_votes_required is not None:
            if vote_count >= min_votes_required:
                accepted_at = datetime.now(timezone.utc)
                approved_proposal = approve_if_pending_fn(proposal.id, accepted_at)
                if approved_proposal:
                    # 승인 성공 시 proposal을 다시 조회하여 관계 로드
                    # proposal 타입에 따라 적절한 관계만 refresh
                    refresh_attrs = ['votes']
                    if hasattr(approved_proposal, 'assumption'):
                        refresh_attrs.append('assumption')
                    if hasattr(approved_proposal, 'criterion'):
                        refresh_attrs.append('criterion')
                    self.db.refresh(approved_proposal, refresh_attrs)
                    # 자동 승인 시 즉시 적용
                    apply_proposal_fn(approved_proposal, event)
                    # Outbox 이벤트 생성 (선택)
                    if create_outbox_event_fn:
                        create_outbox_event_fn(approved_proposal, event)
        
        # Conclusion: 비율 기반
        elif approval_threshold_percent is not None and total_members is not None:
            if total_members == 0:
                return  # 멤버가 없으면 승인 불가
            
            vote_percent = (vote_count / total_members) * 100
            if vote_percent >= approval_threshold_percent:
                accepted_at = datetime.now(timezone.utc)
                approved_proposal = approve_if_pending_fn(proposal.id, accepted_at)
                if approved_proposal:
                    # 승인 성공 시 proposal을 다시 조회하여 관계 로드
                    self.db.refresh(approved_proposal, ['votes', 'criterion'])
                    # 자동 승인 시 즉시 적용
                    apply_proposal_fn(approved_proposal, event)
                    # Outbox 이벤트 생성 (선택)
                    if create_outbox_event_fn:
                        create_outbox_event_fn(approved_proposal, event)
