from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import EventMembership, MembershipStatusType


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_membership(self, membership: EventMembership) -> EventMembership:
        """멤버십 생성"""
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership
