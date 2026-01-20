from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.idempotency_repository import IdempotencyRepository
from app.models.idempotency import IdempotencyStatusType
from app.services.notification_service import NotificationService
from app.utils.transaction import transaction

# 시스템 사용자 ID (Outbox 핸들러용)
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


def _check_and_mark_idempotency(
    db: Session,
    idempotency_key: str
) -> bool:
    """
    멱등성 체크 및 처리 시작 표시
    
    Returns:
        True: 이미 처리됨 (스킵), False: 처리 필요
    """
    idempotency_repo = IdempotencyRepository(db)
    
    # 기존 레코드 조회
    existing_record = idempotency_repo.get(SYSTEM_USER_ID, idempotency_key)
    
    if existing_record:
        if existing_record.status == IdempotencyStatusType.COMPLETED:
            # 이미 처리 완료됨
            return True
        elif existing_record.status == IdempotencyStatusType.IN_PROGRESS:
            # 처리 중 (재시도 상황) - 다시 처리 시도
            # 기존 레코드를 FAILED로 변경하고 새로 시작
            idempotency_repo.mark_failed(existing_record)
            db.commit()
    
    # 새 레코드 생성 시도
    # 간단한 해시 생성 (outbox event id 기반이므로 단순화)
    from hashlib import sha256
    request_hash = sha256(idempotency_key.encode()).hexdigest()
    
    from datetime import timedelta
    record = idempotency_repo.try_acquire(
        user_id=SYSTEM_USER_ID,
        key=idempotency_key,
        method="OUTBOX_HANDLER",
        path=f"/outbox/{idempotency_key}",
        request_hash=request_hash,
        ttl=timedelta(hours=24)
    )
    
    if record is None:
        # 선점 실패 (동시 처리) - 다시 조회하여 확인
        existing_record = idempotency_repo.get(SYSTEM_USER_ID, idempotency_key)
        if existing_record and existing_record.status == IdempotencyStatusType.COMPLETED:
            return True  # 이미 처리됨
    
    return False  # 처리 필요


def _mark_idempotency_completed(
    db: Session,
    idempotency_key: str
) -> None:
    """멱등성 처리 완료 표시"""
    idempotency_repo = IdempotencyRepository(db)
    record = idempotency_repo.get(SYSTEM_USER_ID, idempotency_key)
    
    if record:
        idempotency_repo.mark_completed(
            record=record,
            response_code=200,
            response_body={"status": "completed"}
        )
        db.commit()


def _mark_idempotency_failed(
    db: Session,
    idempotency_key: str
) -> None:
    """멱등성 처리 실패 표시"""
    idempotency_repo = IdempotencyRepository(db)
    record = idempotency_repo.get(SYSTEM_USER_ID, idempotency_key)
    
    if record:
        idempotency_repo.mark_failed(record)
        db.commit()


def handle_proposal_approved(
    payload: dict,
    db: Session,
    outbox_event_id: UUID
) -> None:
    """
    Proposal 승인 알림 핸들러
    
    멱등성 보장: outbox event id를 멱등 키로 사용
    """
    idempotency_key = f"outbox:{outbox_event_id}"
    
    # 멱등성 체크
    if _check_and_mark_idempotency(db, idempotency_key):
        return  # 이미 처리됨
    
    try:
        proposal_id = UUID(payload["proposal_id"])
        event_id = UUID(payload["event_id"])
        approved_by = UUID(payload["approved_by"]) if payload.get("approved_by") else None
        
        notification_service = NotificationService(db)
        notification_service.send_proposal_approved_notification(
            proposal_id=proposal_id,
            event_id=event_id,
            approved_by=approved_by
        )
        
        # 처리 완료 표시
        _mark_idempotency_completed(db, idempotency_key)
    except Exception as e:
        # 실패 시 idempotency 기록 정리 (재시도 가능하도록)
        _mark_idempotency_failed(db, idempotency_key)
        raise


def handle_proposal_rejected(
    payload: dict,
    db: Session,
    outbox_event_id: UUID
) -> None:
    """Proposal 기각 알림 핸들러"""
    idempotency_key = f"outbox:{outbox_event_id}"
    
    # 멱등성 체크
    if _check_and_mark_idempotency(db, idempotency_key):
        return  # 이미 처리됨
    
    try:
        proposal_id = UUID(payload["proposal_id"])
        event_id = UUID(payload["event_id"])
        rejected_by = UUID(payload["rejected_by"])
        
        notification_service = NotificationService(db)
        notification_service.send_proposal_rejected_notification(
            proposal_id=proposal_id,
            event_id=event_id,
            rejected_by=rejected_by
        )
        
        # 처리 완료 표시
        _mark_idempotency_completed(db, idempotency_key)
    except Exception as e:
        # 실패 시 idempotency 기록 정리 (재시도 가능하도록)
        _mark_idempotency_failed(db, idempotency_key)
        raise


def handle_membership_approved(
    payload: dict,
    db: Session,
    outbox_event_id: UUID
) -> None:
    """멤버십 승인 알림 핸들러 (수동/자동 모두 처리)"""
    idempotency_key = f"outbox:{outbox_event_id}"
    
    # 멱등성 체크
    if _check_and_mark_idempotency(db, idempotency_key):
        return  # 이미 처리됨
    
    try:
        membership_id = UUID(payload["membership_id"])
        event_id = UUID(payload["event_id"])
        user_id = UUID(payload["user_id"])
        is_auto_approved = payload.get("is_auto_approved", False)
        approved_by = UUID(payload["approved_by"]) if payload.get("approved_by") else None
        
        notification_service = NotificationService(db)
        notification_service.send_membership_approved_notification(
            membership_id=membership_id,
            event_id=event_id,
            user_id=user_id,
            approved_by=approved_by,
            is_auto_approved=is_auto_approved
        )
        
        # 처리 완료 표시
        _mark_idempotency_completed(db, idempotency_key)
    except Exception as e:
        # 실패 시 idempotency 기록 정리 (재시도 가능하도록)
        _mark_idempotency_failed(db, idempotency_key)
        raise


def handle_membership_rejected(
    payload: dict,
    db: Session,
    outbox_event_id: UUID
) -> None:
    """멤버십 거절 알림 핸들러"""
    idempotency_key = f"outbox:{outbox_event_id}"
    
    # 멱등성 체크
    if _check_and_mark_idempotency(db, idempotency_key):
        return  # 이미 처리됨
    
    try:
        membership_id = UUID(payload["membership_id"])
        event_id = UUID(payload["event_id"])
        user_id = UUID(payload["user_id"])
        rejected_by = UUID(payload["rejected_by"])
        
        notification_service = NotificationService(db)
        notification_service.send_membership_rejected_notification(
            membership_id=membership_id,
            event_id=event_id,
            user_id=user_id,
            rejected_by=rejected_by
        )
        
        # 처리 완료 표시
        _mark_idempotency_completed(db, idempotency_key)
    except Exception as e:
        # 실패 시 idempotency 기록 정리 (재시도 가능하도록)
        _mark_idempotency_failed(db, idempotency_key)
        raise
