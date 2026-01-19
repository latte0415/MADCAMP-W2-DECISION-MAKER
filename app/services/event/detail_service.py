from uuid import UUID

from app.models.event import MembershipStatusType
from app.models.proposal import ProposalCategoryType
from app.services.event.base import EventBaseService
from app.schemas.event import (
    EventDetailResponse,
    AssumptionProposalInfo,
    CriteriaProposalInfo,
    ConclusionProposalInfo,
    AssumptionWithProposals,
    CriterionWithProposals,
    ProposalVoteInfo,
    OptionInfo,
)
from app.exceptions import NotFoundError, ForbiddenError


class EventDetailService(EventBaseService):
    """Event (4-0-0) 관련 서비스"""
    
    def get_event_detail(
        self,
        event_id: UUID,
        user_id: UUID
    ) -> EventDetailResponse:
        """
        이벤트 상세 조회 (Event 4-0-0 페이지용)
        - 주제, 선택지, 전제, 기준, 각각에 대한 제안 조회
        - 각 제안에 대한 투표 정보 포함
        """
        # 이벤트 조회 (options, assumptions, criteria, admin 조인) - base 메서드 사용
        event = self.get_event_with_all_relations(event_id)
        
        # 멤버십 확인 (ACCEPTED 상태인지 확인)
        membership_status = self.repos.event.get_membership_status(user_id, event_id)
        if membership_status != MembershipStatusType.ACCEPTED:
            raise ForbiddenError(
                message="Forbidden",
                detail="Only accepted members can view event details"
            )
        
        # 관리자 여부 확인
        is_admin = event.admin_id == user_id
        
        # 전제 제안 목록 조회
        assumption_proposals = self.repos.proposal.get_assumption_proposals_by_event_id(
            event_id, user_id
        )
        
        # 기준 제안 목록 조회
        criteria_proposals = self.repos.proposal.get_criteria_proposals_by_event_id(
            event_id, user_id
        )
        
        # 전제별 제안 그룹화
        assumption_proposals_by_id: dict[UUID | None, list] = {}
        assumption_creation_proposals = []
        
        for proposal in assumption_proposals:
            # 투표 정보 조회
            vote_count = len(proposal.votes)
            user_vote = self.repos.proposal.get_user_vote_on_assumption_proposal(
                proposal.id, user_id
            )
            has_voted = user_vote is not None
            
            proposal_info = AssumptionProposalInfo(
                id=proposal.id,
                assumption_id=proposal.assumption_id,
                proposal_status=proposal.proposal_status,
                proposal_category=proposal.proposal_category,
                proposal_content=proposal.proposal_content,
                reason=proposal.reason,
                created_at=proposal.created_at,
                created_by=proposal.created_by,
                creator_email=proposal.creator.email if proposal.creator else None,
                vote_info=ProposalVoteInfo(
                    vote_count=vote_count,
                    has_voted=has_voted
                )
            )
            
            if proposal.proposal_category == ProposalCategoryType.CREATION:
                assumption_creation_proposals.append(proposal_info)
            else:
                assumption_id = proposal.assumption_id
                if assumption_id not in assumption_proposals_by_id:
                    assumption_proposals_by_id[assumption_id] = []
                assumption_proposals_by_id[assumption_id].append(proposal_info)
        
        # 기준별 제안 그룹화 및 결론 제안 조회
        criteria_proposals_by_id: dict[UUID | None, list] = {}
        criteria_creation_proposals = []
        
        for proposal in criteria_proposals:
            # 투표 정보 조회
            vote_count = len(proposal.votes)
            user_vote = self.repos.proposal.get_user_vote_on_criteria_proposal(
                proposal.id, user_id
            )
            has_voted = user_vote is not None
            
            proposal_info = CriteriaProposalInfo(
                id=proposal.id,
                criteria_id=proposal.criteria_id,
                proposal_status=proposal.proposal_status,
                proposal_category=proposal.proposal_category,
                proposal_content=proposal.proposal_content,
                reason=proposal.reason,
                created_at=proposal.created_at,
                created_by=proposal.created_by,
                creator_email=proposal.creator.email if proposal.creator else None,
                vote_info=ProposalVoteInfo(
                    vote_count=vote_count,
                    has_voted=has_voted
                )
            )
            
            if proposal.proposal_category == ProposalCategoryType.CREATION:
                criteria_creation_proposals.append(proposal_info)
            else:
                criteria_id = proposal.criteria_id
                if criteria_id not in criteria_proposals_by_id:
                    criteria_proposals_by_id[criteria_id] = []
                criteria_proposals_by_id[criteria_id].append(proposal_info)
        
        # 전제 목록 구성
        assumptions_with_proposals = []
        for assumption in event.assumptions:
            proposals = assumption_proposals_by_id.get(assumption.id, [])
            assumptions_with_proposals.append(
                AssumptionWithProposals(
                    id=assumption.id,
                    content=assumption.content,
                    proposals=proposals
                )
            )
        
        # 기준 목록 구성 (결론 제안 포함)
        criteria_with_proposals = []
        for criterion in event.criteria:
            proposals = criteria_proposals_by_id.get(criterion.id, [])
            
            # 결론 제안 조회
            conclusion_proposals_raw = self.repos.proposal.get_conclusion_proposals_by_criterion_id(
                criterion.id, user_id
            )
            conclusion_proposals = []
            for cp in conclusion_proposals_raw:
                vote_count = len(cp.votes)
                user_vote = self.repos.proposal.get_user_vote_on_conclusion_proposal(
                    cp.id, user_id
                )
                has_voted = user_vote is not None
                
                conclusion_proposals.append(
                    ConclusionProposalInfo(
                        id=cp.id,
                        criterion_id=cp.criterion_id,
                        proposal_status=cp.proposal_status,
                        proposal_content=cp.proposal_content,
                        created_at=cp.created_at,
                        created_by=cp.created_by,
                        creator_email=cp.creator.email if cp.creator else None,
                        vote_info=ProposalVoteInfo(
                            vote_count=vote_count,
                            has_voted=has_voted
                        )
                    )
                )
            
            criteria_with_proposals.append(
                CriterionWithProposals(
                    id=criterion.id,
                    content=criterion.content,
                    conclusion=criterion.conclusion,
                    proposals=proposals,
                    conclusion_proposals=conclusion_proposals
                )
            )
        
        return EventDetailResponse(
            id=event.id,
            decision_subject=event.decision_subject,
            event_status=event.event_status,
            is_admin=is_admin,
            options=[
                OptionInfo(id=option.id, content=option.content)
                for option in event.options
            ],
            assumptions=assumptions_with_proposals,
            criteria=criteria_with_proposals,
            assumption_creation_proposals=assumption_creation_proposals,
            criteria_creation_proposals=criteria_creation_proposals,
        )
