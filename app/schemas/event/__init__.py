"""
Event 관련 스키마 모듈
기존 코드 호환성을 위한 통합 export
"""
# Common schemas
from app.schemas.event.common import OptionInfo, AdminInfo

# Home schemas
from app.schemas.event.home import EventListItemResponse

# Creation schemas
from app.schemas.event.creation import (
    EventCreateRequest,
    OptionAttachRequest,
    AssumptionAttachRequest,
    CriterionAttachRequest,
    EntranceCodeCheckRequest,
    EntranceCodeCheckResponse,
    EntranceCodeGenerateResponse,
    EventResponse,
)

# Overview schemas
from app.schemas.event.overview import (
    EntranceCodeEntryRequest,
    EventEntryResponse,
    EventOverviewResponse,
)

# Detail schemas
from app.schemas.event.detail import (
    EventDetailResponse,
    AssumptionProposalInfo,
    CriteriaProposalInfo,
    ConclusionProposalInfo,
    AssumptionWithProposals,
    CriterionWithProposals,
    ProposalVoteInfo,
)

# Proposal schemas
from app.schemas.event.proposal import (
    AssumptionProposalCreateRequest,
    AssumptionProposalResponse,
    AssumptionProposalVoteResponse,
    CriteriaProposalCreateRequest,
    CriteriaProposalResponse,
    CriteriaProposalVoteResponse,
    ConclusionProposalCreateRequest,
    ConclusionProposalResponse,
    ConclusionProposalVoteResponse,
    ProposalStatusUpdateRequest,
)

# Setting schemas
from app.schemas.event.setting import (
    EventSettingResponse,
    EventUpdateRequest,
    EventStatusUpdateRequest,
    EventStatusUpdateResponse,
    OptionUpdateItem,
    AssumptionUpdateItem,
    CriterionUpdateItem,
    AssumptionInfo,
    CriterionInfo,
)

# Membership schemas
from app.schemas.event.membership import (
    MembershipResponse,
    BulkMembershipResponse,
    MembershipListItemResponse,
)

# Comment schemas
from app.schemas.event.comment import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentResponse,
    CommentCountResponse,
    CommentCreatorInfo,
)

# Vote schemas
from app.schemas.event.vote import (
    VoteCreateRequest,
    VoteResponse,
    VoteViewResponse,
    VoteResultResponse,
    OptionVoteCount,
    CriterionRankInfo,
)

__all__ = [
    # Common
    "OptionInfo",
    "AdminInfo",
    # Home
    "EventListItemResponse",
    # Creation
    "EventCreateRequest",
    "OptionAttachRequest",
    "AssumptionAttachRequest",
    "CriterionAttachRequest",
    "EntranceCodeCheckRequest",
    "EntranceCodeCheckResponse",
    "EntranceCodeGenerateResponse",
    "EventResponse",
    # Overview
    "EntranceCodeEntryRequest",
    "EventEntryResponse",
    "EventOverviewResponse",
    # Detail
    "EventDetailResponse",
    "AssumptionProposalInfo",
    "CriteriaProposalInfo",
    "ConclusionProposalInfo",
    "AssumptionWithProposals",
    "CriterionWithProposals",
    "ProposalVoteInfo",
    # Setting
    "EventSettingResponse",
    "EventUpdateRequest",
    "OptionUpdateItem",
    "AssumptionUpdateItem",
    "CriterionUpdateItem",
    "AssumptionInfo",
    "CriterionInfo",
    # Membership
    "MembershipResponse",
    "BulkMembershipResponse",
    "MembershipListItemResponse",
    # Proposal
    "AssumptionProposalCreateRequest",
    "AssumptionProposalResponse",
    "AssumptionProposalVoteResponse",
    "CriteriaProposalCreateRequest",
    "CriteriaProposalResponse",
    "CriteriaProposalVoteResponse",
    "ConclusionProposalCreateRequest",
    "ConclusionProposalResponse",
    "ConclusionProposalVoteResponse",
    "ProposalStatusUpdateRequest",
    # Comment
    "CommentCreateRequest",
    "CommentUpdateRequest",
    "CommentResponse",
    "CommentCountResponse",
    "CommentCreatorInfo",
    # Setting
    "EventStatusUpdateRequest",
    "EventStatusUpdateResponse",
    # Vote
    "VoteCreateRequest",
    "VoteResponse",
    "VoteViewResponse",
    "VoteResultResponse",
    "OptionVoteCount",
    "CriterionRankInfo",
]
