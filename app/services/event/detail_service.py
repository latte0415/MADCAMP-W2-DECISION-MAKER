from datetime import datetime
from uuid import UUID

from app.models.event import MembershipStatusType
from app.models.proposal import ProposalCategoryType, ProposalStatusType
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
        self._validate_membership_accepted(user_id, event_id, "view event details")
        
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
        
        # N+1 쿼리 방지: 모든 assumption proposal에 대한 사용자 투표를 한 번에 조회
        assumption_proposal_ids = [p.id for p in assumption_proposals]
        user_votes_on_assumptions = self.repos.proposal.get_user_votes_on_assumption_proposals(
            assumption_proposal_ids, user_id
        )
        
        for proposal in assumption_proposals:
            # 투표 정보 조회 (이미 로드된 votes 사용)
            vote_count = len(proposal.votes)
            has_voted = proposal.id in user_votes_on_assumptions
            
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
        
        # N+1 쿼리 방지: 모든 criteria proposal에 대한 사용자 투표를 한 번에 조회
        criteria_proposal_ids = [p.id for p in criteria_proposals]
        user_votes_on_criteria = self.repos.proposal.get_user_votes_on_criteria_proposals(
            criteria_proposal_ids, user_id
        )
        
        for proposal in criteria_proposals:
            # 투표 정보 조회 (이미 로드된 votes 사용)
            vote_count = len(proposal.votes)
            has_voted = proposal.id in user_votes_on_criteria
            
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
        
        # applied_at 정보를 미리 딕셔너리로 매핑 (O(N*M) -> O(N+M))
        assumption_applied_at_map: dict[UUID, dict[str, datetime]] = {}
        for prop in assumption_proposals:
            if (prop.assumption_id and
                prop.proposal_status == ProposalStatusType.ACCEPTED and
                prop.applied_at is not None):
                if prop.assumption_id not in assumption_applied_at_map:
                    assumption_applied_at_map[prop.assumption_id] = {}
                # 삭제와 수정은 별도로 처리 (둘 다 있을 수 있음)
                # 실제로는 하나만 적용되지만, 안전하게 처리
                if prop.proposal_category == ProposalCategoryType.DELETION:
                    assumption_applied_at_map[prop.assumption_id]['deleted_at'] = prop.applied_at
                elif prop.proposal_category == ProposalCategoryType.MODIFICATION:
                    assumption_applied_at_map[prop.assumption_id]['modified_at'] = prop.applied_at
        
        # 전제 목록 구성
        assumptions_with_proposals = []
        for assumption in event.assumptions:
            proposals = assumption_proposals_by_id.get(assumption.id, [])
            # 제안이 적용된 경우 applied_at 정보 찾기 (딕셔너리에서 조회)
            applied_info = assumption_applied_at_map.get(assumption.id, {})
            modified_at = applied_info.get('modified_at')
            deleted_at = applied_info.get('deleted_at')
            
            assumptions_with_proposals.append(
                AssumptionWithProposals(
                    id=assumption.id,
                    content=assumption.content,
                    is_deleted=assumption.is_deleted,
                    is_modified=assumption.is_modified,
                    original_content=assumption.original_content,
                    modified_at=modified_at,
                    deleted_at=deleted_at,
                    proposals=proposals
                )
            )
        
        # 모든 기준의 결론 제안을 한 번에 조회 (N+1 방지)
        criterion_ids = [c.id for c in event.criteria]
        all_conclusion_proposals = []
        conclusion_proposals_by_criterion: dict[UUID, list] = {}
        for criterion_id in criterion_ids:
            conclusion_proposals_raw = self.repos.proposal.get_conclusion_proposals_by_criterion_id(
                criterion_id, user_id
            )
            conclusion_proposals_by_criterion[criterion_id] = conclusion_proposals_raw
            all_conclusion_proposals.extend(conclusion_proposals_raw)
        
        # 모든 결론 제안에 대한 사용자 투표를 한 번에 조회
        conclusion_proposal_ids = [cp.id for cp in all_conclusion_proposals]
        user_votes_on_conclusions = self.repos.proposal.get_user_votes_on_conclusion_proposals(
            conclusion_proposal_ids, user_id
        )
        
        # applied_at 정보를 미리 딕셔너리로 매핑
        criteria_applied_at_map: dict[UUID, dict[str, datetime]] = {}
        for prop in criteria_proposals:
            if (prop.criteria_id and
                prop.proposal_status == ProposalStatusType.ACCEPTED and
                prop.applied_at is not None):
                if prop.criteria_id not in criteria_applied_at_map:
                    criteria_applied_at_map[prop.criteria_id] = {}
                if prop.proposal_category == ProposalCategoryType.DELETION:
                    criteria_applied_at_map[prop.criteria_id]['deleted_at'] = prop.applied_at
                elif prop.proposal_category == ProposalCategoryType.MODIFICATION:
                    criteria_applied_at_map[prop.criteria_id]['modified_at'] = prop.applied_at
        
        # 기준 목록 구성 (결론 제안 포함)
        criteria_with_proposals = []
        for criterion in event.criteria:
            proposals = criteria_proposals_by_id.get(criterion.id, [])
            
            # 결론 제안 조회 (이미 조회된 데이터 사용)
            conclusion_proposals_raw = conclusion_proposals_by_criterion.get(criterion.id, [])
            conclusion_proposals = []
            for cp in conclusion_proposals_raw:
                vote_count = len(cp.votes)
                has_voted = cp.id in user_votes_on_conclusions
                
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
            
            # 제안이 적용된 경우 applied_at 정보 찾기 (딕셔너리에서 조회)
            applied_info = criteria_applied_at_map.get(criterion.id, {})
            modified_at = applied_info.get('modified_at')
            deleted_at = applied_info.get('deleted_at')
            
            criteria_with_proposals.append(
                CriterionWithProposals(
                    id=criterion.id,
                    content=criterion.content,
                    conclusion=criterion.conclusion,
                    is_deleted=criterion.is_deleted,
                    is_modified=criterion.is_modified,
                    original_content=criterion.original_content,
                    modified_at=modified_at,
                    deleted_at=deleted_at,
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
