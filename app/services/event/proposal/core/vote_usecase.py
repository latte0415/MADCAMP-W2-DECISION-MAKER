"""투표 생성/삭제 공통 로직"""
from typing import Callable, TypeVar, Protocol
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.proposal import ProposalStatusType
from app.exceptions import ValidationError
from app.utils.transaction import transaction

# TypeVar 정의
TProposal = TypeVar('TProposal')
TVote = TypeVar('TVote')


class VoteUseCase:
    """투표 생성/삭제 공통 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID,
        # 타입별 의존성 주입
        validate_event_fn: Callable[[UUID, str], Event],
        get_proposal_fn: Callable[[UUID, UUID], TProposal],
        validate_proposal_pending_fn: Callable[[TProposal, UUID, UUID, str], None],
        check_duplicate_fn: Callable[[UUID, UUID], None],
        create_vote_fn: Callable[[UUID, UUID], TVote],  # (proposal_id, user_id) -> vote
        auto_approve_fn: Callable[[TProposal, Event], None],
        build_response_fn: Callable[[TVote, TProposal, int], dict],
    ) -> dict:
        """
        투표 생성 공통 로직
        
        Args:
            validate_event_fn: 이벤트 상태 검증 함수 (IN_PROGRESS)
            get_proposal_fn: proposal 조회 함수 (타입별)
            validate_proposal_pending_fn: proposal PENDING 상태 검증 함수
            check_duplicate_fn: 중복 투표 체크 함수 (타입별)
            create_vote_fn: vote 생성 함수 (repository, 타입별)
            auto_approve_fn: 자동 승인 체크 함수 (타입별)
            build_response_fn: 응답 생성 함수 (타입별)
        """
        # 1. 이벤트 상태 검증 (IN_PROGRESS)
        event = validate_event_fn(event_id, "create votes")
        
        # 2. 제안 존재 및 상태 검증
        proposal = get_proposal_fn(proposal_id, event_id)
        validate_proposal_pending_fn(proposal, proposal_id, event_id, "create votes")
        
        # 3. 중복 투표 체크
        check_duplicate_fn(proposal_id, user_id)
        
        # 4. 투표 생성 및 자동 승인 체크
        with transaction(self.db):
            # create_vote_fn은 (proposal_id, user_id)를 받아서 vote 객체를 생성하고 저장하는 함수
            # 타입별 서비스에서 vote 모델 클래스를 사용하여 생성
            created_vote = create_vote_fn(proposal_id, user_id)
            # votes 관계를 로드하기 위해 refresh
            self.db.refresh(proposal, ['votes'])
            vote_count = len(proposal.votes) if proposal.votes else 0
            
            # 자동 승인 로직 체크 (PENDING 상태인 proposal에만)
            auto_approve_fn(proposal, event)
        
        # refresh 후 vote_count 다시 계산 (자동 승인 후 vote_count 변경 가능)
        self.db.refresh(proposal, ['votes'])
        vote_count = len(proposal.votes) if proposal.votes else 0
        
        return build_response_fn(created_vote, proposal, vote_count)
    
    def delete_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID,
        # 타입별 의존성 주입
        validate_event_fn: Callable[[UUID, str], Event],
        get_proposal_fn: Callable[[UUID, UUID], TProposal],
        validate_proposal_pending_fn: Callable[[TProposal, UUID, UUID, str], None],
        get_vote_fn: Callable[[UUID, UUID], TVote],
        delete_vote_fn: Callable[[TVote], None],
        auto_approve_fn: Callable[[TProposal, Event], None],
        build_response_fn: Callable[[TVote, TProposal, int], dict],
    ) -> dict:
        """
        투표 삭제 공통 로직
        
        Args:
            validate_event_fn: 이벤트 상태 검증 함수 (IN_PROGRESS)
            get_proposal_fn: proposal 조회 함수 (타입별)
            validate_proposal_pending_fn: proposal PENDING 상태 검증 함수
            get_vote_fn: vote 조회 함수 (타입별)
            delete_vote_fn: vote 삭제 함수 (repository, 타입별)
            auto_approve_fn: 자동 승인 체크 함수 (타입별)
            build_response_fn: 응답 생성 함수 (타입별)
        """
        # 1. 이벤트 상태 검증 (IN_PROGRESS)
        event = validate_event_fn(event_id, "delete votes")
        
        # 2. 제안 존재 및 상태 검증
        proposal = get_proposal_fn(proposal_id, event_id)
        validate_proposal_pending_fn(proposal, proposal_id, event_id, "delete votes")
        
        # 3. 투표 존재 및 소유권 검증
        vote = get_vote_fn(proposal_id, user_id)
        
        # 4. 투표 삭제 및 자동 승인 재체크
        with transaction(self.db):
            delete_vote_fn(vote)
            # votes 관계를 로드하기 위해 refresh
            self.db.refresh(proposal, ['votes'])
            vote_count = len(proposal.votes) if proposal.votes else 0
            
            # 자동 승인 로직 재체크 (투표 수 감소 시, PENDING 상태인 proposal에만)
            auto_approve_fn(proposal, event)
        
        # refresh 후 vote_count 다시 계산
        self.db.refresh(proposal, ['votes'])
        vote_count = len(proposal.votes) if proposal.votes else 0
        
        return build_response_fn(vote, proposal, vote_count)
