from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_criterion_id(self, criterion_id: UUID) -> List[Comment]:
        """특정 기준의 코멘트 목록 조회"""
        stmt = (
            select(Comment)
            .where(Comment.criterion_id == criterion_id)
            .order_by(Comment.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def count_by_criterion_id(self, criterion_id: UUID) -> int:
        """특정 기준의 코멘트 수 조회"""
        stmt = (
            select(func.count(Comment.id))
            .where(Comment.criterion_id == criterion_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one() or 0

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        """코멘트 ID로 조회"""
        stmt = select(Comment).where(Comment.id == comment_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_comment(self, comment: Comment) -> Comment:
        """코멘트 생성"""
        self.db.add(comment)
        self.db.flush()  # ID를 얻기 위해 flush만 수행 (commit은 Service에서)
        self.db.refresh(comment)
        return comment

    def update_comment(self, comment: Comment) -> Comment:
        """코멘트 수정"""
        from datetime import datetime, timezone
        comment.updated_at = datetime.now(timezone.utc)
        self.db.flush()  # commit은 Service에서 수행
        self.db.refresh(comment)
        return comment

    def delete_comment(self, comment: Comment) -> None:
        """코멘트 삭제"""
        self.db.delete(comment)
        # commit은 Service에서 수행
