import time
import signal
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.outbox_repository import OutboxRepository, get_worker_id
from app.utils.transaction import transaction


class OutboxWorker:
    def __init__(self, db: Session, batch_size: int = 10, poll_interval: int = 5):
        self.db = db
        self.repos = OutboxRepository(db)
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.worker_id = get_worker_id()
        self.running = True
    
    def process_batch(self) -> None:
        """한 배치 처리"""
        now = datetime.now(timezone.utc)
        
        # 1. 트랜잭션 시작
        with transaction(self.db):
            # 2. 선점 가능한 이벤트 조회 및 선점
            events = self.repos.claim_pending_events(
                batch_size=self.batch_size,
                worker_id=self.worker_id,
                now=now
            )
            # 트랜잭션 커밋 (선점 완료)
        
        # 3. 트랜잭션 외부에서 실제 핸들러 실행
        for event in events:
            try:
                from app.workers.handlers import get_handler_for_event_type
                handler = get_handler_for_event_type(event.event_type)
                # 수정: 핸들러에 db와 event.id 전달 (멱등성 체크용)
                handler(event.payload, self.db, event.id)
                
                # 4. 성공 시 DONE 표시
                with transaction(self.db):
                    self.repos.mark_done(event.id, datetime.now(timezone.utc))
                    
            except Exception as e:
                # 5. 실패 시 재시도 스케줄링
                error_msg = str(e)
                backoff_seconds = 2 ** event.attempts  # 지수 백오프
                next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                
                with transaction(self.db):
                    can_retry = self.repos.mark_failed(
                        event_id=event.id,
                        error=error_msg,
                        next_retry_at=next_retry_at,
                        max_attempts=3
                    )
                    if not can_retry:
                        # 최대 시도 횟수 초과 → 로깅/알림 필요
                        print(f"Event {event.id} failed after max attempts")
    
    def run(self) -> None:
        """워커 메인 루프"""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        print(f"Outbox worker started: {self.worker_id}")
        
        while self.running:
            try:
                self.process_batch()
            except Exception as e:
                print(f"Error processing batch: {e}")
            
            time.sleep(self.poll_interval)
        
        print("Outbox worker stopped")
    
    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown"""
        print("Shutdown signal received")
        self.running = False


if __name__ == "__main__":
    # 별도 프로세스로 실행
    db = next(get_db())
    worker = OutboxWorker(db, batch_size=10, poll_interval=5)
    worker.run()
