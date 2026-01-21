from datetime import datetime, timezone
from uuid import UUID

from app.models.event import Event, EventStatusType, MembershipStatusType
from app.models.proposal import (
    AssumptionProposal,
    CriteriaProposal,
    ConclusionProposal,
    ProposalStatusType,
    ProposalCategoryType,
)
from app.models.vote import (
    AssumptionProposalVote,
    CriterionProposalVote,
    ConclusionProposalVote,
)
from app.models.content import Assumption, Criterion
from app.services.event.base import EventBaseService
from app.schemas.event import (
    AssumptionProposalCreateRequest,
    AssumptionProposalResponse,
    AssumptionProposalVoteResponse,
    CriteriaProposalCreateRequest,
    CriteriaProposalResponse,
    CriteriaProposalVoteResponse,
    ConclusionProposalCreateRequest,
    ConclusionProposalResponse,
    ConclusionProposalVoteResponse,
)
from app.exceptions import (
    NotFoundError,
    ForbiddenError,
    ValidationError,
    ConflictError,
)
from app.utils.transaction import transaction
from app.services.idempotency_service import IdempotencyService
from app.repositories.outbox_repository import OutboxRepository
from app.services.event.proposal.core.vote_usecase import VoteUseCase
from app.services.event.proposal.core.auto_approval import AutoApprovalChecker
from app.services.event.proposal.core.approval_usecase import ApprovalUseCase
from app.services.event.proposal.core.idempotency_wrapper import IdempotencyWrapper


class ProposalService(EventBaseService):
    """Proposal 관련 서비스"""

    def __init__(
        self,
        db,
        repos,
        idempotency_service: IdempotencyService | None = None,
        outbox_repo: OutboxRepository | None = None
    ):
        super().__init__(db, repos)
        self.idempotency_service = idempotency_service
        self.outbox_repo = outbox_repo
        self.vote_usecase = VoteUseCase(db)
        self.auto_approval_checker = AutoApprovalChecker(db)
        self.approval_usecase = ApprovalUseCase(db)
        self.idempotency_wrapper = IdempotencyWrapper(idempotency_service)

    def create_assumption_proposal(
        self,
        event_id: UUID,
        request: AssumptionProposalCreateRequest,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> AssumptionProposalResponse:
        """
        전제 제안 생성
        - IN_PROGRESS 상태에서만 가능
        - ACCEPTED 멤버십 필요
        - 중복 제안 체크 (PENDING 상태만)
        """
        def _execute_create() -> dict:
            # 1. 이벤트 상태 검증 (IN_PROGRESS)
            event = self._validate_event_in_progress(event_id, "create proposals")

            # 2. 멤버십 검증 (ACCEPTED)
            self._validate_membership_accepted(user_id, event_id, "create proposals")

            # 3. proposal_category에 따른 필드 검증
            self._validate_proposal_category_fields(request, event_id)

            # 4. 중복 제안 체크 (PENDING 상태만)
            existing_proposal = self.repos.proposal.get_pending_assumption_proposal_by_user(
                event_id, request.assumption_id, user_id
            )
            if existing_proposal:
                raise ConflictError(
                    message="Duplicate proposal",
                    detail="You already have a pending proposal for this assumption"
                )

            # 5. 제안 생성
            proposal = AssumptionProposal(
                event_id=event_id,
                assumption_id=request.assumption_id,
                proposal_category=request.proposal_category,
                proposal_content=request.proposal_content,
                reason=request.reason,
                created_by=user_id,
                proposal_status=ProposalStatusType.PENDING,
            )
            with transaction(self.db):
                created_proposal = self.repos.proposal.create_assumption_proposal(proposal)
                # votes 관계를 로드하기 위해 refresh (재조회 대신)
                self.db.refresh(created_proposal, ['votes'])
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.created.v1",
                        payload={
                            "proposal_id": str(created_proposal.id),
                            "proposal_type": "assumption"
                        },
                        target_event_id=event_id
                    )
            vote_count = len(created_proposal.votes) if created_proposal.votes else 0
            has_voted = False  # 새로 생성된 제안이므로 투표 없음

            response = AssumptionProposalResponse(
                id=created_proposal.id,
                event_id=created_proposal.event_id,
                assumption_id=created_proposal.assumption_id,
                proposal_status=created_proposal.proposal_status,
                proposal_category=created_proposal.proposal_category,
                proposal_content=created_proposal.proposal_content,
                reason=created_proposal.reason,
                created_at=created_proposal.created_at,
                created_by=created_proposal.created_by,
                vote_count=vote_count,
                has_voted=has_voted,
            )
            return response.model_dump()
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="POST",
            path=f"/events/{event_id}/assumption-proposals",
            body=request.model_dump(exclude_none=True, mode='json'),
            fn=_execute_create
        )
        return AssumptionProposalResponse(**result)

    def create_assumption_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> AssumptionProposalVoteResponse:
        """
        전제 제안 투표 생성
        - IN_PROGRESS 상태에서만 가능
        - PENDING 제안에만 투표 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal or proposal.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def create_vote(pid, uid):
            vote = AssumptionProposalVote(
                assumption_proposal_id=pid,
                created_by=uid,
            )
            created_vote = self.repos.proposal.create_assumption_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo:
                proposal = self.repos.proposal.get_assumption_proposal_by_id(pid)
                if proposal:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.vote.created.v1",
                        payload={
                            "proposal_id": str(pid),
                            "proposal_type": "assumption"
                        },
                        target_event_id=proposal.event_id
                    )
            
            return created_vote
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=event.assumption_min_votes_required,
                approval_threshold_percent=None,
                total_members=None,
                is_auto_approved=event.assumption_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_assumption_proposal_if_pending,
                apply_proposal_fn=self._apply_assumption_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "assumption",
                        "event_id": str(p.event_id),
                        "approved_by": None
                    },
                    target_event_id=p.event_id
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return AssumptionProposalVoteResponse(
                message="Vote created successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.create_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_assumption_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            check_duplicate_fn=self._check_duplicate_vote,
            create_vote_fn=create_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return AssumptionProposalVoteResponse(**result)

    def delete_assumption_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> AssumptionProposalVoteResponse:
        """
        전제 제안 투표 삭제
        - IN_PROGRESS 상태에서만 가능
        - 본인 투표만 삭제 가능
        - PENDING 제안에만 투표 삭제 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal or proposal.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def get_vote(pid, uid):
            vote = self.repos.proposal.get_user_vote_on_assumption_proposal(pid, uid)
            if not vote:
                raise NotFoundError(
                    message="Vote not found",
                    detail="You have not voted on this proposal"
                )
            return vote
        
        def delete_vote(vote):
            # Outbox 이벤트 추가를 위해 proposal 조회 (트랜잭션 내부)
            proposal = self.repos.proposal.get_assumption_proposal_by_id(vote.assumption_proposal_id)
            
            self.repos.proposal.delete_assumption_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo and proposal:
                self.outbox_repo.create_outbox_event(
                    event_type="proposal.vote.deleted.v1",
                    payload={
                        "proposal_id": str(vote.assumption_proposal_id),
                        "proposal_type": "assumption"
                    },
                    target_event_id=proposal.event_id
                )
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=event.assumption_min_votes_required,
                approval_threshold_percent=None,
                total_members=None,
                is_auto_approved=event.assumption_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_assumption_proposal_if_pending,
                apply_proposal_fn=self._apply_assumption_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "assumption",
                        "event_id": str(p.event_id),
                        "approved_by": None
                    },
                    target_event_id=p.event_id
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return AssumptionProposalVoteResponse(
                message="Vote deleted successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.delete_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_assumption_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            get_vote_fn=get_vote,
            delete_vote_fn=delete_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return AssumptionProposalVoteResponse(**result)

    def _validate_proposal_pending(
        self, proposal_id: UUID, event_id: UUID, operation: str
    ) -> AssumptionProposal:
        """제안 존재 및 PENDING 상태 검증"""
        proposal = self.repos.proposal.get_assumption_proposal_by_id(proposal_id)
        if not proposal or proposal.event_id != event_id:
            raise NotFoundError(
                message="Proposal not found",
                detail=f"Proposal with id {proposal_id} not found for this event"
            )

        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(
                message="Proposal not pending",
                detail=f"{operation} can only be performed for PENDING proposals"
            )
        return proposal

    def _validate_assumption_for_proposal(
        self, assumption_id: UUID, event_id: UUID, proposal_category: ProposalCategoryType
    ) -> Assumption:
        """Assumption 존재, event_id 일치, 삭제 여부 검증"""
        assumption = self.repos.assumption.get_by_id(assumption_id)
        if not assumption or assumption.event_id != event_id:
            raise NotFoundError(
                message="Assumption not found",
                detail=f"Assumption with id {assumption_id} not found for this event"
            )
        if assumption.is_deleted:
            raise ValidationError(
                message="Assumption is deleted",
                detail="Assumption is already deleted"
            )
        return assumption

    def _validate_proposal_category_fields(
        self, request: AssumptionProposalCreateRequest, event_id: UUID
    ) -> None:
        """proposal_category에 따른 필드 검증 (proposal_content, assumption_id)"""
        if request.proposal_category == ProposalCategoryType.DELETION:
            if request.proposal_content is not None:
                raise ValidationError(
                    message="Invalid proposal_content",
                    detail="proposal_content must be NULL for DELETION proposals"
                )
        else:
            if request.proposal_content is None:
                raise ValidationError(
                    message="Missing proposal_content",
                    detail="proposal_content is required for CREATION/MODIFICATION proposals"
                )

        if request.proposal_category == ProposalCategoryType.CREATION:
            if request.assumption_id is not None:
                raise ValidationError(
                    message="Invalid assumption_id",
                    detail="assumption_id must be NULL for CREATION proposals"
                )
        else:
            if request.assumption_id is None:
                raise ValidationError(
                    message="Missing assumption_id",
                    detail=f"assumption_id is required for {request.proposal_category.value} proposals"
                )
            # assumption 존재 확인
            self._validate_assumption_for_proposal(
                request.assumption_id, event_id, request.proposal_category
            )

    def _check_duplicate_vote(self, proposal_id: UUID, user_id: UUID) -> None:
        """중복 투표 체크"""
        existing_vote = self.repos.proposal.get_user_vote_on_assumption_proposal(
            proposal_id, user_id
        )
        if existing_vote:
            raise ConflictError(
                message="Already voted",
                detail="You have already voted on this proposal"
            )

    def _get_user_vote_or_raise(
        self, proposal_id: UUID, user_id: UUID
    ) -> AssumptionProposalVote:
        """투표 존재 검증"""
        vote = self.repos.proposal.get_user_vote_on_assumption_proposal(
            proposal_id, user_id
        )
        if not vote:
            raise NotFoundError(
                message="Vote not found",
                detail="You have not voted on this proposal"
            )
        return vote

    def _check_and_auto_approve_assumption_proposal(
        self, proposal: AssumptionProposal, event: Event
    ) -> None:
        """
        투표 수가 일정 수준 도달 시 자동 승인
        
        정책:
        - auto_approved, min_votes_required 설정은 PENDING 상태인 proposal에만 소급 적용
        - 이미 ACCEPTED, REJECTED된 proposal에는 반영되지 않음
        
        동작:
        - assumption_is_auto_approved_by_votes가 True일 때만 동작
        - assumption_min_votes_required 이상이면 ACCEPTED로 변경
        - 승인 시 자동으로 제안 적용 (apply_proposal 호출)
        - PENDING 상태인 proposal에만 적용 (이미 ACCEPTED/REJECTED된 것은 무시)
        """
        # PENDING 상태가 아니면 자동 승인 로직 적용하지 않음
        if proposal.proposal_status != ProposalStatusType.PENDING:
            return

        if not event.assumption_is_auto_approved_by_votes:
            return

        if event.assumption_min_votes_required is None:
            return

        vote_count = len(proposal.votes)
        if vote_count >= event.assumption_min_votes_required:
            # 조건부 UPDATE로 락 없이 중복 승인 방지
            accepted_at = datetime.now(timezone.utc)
            approved_proposal = self.repos.proposal.approve_assumption_proposal_if_pending(
                proposal.id, accepted_at
            )
            if approved_proposal:
                # 승인 성공 시 proposal을 다시 조회하여 관계 로드
                self.db.refresh(approved_proposal, ['votes', 'assumption'])
                # 자동 승인 시 즉시 적용
                self._apply_assumption_proposal(approved_proposal, event)
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.approved.v1",
                        payload={
                            "proposal_id": str(approved_proposal.id),
                            "proposal_type": "assumption",
                            "event_id": str(approved_proposal.event_id),
                            "approved_by": None  # 자동 승인
                        },
                        target_event_id=approved_proposal.event_id
                    )
                # commit은 외부 트랜잭션 매니저가 처리

    def _apply_assumption_proposal(
        self, proposal: AssumptionProposal, event: Event
    ) -> None:
        """
        제안을 실제 Assumption에 적용
        - CREATION: 새 Assumption 생성
        - MODIFICATION: 기존 Assumption 수정 (original_content 저장, is_modified=True)
        - DELETION: 기존 Assumption 소프트 삭제 (is_deleted=True)
        """
        if proposal.proposal_category == ProposalCategoryType.CREATION:
            # 새 전제 생성
            assumption = Assumption(
                event_id=proposal.event_id,
                content=proposal.proposal_content,
                created_by=proposal.created_by,
            )
            result = self.repos.assumption.create_assumptions([assumption])
            proposal.applied_target_id = result[0].id
        elif proposal.proposal_category == ProposalCategoryType.MODIFICATION:
            # 기존 전제 수정
            assumption = self.repos.assumption.get_by_id(proposal.assumption_id)
            if assumption:
                assumption.original_content = assumption.content  # 원본 저장
                assumption.content = proposal.proposal_content
                assumption.is_modified = True
                self.repos.assumption.update_assumption(assumption, proposal.created_by)
                proposal.applied_target_id = assumption.id
        elif proposal.proposal_category == ProposalCategoryType.DELETION:
            # 소프트 삭제
            assumption = self.repos.assumption.get_by_id(proposal.assumption_id)
            if assumption:
                assumption.is_deleted = True
                self.repos.assumption.update_assumption(assumption, proposal.created_by)
                proposal.applied_target_id = assumption.id

        proposal.applied_at = datetime.now(timezone.utc)
        self.repos.proposal.update_assumption_proposal(proposal)

    # ============================================================================
    # Criteria Proposal Methods
    # ============================================================================

    def create_criteria_proposal(
        self,
        event_id: UUID,
        request: CriteriaProposalCreateRequest,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> CriteriaProposalResponse:
        """
        기준 제안 생성
        - IN_PROGRESS 상태에서만 가능
        - ACCEPTED 멤버십 필요
        - 중복 제안 체크 (PENDING 상태만)
        """
        def _execute_create() -> dict:
            # 1. 이벤트 상태 검증 (IN_PROGRESS)
            event = self._validate_event_in_progress(event_id, "create proposals")

            # 2. 멤버십 검증 (ACCEPTED)
            self._validate_membership_accepted(user_id, event_id, "create proposals")

            # 3. proposal_category에 따른 필드 검증
            self._validate_criteria_proposal_category_fields(request, event_id)

            # 4. 중복 제안 체크 (PENDING 상태만)
            existing_proposal = self.repos.proposal.get_pending_criteria_proposal_by_user(
                event_id, request.criteria_id, user_id
            )
            if existing_proposal:
                raise ConflictError(
                    message="Duplicate proposal",
                    detail="You already have a pending proposal for this criterion"
                )

            # 5. 제안 생성
            proposal = CriteriaProposal(
                event_id=event_id,
                criteria_id=request.criteria_id,
                proposal_category=request.proposal_category,
                proposal_content=request.proposal_content,
                reason=request.reason,
                created_by=user_id,
                proposal_status=ProposalStatusType.PENDING,
            )
            with transaction(self.db):
                created_proposal = self.repos.proposal.create_criteria_proposal(proposal)
                # votes 관계를 로드하기 위해 refresh (재조회 대신)
                self.db.refresh(created_proposal, ['votes'])
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.created.v1",
                        payload={
                            "proposal_id": str(created_proposal.id),
                            "proposal_type": "criteria"
                        },
                        target_event_id=event_id
                    )
            vote_count = len(created_proposal.votes) if created_proposal.votes else 0
            has_voted = False  # 새로 생성된 제안이므로 투표 없음

            response = CriteriaProposalResponse(
                id=created_proposal.id,
                event_id=created_proposal.event_id,
                criteria_id=created_proposal.criteria_id,
                proposal_status=created_proposal.proposal_status,
                proposal_category=created_proposal.proposal_category,
                proposal_content=created_proposal.proposal_content,
                reason=created_proposal.reason,
                created_at=created_proposal.created_at,
                created_by=created_proposal.created_by,
                vote_count=vote_count,
                has_voted=has_voted,
            )
            return response.model_dump()
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="POST",
            path=f"/events/{event_id}/criteria-proposals",
            body=request.model_dump(exclude_none=True, mode='json'),
            fn=_execute_create
        )
        return CriteriaProposalResponse(**result)

    def create_criteria_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> CriteriaProposalVoteResponse:
        """
        기준 제안 투표 생성
        - IN_PROGRESS 상태에서만 가능
        - PENDING 제안에만 투표 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal or proposal.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def create_vote(pid, uid):
            vote = CriterionProposalVote(
                criterion_proposal_id=pid,
                created_by=uid,
            )
            created_vote = self.repos.proposal.create_criteria_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo:
                proposal = self.repos.proposal.get_criteria_proposal_by_id(pid)
                if proposal:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.vote.created.v1",
                        payload={
                            "proposal_id": str(pid),
                            "proposal_type": "criteria"
                        },
                        target_event_id=proposal.event_id
                    )
            
            return created_vote
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=event.criteria_min_votes_required,
                approval_threshold_percent=None,
                total_members=None,
                is_auto_approved=event.criteria_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_criteria_proposal_if_pending,
                apply_proposal_fn=self._apply_criteria_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "criteria",
                        "event_id": str(p.event_id),
                        "approved_by": None
                    },
                    target_event_id=p.event_id
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return CriteriaProposalVoteResponse(
                message="Vote created successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.create_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_criteria_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            check_duplicate_fn=self._check_duplicate_criteria_vote,
            create_vote_fn=create_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return CriteriaProposalVoteResponse(**result)

    def delete_criteria_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> CriteriaProposalVoteResponse:
        """
        기준 제안 투표 삭제
        - IN_PROGRESS 상태에서만 가능
        - 본인 투표만 삭제 가능
        - PENDING 제안에만 투표 삭제 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal or proposal.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def get_vote(pid, uid):
            vote = self.repos.proposal.get_user_vote_on_criteria_proposal(pid, uid)
            if not vote:
                raise NotFoundError(
                    message="Vote not found",
                    detail="You have not voted on this proposal"
                )
            return vote
        
        def delete_vote(vote):
            # Outbox 이벤트 추가를 위해 proposal 조회 (트랜잭션 내부)
            proposal = self.repos.proposal.get_criteria_proposal_by_id(vote.criterion_proposal_id)
            
            self.repos.proposal.delete_criteria_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo and proposal:
                self.outbox_repo.create_outbox_event(
                    event_type="proposal.vote.deleted.v1",
                    payload={
                        "proposal_id": str(vote.criterion_proposal_id),
                        "proposal_type": "criteria"
                    },
                    target_event_id=proposal.event_id
                )
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=event.criteria_min_votes_required,
                approval_threshold_percent=None,
                total_members=None,
                is_auto_approved=event.criteria_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_criteria_proposal_if_pending,
                apply_proposal_fn=self._apply_criteria_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "criteria",
                        "event_id": str(p.event_id),
                        "approved_by": None
                    },
                    target_event_id=p.event_id
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return CriteriaProposalVoteResponse(
                message="Vote deleted successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.delete_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_criteria_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            get_vote_fn=get_vote,
            delete_vote_fn=delete_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return CriteriaProposalVoteResponse(**result)

    def _validate_criteria_proposal_pending(
        self, proposal_id: UUID, event_id: UUID, operation: str
    ) -> CriteriaProposal:
        """기준 제안 존재 및 PENDING 상태 검증"""
        proposal = self.repos.proposal.get_criteria_proposal_by_id(proposal_id)
        if not proposal or proposal.event_id != event_id:
            raise NotFoundError(
                message="Proposal not found",
                detail=f"Proposal with id {proposal_id} not found for this event"
            )

        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(
                message="Proposal not pending",
                detail=f"{operation} can only be performed for PENDING proposals"
            )
        return proposal

    def _validate_criterion_for_proposal(
        self, criteria_id: UUID, event_id: UUID, proposal_category: ProposalCategoryType
    ) -> Criterion:
        """Criterion 존재, event_id 일치, 삭제 여부 검증"""
        criterion = self.repos.criterion.get_by_id(criteria_id)
        if not criterion or criterion.event_id != event_id:
            raise NotFoundError(
                message="Criterion not found",
                detail=f"Criterion with id {criteria_id} not found for this event"
            )
        if criterion.is_deleted:
            raise ValidationError(
                message="Criterion is deleted",
                detail="Criterion is already deleted"
            )
        return criterion

    def _validate_criteria_proposal_category_fields(
        self, request: CriteriaProposalCreateRequest, event_id: UUID
    ) -> None:
        """proposal_category에 따른 필드 검증 (proposal_content, criteria_id)"""
        if request.proposal_category == ProposalCategoryType.DELETION:
            if request.proposal_content is not None:
                raise ValidationError(
                    message="Invalid proposal_content",
                    detail="proposal_content must be NULL for DELETION proposals"
                )
        else:
            if request.proposal_content is None:
                raise ValidationError(
                    message="Missing proposal_content",
                    detail="proposal_content is required for CREATION/MODIFICATION proposals"
                )

        if request.proposal_category == ProposalCategoryType.CREATION:
            if request.criteria_id is not None:
                raise ValidationError(
                    message="Invalid criteria_id",
                    detail="criteria_id must be NULL for CREATION proposals"
                )
        else:
            if request.criteria_id is None:
                raise ValidationError(
                    message="Missing criteria_id",
                    detail=f"criteria_id is required for {request.proposal_category.value} proposals"
                )
            # criterion 존재 확인
            self._validate_criterion_for_proposal(
                request.criteria_id, event_id, request.proposal_category
            )

    def _check_duplicate_criteria_vote(self, proposal_id: UUID, user_id: UUID) -> None:
        """중복 투표 체크"""
        existing_vote = self.repos.proposal.get_user_vote_on_criteria_proposal(
            proposal_id, user_id
        )
        if existing_vote:
            raise ConflictError(
                message="Already voted",
                detail="You have already voted on this proposal"
            )

    def _get_user_criteria_vote_or_raise(
        self, proposal_id: UUID, user_id: UUID
    ) -> CriterionProposalVote:
        """투표 존재 검증"""
        vote = self.repos.proposal.get_user_vote_on_criteria_proposal(
            proposal_id, user_id
        )
        if not vote:
            raise NotFoundError(
                message="Vote not found",
                detail="You have not voted on this proposal"
            )
        return vote

    def _check_and_auto_approve_criteria_proposal(
        self, proposal: CriteriaProposal, event: Event
    ) -> None:
        """
        투표 수가 일정 수준 도달 시 자동 승인
        
        정책:
        - auto_approved, min_votes_required 설정은 PENDING 상태인 proposal에만 소급 적용
        - 이미 ACCEPTED, REJECTED된 proposal에는 반영되지 않음
        
        동작:
        - criteria_is_auto_approved_by_votes가 True일 때만 동작
        - criteria_min_votes_required 이상이면 ACCEPTED로 변경
        - 승인 시 자동으로 제안 적용 (apply_proposal 호출)
        - PENDING 상태인 proposal에만 적용 (이미 ACCEPTED/REJECTED된 것은 무시)
        """
        # PENDING 상태가 아니면 자동 승인 로직 적용하지 않음
        if proposal.proposal_status != ProposalStatusType.PENDING:
            return

        if not event.criteria_is_auto_approved_by_votes:
            return

        if event.criteria_min_votes_required is None:
            return

        vote_count = len(proposal.votes)
        if vote_count >= event.criteria_min_votes_required:
            # 조건부 UPDATE로 락 없이 중복 승인 방지
            accepted_at = datetime.now(timezone.utc)
            approved_proposal = self.repos.proposal.approve_criteria_proposal_if_pending(
                proposal.id, accepted_at
            )
            if approved_proposal:
                # 승인 성공 시 proposal을 다시 조회하여 관계 로드
                self.db.refresh(approved_proposal, ['votes', 'criterion'])
                # 자동 승인 시 즉시 적용
                self._apply_criteria_proposal(approved_proposal, event)
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.approved.v1",
                        payload={
                            "proposal_id": str(approved_proposal.id),
                            "proposal_type": "criteria",
                            "event_id": str(approved_proposal.event_id),
                            "approved_by": None  # 자동 승인
                        },
                        target_event_id=approved_proposal.event_id
                    )
                # commit은 외부 트랜잭션 매니저가 처리

    def _apply_criteria_proposal(
        self, proposal: CriteriaProposal, event: Event
    ) -> None:
        """
        제안을 실제 Criterion에 적용
        - CREATION: 새 Criterion 생성
        - MODIFICATION: 기존 Criterion 수정 (original_content 저장, is_modified=True)
        - DELETION: 기존 Criterion 소프트 삭제 (is_deleted=True)
        """
        if proposal.proposal_category == ProposalCategoryType.CREATION:
            # 새 기준 생성
            criterion = Criterion(
                event_id=proposal.event_id,
                content=proposal.proposal_content,
                created_by=proposal.created_by,
            )
            result = self.repos.criterion.create_criteria([criterion])
            proposal.applied_target_id = result[0].id
        elif proposal.proposal_category == ProposalCategoryType.MODIFICATION:
            # 기존 기준 수정
            criterion = self.repos.criterion.get_by_id(proposal.criteria_id)
            if criterion:
                criterion.original_content = criterion.content  # 원본 저장
                criterion.content = proposal.proposal_content
                criterion.is_modified = True
                self.repos.criterion.update_criterion(criterion, proposal.created_by)
                proposal.applied_target_id = criterion.id
        elif proposal.proposal_category == ProposalCategoryType.DELETION:
            # 소프트 삭제
            criterion = self.repos.criterion.get_by_id(proposal.criteria_id)
            if criterion:
                criterion.is_deleted = True
                self.repos.criterion.update_criterion(criterion, proposal.created_by)
                proposal.applied_target_id = criterion.id

        proposal.applied_at = datetime.now(timezone.utc)
        self.repos.proposal.update_criteria_proposal(proposal)

    # ============================================================================
    # Conclusion Proposal Methods
    # ============================================================================

    def create_conclusion_proposal(
        self,
        event_id: UUID,
        criterion_id: UUID,
        request: ConclusionProposalCreateRequest,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> ConclusionProposalResponse:
        """
        결론 제안 생성
        - IN_PROGRESS 상태에서만 가능
        - ACCEPTED 멤버십 필요
        - 중복 제안 체크 (PENDING 상태만)
        """
        def _execute_create() -> dict:
            # 1. 이벤트 상태 검증 (IN_PROGRESS)
            event = self._validate_event_in_progress(event_id, "create proposals")

            # 2. 멤버십 검증 (ACCEPTED)
            self._validate_membership_accepted(user_id, event_id, "create proposals")

            # 3. Criterion 존재 및 event_id 일치 검증
            criterion = self.repos.criterion.get_by_id(criterion_id)
            if not criterion or criterion.event_id != event_id:
                raise NotFoundError(
                    message="Criterion not found",
                    detail=f"Criterion with id {criterion_id} not found for this event"
                )

            # 4. 중복 제안 체크 (PENDING 상태만)
            existing_proposal = self.repos.proposal.get_pending_conclusion_proposal_by_user(
                criterion_id, user_id
            )
            if existing_proposal:
                raise ConflictError(
                    message="Duplicate proposal",
                    detail="You already have a pending proposal for this criterion"
                )

            # 5. 제안 생성
            proposal = ConclusionProposal(
                criterion_id=criterion_id,
                proposal_content=request.proposal_content,
                created_by=user_id,
                proposal_status=ProposalStatusType.PENDING,
            )
            with transaction(self.db):
                created_proposal = self.repos.proposal.create_conclusion_proposal(proposal)
                # votes 관계를 로드하기 위해 refresh
                self.db.refresh(created_proposal, ['votes'])
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.created.v1",
                        payload={
                            "proposal_id": str(created_proposal.id),
                            "proposal_type": "conclusion"
                        },
                        target_event_id=event_id
                    )
            vote_count = len(created_proposal.votes) if created_proposal.votes else 0
            has_voted = False  # 새로 생성된 제안이므로 투표 없음

            response = ConclusionProposalResponse(
                id=created_proposal.id,
                criterion_id=created_proposal.criterion_id,
                proposal_status=created_proposal.proposal_status,
                proposal_content=created_proposal.proposal_content,
                created_at=created_proposal.created_at,
                created_by=created_proposal.created_by,
                vote_count=vote_count,
                has_voted=has_voted,
            )
            return response.model_dump()
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="POST",
            path=f"/events/{event_id}/criteria/{criterion_id}/conclusion-proposals",
            body=request.model_dump(exclude_none=True, mode='json'),
            fn=_execute_create
        )
        return ConclusionProposalResponse(**result)

    def create_conclusion_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> ConclusionProposalVoteResponse:
        """
        결론 제안 투표 생성
        - IN_PROGRESS 상태에서만 가능
        - PENDING 제안에만 투표 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found"
                )
            # criterion을 통해 event_id 확인
            criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
            if not criterion or criterion.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def create_vote(pid, uid):
            vote = ConclusionProposalVote(
                conclusion_proposal_id=pid,
                created_by=uid,
            )
            created_vote = self.repos.proposal.create_conclusion_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo:
                proposal = self.repos.proposal.get_conclusion_proposal_by_id(pid)
                if proposal:
                    # conclusion proposal의 event_id는 criterion을 통해 조회
                    criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
                    if criterion:
                        self.outbox_repo.create_outbox_event(
                            event_type="proposal.vote.created.v1",
                            payload={
                                "proposal_id": str(pid),
                                "proposal_type": "conclusion"
                            },
                            target_event_id=criterion.event_id
                        )
            
            return created_vote
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            # 전체 ACCEPTED 멤버십 수 조회
            from app.models.event import EventMembership
            from sqlalchemy import func as sql_func, select
            stmt = (
                select(sql_func.count(EventMembership.id))
                .where(
                    EventMembership.event_id == event.id,
                    EventMembership.membership_status == MembershipStatusType.ACCEPTED
                )
            )
            result = self.db.execute(stmt)
            total_members = result.scalar() or 0
            
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=None,
                approval_threshold_percent=event.conclusion_approval_threshold_percent,
                total_members=total_members,
                is_auto_approved=event.conclusion_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_conclusion_proposal_if_pending,
                apply_proposal_fn=self._apply_conclusion_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "conclusion",
                        "event_id": str(criterion.event_id) if (criterion := self.repos.criterion.get_by_id(p.criterion_id)) else None,
                        "approved_by": None
                    },
                    target_event_id=criterion.event_id if (criterion := self.repos.criterion.get_by_id(p.criterion_id)) else None
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return ConclusionProposalVoteResponse(
                message="Vote created successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.create_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_conclusion_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            check_duplicate_fn=self._check_duplicate_conclusion_vote,
            create_vote_fn=create_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return ConclusionProposalVoteResponse(**result)

    def delete_conclusion_proposal_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID
    ) -> ConclusionProposalVoteResponse:
        """
        결론 제안 투표 삭제
        - IN_PROGRESS 상태에서만 가능
        - 본인 투표만 삭제 가능
        - PENDING 제안에만 투표 삭제 가능
        """
        def validate_proposal_pending(proposal, pid, eid, op):
            if not proposal:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found"
                )
            # criterion을 통해 event_id 확인
            criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
            if not criterion or criterion.event_id != eid:
                raise NotFoundError(
                    message="Proposal not found",
                    detail=f"Proposal with id {pid} not found for this event"
                )
            if proposal.proposal_status != ProposalStatusType.PENDING:
                raise ValidationError(
                    message="Proposal not pending",
                    detail=f"{op} can only be performed for PENDING proposals"
                )
        
        def get_vote(pid, uid):
            vote = self.repos.proposal.get_user_vote_on_conclusion_proposal(pid, uid)
            if not vote:
                raise NotFoundError(
                    message="Vote not found",
                    detail="You have not voted on this proposal"
                )
            return vote
        
        def delete_vote(vote):
            # Outbox 이벤트 추가를 위해 proposal 조회 (트랜잭션 내부)
            proposal = self.repos.proposal.get_conclusion_proposal_by_id(vote.conclusion_proposal_id)
            
            self.repos.proposal.delete_conclusion_proposal_vote(vote)
            
            # Outbox 이벤트 추가 (트랜잭션 내부)
            if self.outbox_repo and proposal:
                # conclusion proposal의 event_id는 criterion을 통해 조회
                criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
                if criterion:
                    self.outbox_repo.create_outbox_event(
                        event_type="proposal.vote.deleted.v1",
                        payload={
                            "proposal_id": str(vote.conclusion_proposal_id),
                            "proposal_type": "conclusion"
                        },
                        target_event_id=criterion.event_id
                    )
        
        def auto_approve(proposal, event):
            vote_count = len(proposal.votes) if proposal.votes else 0
            # 전체 ACCEPTED 멤버십 수 조회
            from app.models.event import EventMembership
            from sqlalchemy import func as sql_func, select
            stmt = (
                select(sql_func.count(EventMembership.id))
                .where(
                    EventMembership.event_id == event.id,
                    EventMembership.membership_status == MembershipStatusType.ACCEPTED
                )
            )
            result = self.db.execute(stmt)
            total_members = result.scalar() or 0
            
            self.auto_approval_checker.check_and_auto_approve(
                proposal=proposal,
                event=event,
                vote_count=vote_count,
                min_votes_required=None,
                approval_threshold_percent=event.conclusion_approval_threshold_percent,
                total_members=total_members,
                is_auto_approved=event.conclusion_is_auto_approved_by_votes,
                approve_if_pending_fn=self.repos.proposal.approve_conclusion_proposal_if_pending,
                apply_proposal_fn=self._apply_conclusion_proposal,
                create_outbox_event_fn=lambda p, e: self.outbox_repo.create_outbox_event(
                    event_type="proposal.approved.v1",
                    payload={
                        "proposal_id": str(p.id),
                        "proposal_type": "conclusion",
                        "event_id": str(criterion.event_id) if (criterion := self.repos.criterion.get_by_id(p.criterion_id)) else None,
                        "approved_by": None
                    },
                    target_event_id=criterion.event_id if (criterion := self.repos.criterion.get_by_id(p.criterion_id)) else None
                ) if self.outbox_repo else None,
            )
        
        def build_response(vote, proposal, vote_count):
            return ConclusionProposalVoteResponse(
                message="Vote deleted successfully",
                vote_id=vote.id,
                proposal_id=proposal_id,
                vote_count=vote_count,
            ).model_dump()
        
        result = self.vote_usecase.delete_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            validate_event_fn=self._validate_event_in_progress,
            get_proposal_fn=lambda pid, eid: self.repos.proposal.get_conclusion_proposal_by_id(pid),
            validate_proposal_pending_fn=validate_proposal_pending,
            get_vote_fn=get_vote,
            delete_vote_fn=delete_vote,
            auto_approve_fn=auto_approve,
            build_response_fn=build_response,
        )
        return ConclusionProposalVoteResponse(**result)

    def _validate_conclusion_proposal_pending(
        self, proposal_id: UUID, event_id: UUID, operation: str
    ) -> ConclusionProposal:
        """결론 제안 존재 및 PENDING 상태 검증"""
        proposal = self.repos.proposal.get_conclusion_proposal_by_id(proposal_id)
        if not proposal:
            raise NotFoundError(
                message="Proposal not found",
                detail=f"Proposal with id {proposal_id} not found"
            )

        # criterion을 통해 event_id 확인
        criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
        if not criterion or criterion.event_id != event_id:
            raise NotFoundError(
                message="Proposal not found",
                detail=f"Proposal with id {proposal_id} not found for this event"
            )

        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(
                message="Proposal not pending",
                detail=f"{operation} can only be performed for PENDING proposals"
            )
        return proposal

    def _check_duplicate_conclusion_vote(self, proposal_id: UUID, user_id: UUID) -> None:
        """중복 투표 체크"""
        existing_vote = self.repos.proposal.get_user_vote_on_conclusion_proposal(
            proposal_id, user_id
        )
        if existing_vote:
            raise ConflictError(
                message="Already voted",
                detail="You have already voted on this proposal"
            )

    def _get_user_conclusion_vote_or_raise(
        self, proposal_id: UUID, user_id: UUID
    ) -> ConclusionProposalVote:
        """투표 존재 검증"""
        vote = self.repos.proposal.get_user_vote_on_conclusion_proposal(
            proposal_id, user_id
        )
        if not vote:
            raise NotFoundError(
                message="Vote not found",
                detail="You have not voted on this proposal"
            )
        return vote

    def _check_and_auto_approve_conclusion_proposal(
        self, proposal: ConclusionProposal, event: Event
    ) -> None:
        """
        투표 비율이 일정 수준 도달 시 자동 승인
        
        정책:
        - conclusion_is_auto_approved_by_votes가 True일 때만 동작
        - conclusion_approval_threshold_percent 이상이면 ACCEPTED로 변경
        - 승인 시 자동으로 제안 적용 (apply_proposal 호출)
        - PENDING 상태인 proposal에만 적용
        """
        # PENDING 상태가 아니면 자동 승인 로직 적용하지 않음
        if proposal.proposal_status != ProposalStatusType.PENDING:
            return

        if not event.conclusion_is_auto_approved_by_votes:
            return

        if event.conclusion_approval_threshold_percent is None:
            return

        # 전체 ACCEPTED 멤버십 수 조회
        from app.models.event import EventMembership
        from sqlalchemy import func as sql_func, select
        stmt = (
            select(sql_func.count(EventMembership.id))
            .where(
                EventMembership.event_id == event.id,
                EventMembership.membership_status == MembershipStatusType.ACCEPTED
            )
        )
        result = self.db.execute(stmt)
        total_members = result.scalar() or 0

        if total_members == 0:
            return  # 멤버가 없으면 승인 불가

        vote_count = len(proposal.votes)
        vote_percent = (vote_count / total_members) * 100

        if vote_percent >= event.conclusion_approval_threshold_percent:
            # 조건부 UPDATE로 락 없이 중복 승인 방지
            accepted_at = datetime.now(timezone.utc)
            approved_proposal = self.repos.proposal.approve_conclusion_proposal_if_pending(
                proposal.id, accepted_at
            )
            if approved_proposal:
                # 승인 성공 시 proposal을 다시 조회하여 관계 로드
                self.db.refresh(approved_proposal, ['votes', 'criterion'])
                # 자동 승인 시 즉시 적용
                self._apply_conclusion_proposal(approved_proposal, event)
                
                # Outbox 이벤트 추가 (트랜잭션 내부)
                if self.outbox_repo:
                    # event_id는 criterion을 통해 조회
                    criterion = self.repos.criterion.get_by_id(approved_proposal.criterion_id)
                    if criterion:
                        self.outbox_repo.create_outbox_event(
                            event_type="proposal.approved.v1",
                            payload={
                                "proposal_id": str(approved_proposal.id),
                                "proposal_type": "conclusion",
                                "event_id": str(criterion.event_id),
                                "approved_by": None  # 자동 승인
                            },
                            target_event_id=criterion.event_id
                        )
                # commit은 외부 트랜잭션 매니저가 처리

    def _apply_conclusion_proposal(
        self, proposal: ConclusionProposal, event: Event
    ) -> None:
        """
        제안을 실제 Criterion의 conclusion에 적용
        """
        criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
        if criterion:
            criterion.conclusion = proposal.proposal_content
            self.repos.criterion.update_criterion(criterion, proposal.created_by)

        proposal.applied_at = datetime.now(timezone.utc)
        self.repos.proposal.update_conclusion_proposal(proposal)

    # ============================================================================
    # Admin Proposal Status Update Methods
    # ============================================================================

    def update_assumption_proposal_status(
        self,
        event_id: UUID,
        proposal_id: UUID,
        status: ProposalStatusType,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> AssumptionProposalResponse:
        """
        전제 제안 상태 변경 (관리자용)
        - 관리자 권한 확인
        - PENDING 상태만 변경 가능
        - ACCEPTED 시 제안 적용
        """
        def _execute_update() -> dict:
            def validate_proposal_belongs_to_event(proposal, eid):
                if proposal.event_id != eid:
                    raise NotFoundError(
                        message="Proposal not found",
                        detail="Proposal does not belong to this event"
                    )

            def create_outbox_event(proposal, event, st):
                if self.outbox_repo:
                    event_type = "proposal.approved.v1" if st == ProposalStatusType.ACCEPTED else "proposal.rejected.v1"
                    key = "approved_by" if st == ProposalStatusType.ACCEPTED else "rejected_by"
                    payload = {
                        "proposal_id": str(proposal.id),
                        "proposal_type": "assumption",
                        "event_id": str(proposal.event_id),
                        key: str(user_id)
                    }
                    self.outbox_repo.create_outbox_event(event_type=event_type, payload=payload, target_event_id=proposal.event_id)
            
            def build_response(proposal, uid):
                vote_count = len(proposal.votes) if proposal.votes else 0
                has_voted = any(vote.created_by == uid for vote in (proposal.votes or []))
                return AssumptionProposalResponse(
                    id=proposal.id,
                    event_id=proposal.event_id,
                    assumption_id=proposal.assumption_id,
                    proposal_status=proposal.proposal_status,
                    proposal_category=proposal.proposal_category,
                    proposal_content=proposal.proposal_content,
                    reason=proposal.reason,
                    created_at=proposal.created_at,
                    created_by=proposal.created_by,
                    vote_count=vote_count,
                    has_voted=has_voted
                ).model_dump()
            
            return self.approval_usecase.update_status(
                event_id=event_id,
                proposal_id=proposal_id,
                status=status,
                user_id=user_id,
                verify_admin_fn=self.verify_admin,
                get_proposal_fn=lambda pid: self.repos.proposal.get_assumption_proposal_by_id(pid),
                validate_proposal_belongs_to_event_fn=validate_proposal_belongs_to_event,
                approve_if_pending_fn=self.repos.proposal.approve_assumption_proposal_if_pending,
                reject_if_pending_fn=self.repos.proposal.reject_assumption_proposal_if_pending,
                apply_proposal_fn=self._apply_assumption_proposal,
                build_response_fn=build_response,
                create_outbox_event_fn=create_outbox_event,
            )
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="PATCH",
            path=f"/events/{event_id}/assumption-proposals/{proposal_id}/status",
            body={"status": status.value},
            fn=_execute_update
        )
        return AssumptionProposalResponse(**result)

    def update_criteria_proposal_status(
        self,
        event_id: UUID,
        proposal_id: UUID,
        status: ProposalStatusType,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> CriteriaProposalResponse:
        """
        기준 제안 상태 변경 (관리자용)
        - 관리자 권한 확인
        - PENDING 상태만 변경 가능
        - ACCEPTED 시 제안 적용
        """
        def _execute_update() -> dict:
            def validate_proposal_belongs_to_event(proposal, eid):
                if proposal.event_id != eid:
                    raise NotFoundError(
                        message="Proposal not found",
                        detail="Proposal does not belong to this event"
                    )

            def create_outbox_event(proposal, event, st):
                if self.outbox_repo:
                    event_type = "proposal.approved.v1" if st == ProposalStatusType.ACCEPTED else "proposal.rejected.v1"
                    key = "approved_by" if st == ProposalStatusType.ACCEPTED else "rejected_by"
                    payload = {
                        "proposal_id": str(proposal.id),
                        "proposal_type": "criteria",
                        "event_id": str(proposal.event_id),
                        key: str(user_id)
                    }
                    self.outbox_repo.create_outbox_event(event_type=event_type, payload=payload, target_event_id=proposal.event_id)
            
            def build_response(proposal, uid):
                vote_count = len(proposal.votes) if proposal.votes else 0
                has_voted = any(vote.created_by == uid for vote in (proposal.votes or []))
                return CriteriaProposalResponse(
                    id=proposal.id,
                    event_id=proposal.event_id,
                    criteria_id=proposal.criteria_id,
                    proposal_status=proposal.proposal_status,
                    proposal_category=proposal.proposal_category,
                    proposal_content=proposal.proposal_content,
                    reason=proposal.reason,
                    created_at=proposal.created_at,
                    created_by=proposal.created_by,
                    vote_count=vote_count,
                    has_voted=has_voted
                ).model_dump()
            
            return self.approval_usecase.update_status(
                event_id=event_id,
                proposal_id=proposal_id,
                status=status,
                user_id=user_id,
                verify_admin_fn=self.verify_admin,
                get_proposal_fn=lambda pid: self.repos.proposal.get_criteria_proposal_by_id(pid),
                validate_proposal_belongs_to_event_fn=validate_proposal_belongs_to_event,
                approve_if_pending_fn=self.repos.proposal.approve_criteria_proposal_if_pending,
                reject_if_pending_fn=self.repos.proposal.reject_criteria_proposal_if_pending,
                apply_proposal_fn=self._apply_criteria_proposal,
                build_response_fn=build_response,
                create_outbox_event_fn=create_outbox_event,
            )
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="PATCH",
            path=f"/events/{event_id}/criteria-proposals/{proposal_id}/status",
            body={"status": status.value},
            fn=_execute_update
        )
        return CriteriaProposalResponse(**result)

    def update_conclusion_proposal_status(
        self,
        event_id: UUID,
        proposal_id: UUID,
        status: ProposalStatusType,
        user_id: UUID,
        idempotency_key: str | None = None
    ) -> ConclusionProposalResponse:
        """
        결론 제안 상태 변경 (관리자용)
        - 관리자 권한 확인
        - PENDING 상태만 변경 가능
        - ACCEPTED 시 제안 적용
        """
        def _execute_update() -> dict:
            def validate_proposal_belongs_to_event(proposal, eid):
                # criterion을 통해 event_id 확인
                criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
                if not criterion or criterion.event_id != eid:
                    raise NotFoundError(
                        message="Proposal not found",
                        detail="Proposal does not belong to this event"
                    )

            def create_outbox_event(proposal, event, st):
                if self.outbox_repo:
                    event_type = "proposal.approved.v1" if st == ProposalStatusType.ACCEPTED else "proposal.rejected.v1"
                    key = "approved_by" if st == ProposalStatusType.ACCEPTED else "rejected_by"
                    criterion = self.repos.criterion.get_by_id(proposal.criterion_id)
                    payload = {
                        "proposal_id": str(proposal.id),
                        "proposal_type": "conclusion",
                        "event_id": str(criterion.event_id) if criterion else None,
                        key: str(user_id)
                    }
                    self.outbox_repo.create_outbox_event(event_type=event_type, payload=payload, target_event_id=criterion.event_id if criterion else None)
            
            def build_response(proposal, uid):
                vote_count = len(proposal.votes) if proposal.votes else 0
                has_voted = any(vote.created_by == uid for vote in (proposal.votes or []))
                return ConclusionProposalResponse(
                    id=proposal.id,
                    criterion_id=proposal.criterion_id,
                    proposal_status=proposal.proposal_status,
                    proposal_content=proposal.proposal_content,
                    created_at=proposal.created_at,
                    created_by=proposal.created_by,
                    vote_count=vote_count,
                    has_voted=has_voted
                ).model_dump()
            
            return self.approval_usecase.update_status(
                event_id=event_id,
                proposal_id=proposal_id,
                status=status,
                user_id=user_id,
                verify_admin_fn=self.verify_admin,
                get_proposal_fn=lambda pid: self.repos.proposal.get_conclusion_proposal_by_id(pid),
                validate_proposal_belongs_to_event_fn=validate_proposal_belongs_to_event,
                approve_if_pending_fn=self.repos.proposal.approve_conclusion_proposal_if_pending,
                reject_if_pending_fn=self.repos.proposal.reject_conclusion_proposal_if_pending,
                apply_proposal_fn=self._apply_conclusion_proposal,
                build_response_fn=build_response,
                create_outbox_event_fn=create_outbox_event,
            )
        
        # Idempotency 적용
        result = self.idempotency_wrapper.wrap(
            idempotency_key=idempotency_key,
            user_id=user_id,
            method="PATCH",
            path=f"/events/{event_id}/conclusion-proposals/{proposal_id}/status",
            body={"status": status.value},
            fn=_execute_update
        )
        return ConclusionProposalResponse(**result)
