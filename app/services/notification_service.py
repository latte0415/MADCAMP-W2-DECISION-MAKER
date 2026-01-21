from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.event_repository import EventRepository
from app.repositories.proposal.generic import ProposalRepositoryGeneric
from app.repositories.membership_repository import MembershipRepository
from app.utils.mailer import SendGridMailer


class NotificationService:
    def __init__(self, db: Session, mailer: SendGridMailer | None = None):
        self.db = db
        self.mailer = mailer
        self.event_repo = EventRepository(db)
        self.proposal_repo = ProposalRepositoryGeneric(db)
        self.membership_repo = MembershipRepository(db)
    
    def send_proposal_approved_notification(
        self,
        proposal_id: UUID,
        event_id: UUID,
        approved_by: UUID | None
    ) -> None:
        """
        Proposal 승인 알림 발송
        
        TODO: 실제 알림 발송 구현
        - 프론트엔드 실시간 알림 (SSE/WebSocket)
        - 이메일 알림 (선택)
        - 푸시 알림 (향후)
        """
        # 1. 필요한 데이터 조회 (payload에 최소 정보만 있으므로)
        # proposal, event, user 정보 조회
        
        # 2. 알림 발송
        # - 프론트엔드 실시간 알림 (SSE/WebSocket)
        # - 이메일 알림 (선택)
        # - 푸시 알림 (향후)
        pass
    
    def send_proposal_rejected_notification(
        self,
        proposal_id: UUID,
        event_id: UUID,
        rejected_by: UUID
    ) -> None:
        """
        Proposal 기각 알림 발송
        
        TODO: 실제 알림 발송 구현
        - 프론트엔드 실시간 알림 (SSE/WebSocket)
        """
        # 프론트엔드 실시간 알림
        pass
    
    def send_membership_approved_notification(
        self,
        membership_id: UUID,
        event_id: UUID,
        user_id: UUID,
        approved_by: UUID | None,
        is_auto_approved: bool = False
    ) -> None:
        """
        멤버십 승인 알림 발송 (수동/자동 모두 처리)
        
        TODO: 실제 알림 발송 구현
        - 프론트엔드 실시간 알림
        - 이메일 알림 (선택, 자동 승인 시에는 선택적)
        - is_auto_approved에 따라 알림 메시지 다르게 처리 가능
        """
        # 1. 필요한 데이터 조회
        # membership, event, user 정보 조회
        
        # 2. 알림 발송
        # - 프론트엔드 실시간 알림
        # - 이메일 알림 (선택, 자동 승인 시에는 선택적)
        # - is_auto_approved에 따라 알림 메시지 다르게 처리 가능
        pass
    
    def send_membership_rejected_notification(
        self,
        membership_id: UUID,
        event_id: UUID,
        user_id: UUID,
        rejected_by: UUID
    ) -> None:
        """
        멤버십 거절 알림 발송
        
        TODO: 실제 알림 발송 구현
        - 프론트엔드 실시간 알림
        """
        # 프론트엔드 실시간 알림
        pass
