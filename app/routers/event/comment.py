from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models import User
from app.services.event.comment_service import CommentService
from app.schemas.event.comment import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentResponse,
    CommentCountResponse,
    CommentCreatorInfo,
)
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_comment_service


router = APIRouter(tags=["events-comment"])


@router.get(
    "/events/{event_id}/criteria/{criterion_id}/comments/count",
    response_model=CommentCountResponse
)
def get_comment_count(
    event_id: UUID,
    criterion_id: UUID,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentCountResponse:
    """
    특정 기준에 대한 코멘트 수 조회 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 조회 가능
    """
    count = comment_service.get_comment_count(
        event_id=event_id,
        criterion_id=criterion_id,
        user_id=current_user.id
    )
    return CommentCountResponse(count=count)


@router.get(
    "/events/{event_id}/criteria/{criterion_id}/comments",
    response_model=List[CommentResponse]
)
def get_comments(
    event_id: UUID,
    criterion_id: UUID,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> List[CommentResponse]:
    """
    특정 기준에 대한 코멘트 목록 조회 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 조회 가능
    - 작성자 정보 포함
    """
    comments = comment_service.get_comments(
        event_id=event_id,
        criterion_id=criterion_id,
        user_id=current_user.id
    )
    return [
        CommentResponse(
            id=comment.id,
            criterion_id=comment.criterion_id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            created_by=comment.created_by,
            creator=CommentCreatorInfo(
                id=comment.creator.id,
                name=comment.creator.name,
                email=comment.creator.email
            ) if comment.creator else None
        )
        for comment in comments
    ]


@router.post(
    "/events/{event_id}/criteria/{criterion_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    event_id: UUID,
    criterion_id: UUID,
    request: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """
    코멘트 생성 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 생성 가능
    """
    comment = comment_service.create_comment(
        event_id=event_id,
        criterion_id=criterion_id,
        content=request.content,
        user_id=current_user.id
    )
    return CommentResponse(
        id=comment.id,
        criterion_id=comment.criterion_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        created_by=comment.created_by,
        creator=CommentCreatorInfo(
            id=comment.creator.id,
            name=comment.creator.name,
            email=comment.creator.email
        ) if comment.creator else None
    )


@router.patch(
    "/events/{event_id}/comments/{comment_id}",
    response_model=CommentResponse
)
def update_comment(
    event_id: UUID,
    comment_id: UUID,
    request: CommentUpdateRequest,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """
    코멘트 수정 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 수정 가능
    - 본인이 작성한 코멘트만 수정 가능
    """
    comment = comment_service.update_comment(
        event_id=event_id,
        comment_id=comment_id,
        content=request.content,
        user_id=current_user.id
    )
    return CommentResponse(
        id=comment.id,
        criterion_id=comment.criterion_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        created_by=comment.created_by,
        creator=CommentCreatorInfo(
            id=comment.creator.id,
            name=comment.creator.name,
            email=comment.creator.email
        ) if comment.creator else None
    )


@router.delete(
    "/events/{event_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    event_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
) -> None:
    """
    코멘트 삭제 API
    - 이벤트 멤버십이 ACCEPTED 상태인 사용자만 삭제 가능
    - 본인이 작성한 코멘트만 삭제 가능
    """
    comment_service.delete_comment(
        event_id=event_id,
        comment_id=comment_id,
        user_id=current_user.id
    )
