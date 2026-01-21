import asyncio
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models import User
from app.db import get_db
from app.dependencies.auth import get_current_user
from app.services.event.stream_service import EventStreamService
from app.services.event.base import EventBaseService
from app.dependencies.repositories import get_event_aggregate_repositories
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.dependencies.services import get_stream_service
from app.exceptions import ForbiddenError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["events-stream"])


def get_event_base_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> EventBaseService:
    """EventBaseService 의존성 주입"""
    from app.services.event.base import EventBaseService
    return EventBaseService(db=db, repos=repos)


@router.get("/events/{event_id}/stream")
async def stream_event_updates(
    event_id: UUID,
    request: Request,
    last_event_id: Optional[UUID] = Query(None, alias="last_event_id", description="마지막으로 받은 이벤트 ID (재연결 시 사용)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    stream_service: EventStreamService = Depends(get_stream_service),
    base_service: EventBaseService = Depends(get_event_base_service),
):
    """
    SSE 스트림 엔드포인트
    
    이벤트의 실시간 업데이트를 Server-Sent Events로 전송합니다.
    - Proposal 생성, 투표 수 변경, 승인/기각 상태 변경, 코멘트 추가 등을 실시간으로 전송
    - Last-Event-ID 헤더 또는 쿼리 파라미터로 재연결 지원
    - Heartbeat를 30초마다 전송하여 프록시/로드밸런서 idle timeout 방지
    """
    # 멤버십 검증 (ACCEPTED 멤버십만 접근 가능)
    try:
        base_service._validate_membership_accepted(
            user_id=current_user.id,
            event_id=event_id,
            operation="stream events"
        )
    except ForbiddenError:
        # 멤버십이 ACCEPTED가 아니면 403 반환
        from fastapi import status
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "Forbidden", "detail": "Only accepted members can stream events"}
        )
    
    # Last-Event-ID 헤더도 확인 (쿼리 파라미터보다 우선)
    last_id = None
    if "Last-Event-ID" in request.headers:
        try:
            last_id = UUID(request.headers["Last-Event-ID"])
        except ValueError:
            logger.warning(f"Invalid Last-Event-ID header: {request.headers['Last-Event-ID']}")
    elif last_event_id:
        last_id = last_event_id
    
    async def event_generator():
        """SSE 이벤트 생성기"""
        heartbeat_counter = 0
        heartbeat_interval = 30  # 30초마다 heartbeat
        
        try:
            while True:
                # 클라이언트 연결 확인
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: {current_user.id}")
                    break
                
                try:
                    # 이벤트 조회
                    events, last_id_updated = stream_service.get_event_updates(
                        target_event_id=event_id,
                        last_id=last_id,
                        limit=100
                    )
                    
                    if events:
                        # 이벤트 전송
                        for event in events:
                            sse_data = event.model_dump()
                            sse_message = stream_service.format_sse_message(
                                event_id=event.id,
                                data=sse_data
                            )
                            yield sse_message
                        
                        # last_id 업데이트
                        last_id = last_id_updated
                        heartbeat_counter = 0  # 이벤트 전송 시 heartbeat 카운터 리셋
                    else:
                        # 이벤트가 없으면 heartbeat 체크
                        heartbeat_counter += 1
                        if heartbeat_counter >= heartbeat_interval:
                            yield stream_service.format_heartbeat()
                            heartbeat_counter = 0
                    
                    # 1초 대기
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in event stream: {e}", exc_info=True)
                    # 에러 발생 시 retry 헤더 전송
                    yield stream_service.format_retry(retry_ms=5000)
                    # 5초 대기 후 재시도
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info(f"Event stream cancelled: {current_user.id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in event stream: {e}", exc_info=True)
            yield stream_service.format_retry(retry_ms=5000)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx 프록시 버퍼링 방지
        }
    )
