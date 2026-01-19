from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment
from app.repositories.content.comment import CommentRepository
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.services.event.base import EventBaseService
from app.exceptions import NotFoundError, ForbiddenError


class CommentService(EventBaseService):
    """Comment 관련 서비스"""
    
    def __init__(
        self,
        db: Session,
        repos: EventAggregateRepositories,
        comment_repo: CommentRepository
    ):
        super().__init__(db, repos)
        self.comment_repo = comment_repo

    def get_comment_count(
        self,
        event_id: UUID,
        criterion_id: UUID,
        user_id: UUID
    ) -> int:
        """특정 기준에 대한 코멘트 수 조회"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "view comments")
        
        # 기준이 해당 이벤트에 속하는지 확인
        criterion = self._validate_criterion_belongs_to_event(criterion_id, event_id)
        
        # 코멘트 수 조회
        return self.comment_repo.count_by_criterion_id(criterion_id)

    def get_comments(
        self,
        event_id: UUID,
        criterion_id: UUID,
        user_id: UUID
    ) -> List[Comment]:
        """특정 기준에 대한 코멘트 목록 조회"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "view comments")
        
        # 기준이 해당 이벤트에 속하는지 확인
        criterion = self._validate_criterion_belongs_to_event(criterion_id, event_id)
        
        # 코멘트 목록 조회 (creator 관계 포함)
        comments = self.comment_repo.get_by_criterion_id(criterion_id)
        
        # creator 관계 로드
        for comment in comments:
            if comment.creator is None:
                self.db.refresh(comment, ["creator"])
        
        return comments

    def create_comment(
        self,
        event_id: UUID,
        criterion_id: UUID,
        content: str,
        user_id: UUID
    ) -> Comment:
        """코멘트 생성"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "create comment")
        
        # 기준이 해당 이벤트에 속하는지 확인
        criterion = self._validate_criterion_belongs_to_event(criterion_id, event_id)
        
        # 코멘트 생성
        comment = Comment(
            criterion_id=criterion_id,
            content=content,
            created_by=user_id
        )
        
        result = self.comment_repo.create_comment(comment)
        self.db.commit()
        
        # creator 관계 로드
        self.db.refresh(result, ["creator"])
        
        return result

    def update_comment(
        self,
        event_id: UUID,
        comment_id: UUID,
        content: str,
        user_id: UUID
    ) -> Comment:
        """코멘트 수정"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "update comment")
        
        # 코멘트 조회 및 검증
        comment = self._validate_comment_exists_and_belongs_to_event(comment_id, event_id)
        
        # 소유자 검증
        if comment.created_by != user_id:
            raise ForbiddenError(
                message="Forbidden",
                detail="Only the comment creator can update this comment"
            )
        
        # 코멘트 수정
        comment.content = content
        result = self.comment_repo.update_comment(comment)
        self.db.commit()
        
        # creator 관계 로드
        self.db.refresh(result, ["creator"])
        
        return result

    def delete_comment(
        self,
        event_id: UUID,
        comment_id: UUID,
        user_id: UUID
    ) -> None:
        """코멘트 삭제"""
        # 이벤트 멤버십 검증
        self._validate_membership_accepted(user_id, event_id, "delete comment")
        
        # 코멘트 조회 및 검증
        comment = self._validate_comment_exists_and_belongs_to_event(comment_id, event_id)
        
        # 소유자 검증
        if comment.created_by != user_id:
            raise ForbiddenError(
                message="Forbidden",
                detail="Only the comment creator can delete this comment"
            )
        
        # 코멘트 삭제
        self.comment_repo.delete_comment(comment)
        self.db.commit()

    def _validate_criterion_belongs_to_event(
        self,
        criterion_id: UUID,
        event_id: UUID
    ):
        """기준이 해당 이벤트에 속하는지 확인"""
        criterion = self.repos.criterion.get_by_id(criterion_id)
        
        if not criterion:
            raise NotFoundError(
                message="Criterion not found",
                detail=f"Criterion with id {criterion_id} not found"
            )
        
        if criterion.event_id != event_id:
            raise NotFoundError(
                message="Criterion not found",
                detail=f"Criterion does not belong to this event"
            )
        
        return criterion

    def _validate_comment_exists_and_belongs_to_event(
        self,
        comment_id: UUID,
        event_id: UUID
    ) -> Comment:
        """코멘트가 존재하고 해당 이벤트에 속하는지 확인"""
        comment = self.comment_repo.get_by_id(comment_id)
        
        if not comment:
            raise NotFoundError(
                message="Comment not found",
                detail=f"Comment with id {comment_id} not found"
            )
        
        # 코멘트의 기준이 해당 이벤트에 속하는지 확인
        criterion = self._validate_criterion_belongs_to_event(comment.criterion_id, event_id)
        
        return comment
