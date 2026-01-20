from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import datetime

from app.schemas.event.common import OptionInfo
from app.schemas.event.setting import CriterionInfo


class VoteCreateRequest(BaseModel):
    """투표 생성/업데이트 요청"""
    option_id: UUID  # 선택된 선택지 ID
    criterion_ids: List[UUID]  # 기준 ID 리스트 (순서대로, 0번째 = 1순위)


class VoteViewResponse(BaseModel):
    """투표 응답 (UI 표시용 정보 포함)"""
    # 투표 정보
    option_id: UUID | None  # 선택된 선택지 ID (NULL이면 투표 안한 걸로 판단)
    criterion_order: List[UUID]  # 기준 ID 리스트 (순서대로)
    created_at: datetime | None
    updated_at: datetime | None
    
    # UI 표시용 정보
    decision_subject: str  # 의사결정 주제
    options: List[OptionInfo]  # 전체 선택지 목록
    criteria: List[CriterionInfo]  # 전체 기준 목록

    class Config:
        from_attributes = True

class VoteResponse(BaseModel):
    """투표 응답"""
    option_id: UUID  # 선택된 선택지 ID
    criterion_order: List[UUID]  # 기준 ID 리스트 (순서대로)
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class OptionVoteCount(BaseModel):
    """옵션별 투표 수"""
    option_id: UUID
    option_content: str
    vote_count: int

    class Config:
        from_attributes = True


class CriterionRankInfo(BaseModel):
    """기준 순위 정보"""
    criterion_id: UUID
    criterion_content: str
    count: int  # 1순위로 선택된 횟수 또는 가중치 점수

    class Config:
        from_attributes = True


class VoteResultResponse(BaseModel):
    """투표 결과 조회 응답"""
    # 전체 인원 정보
    total_participants_count: int  # 전체 참가 인원 (ACCEPTED 멤버십)
    voted_participants_count: int  # 투표 참여 인원
    
    # 옵션별 투표 수
    option_vote_counts: List[OptionVoteCount]
    
    # 1순위로 가장 많이 꼽힌 기준 (내림차순)
    first_priority_criteria: List[CriterionRankInfo]
    
    # 우선순위별 가중치 부여한 기준 (내림차순, 1위=3점, 2위=2점, 3위=1점)
    weighted_criteria: List[CriterionRankInfo]

    class Config:
        from_attributes = True
