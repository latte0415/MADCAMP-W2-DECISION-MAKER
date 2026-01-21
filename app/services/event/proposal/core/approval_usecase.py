"""승인/거절 상태 변경 공통 로직"""
from typing import Callable, TypeVar
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.proposal import ProposalStatusType
from app.exceptions import ConflictError, ValidationError, NotFoundError
from app.utils.transaction import transaction

TProposal = TypeVar('TProposal')


class ApprovalUseCase:
    """승인/거절 상태 변경 공통 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_status(
        self,
        event_id: UUID,
        proposal_id: UUID,
        status: ProposalStatusType,
        user_id: UUID,
        # 타입별 의존성 주입
        verify_admin_fn: Callable[[UUID, UUID], Event],
        get_proposal_fn: Callable[[UUID], TProposal],
        validate_proposal_belongs_to_event_fn: Callable[[TProposal, UUID], None],
        approve_if_pending_fn: Callable[[UUID, datetime], TProposal | None],
        reject_if_pending_fn: Callable[[UUID], TProposal | None],
        apply_proposal_fn: Callable[[TProposal, Event], None],
        build_response_fn: Callable[[TProposal, UUID], dict],
        create_outbox_event_fn: Callable[[TProposal, Event, ProposalStatusType], None] | None = None,
    ) -> dict:
        """
        Proposal 상태 변경 공통 로직
        
        Args:
            verify_admin_fn: 관리자 권한 확인 함수
            get_proposal_fn: proposal 조회 함수 (타입별)
            validate_proposal_belongs_to_event_fn: proposal이 event에 속하는지 검증
            approve_if_pending_fn: 조건부 승인 함수 (repository 레벨)
            reject_if_pending_fn: 조건부 거절 함수 (repository 레벨)
            apply_proposal_fn: 제안 적용 함수 (타입별)
            create_outbox_event_fn: Outbox 이벤트 생성 함수 (선택)
            build_response_fn: 응답 생성 함수 (타입별)
        """
        if status not in (ProposalStatusType.ACCEPTED, ProposalStatusType.REJECTED):
            raise ValidationError(
                message="Invalid status",
                detail="Status must be ACCEPTED or REJECTED"
            )
        
        # 1. 관리자 권한 확인
        event = verify_admin_fn(event_id, user_id)
        
        # 2. 제안 조회 및 검증
        proposal = get_proposal_fn(proposal_id)
        if not proposal:
            raise NotFoundError(
                message="Proposal not found",
                detail=f"Proposal with id {proposal_id} not found"
            )
        
        # proposal이 event에 속하는지 검증
        validate_proposal_belongs_to_event_fn(proposal, event_id)
        
        # 3. 조건부 UPDATE로 상태 변경 (원자성 보장)
        with transaction(self.db):
            if status == ProposalStatusType.ACCEPTED:
                accepted_at = datetime.now(timezone.utc)
                updated_proposal = approve_if_pending_fn(proposal_id, accepted_at)
            else:
                updated_proposal = reject_if_pending_fn(proposal_id)
            
            # 조건부 UPDATE 실패 처리
            if updated_proposal is None:
                self.db.refresh(proposal, ['votes'])
                if proposal.proposal_status == ProposalStatusType.ACCEPTED:
                    raise ConflictError(
                        message="Proposal already accepted",
                        detail="This proposal has already been accepted"
                    )
                elif proposal.proposal_status == ProposalStatusType.REJECTED:
                    raise ConflictError(
                        message="Proposal already rejected",
                        detail="This proposal has already been rejected"
                    )
                else:
                    raise ConflictError(
                        message="Proposal status changed",
                        detail="Proposal status has changed and cannot be updated"
                    )
            
            # 조건부 UPDATE 성공한 경우에만 후속 처리
            proposal = updated_proposal
            if status == ProposalStatusType.ACCEPTED:
                apply_proposal_fn(proposal, event)
            
            # Outbox 이벤트 생성 (트랜잭션 내부)
            if create_outbox_event_fn:
                create_outbox_event_fn(proposal, event, status)
            
            # 응답 생성을 위해 refresh
            self.db.refresh(proposal, ['votes'])
        
        return build_response_fn(proposal, user_id)
