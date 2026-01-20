from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session):
    """
    트랜잭션 컨텍스트 매니저
    
    사용 예시:
        with transaction(self.db):
            # DB 작업 수행
            self.repos.proposal.create_assumption_proposal(proposal)
            # 예외 발생 시 자동 rollback, 정상 종료 시 commit
    
    규칙:
        - 정상 종료 시 commit() 실행
        - 예외 발생 시 rollback() 후 예외 재발생
        - 서비스는 직접 commit하지 않음 (매니저가 처리)
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
