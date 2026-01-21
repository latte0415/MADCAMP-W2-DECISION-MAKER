import json
import hashlib
from typing import Callable, Optional, Dict, Any
from datetime import timedelta, datetime
from uuid import UUID
from enum import Enum

from sqlalchemy.orm import Session

from app.repositories.idempotency_repository import IdempotencyRepository
from app.models.idempotency import IdempotencyStatusType
from app.exceptions import ConflictError, ValidationError
from app.utils.transaction import transaction


class IdempotencyService:
    """Idempotency 처리 서비스"""
    
    DEFAULT_TTL = timedelta(hours=24)
    
    def __init__(self, db: Session, idempotency_repo: IdempotencyRepository):
        self.db = db
        self.idempotency_repo = idempotency_repo
    
    def _to_json_serializable(self, value: Any) -> Any:
        """
        값을 JSON 직렬화 가능한 형태로 변환
        - UUID → 문자열
        - Enum → 값 (문자열 또는 숫자)
        - datetime → ISO 형식 문자열
        - dict/list → 재귀적으로 변환
        """
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, Enum):
            return value.value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: self._to_json_serializable(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._to_json_serializable(item) for item in value]
        return value
    
    def normalize_request_body(self, body: dict) -> dict:
        """
        요청 바디 정규화
        - 반영되는 필드만 포함 (타임스탬프 등 비결정 필드 제외)
        - 키 정렬하여 일관성 보장
        - UUID, Enum 등을 JSON 직렬화 가능한 형태로 변환
        """
        # Pydantic 모델인 경우 dict로 변환
        if hasattr(body, 'model_dump'):
            # mode='json'을 사용하면 자동으로 직렬화 가능한 형태로 변환됨
            body = body.model_dump(exclude_none=True, mode='json')
        elif hasattr(body, 'dict'):
            body = body.dict(exclude_none=True)
        
        # 비결정 필드 제외 (필요시 확장 가능)
        excluded_fields = {'timestamp', 'created_at', 'updated_at', 'id'}
        normalized = {
            k: v for k, v in body.items()
            if k not in excluded_fields
        }
        
        # JSON 직렬화 가능한 형태로 변환
        normalized = {k: self._to_json_serializable(v) for k, v in normalized.items()}
        
        # 키 정렬하여 일관성 보장
        return dict(sorted(normalized.items()))
    
    def compute_request_hash(
        self,
        method: str,
        path: str,
        body: dict
    ) -> str:
        """
        요청 시그니처 생성
        - method + path + (정규화된 body) 형태
        - SHA-256 해시 생성
        """
        normalized_body = self.normalize_request_body(body)
        
        # JSON 직렬화 (정렬된 키 순서 보장)
        body_json = json.dumps(normalized_body, sort_keys=True, ensure_ascii=False)
        
        # 시그니처 생성
        signature = f"{method}:{path}:{body_json}"
        
        # SHA-256 해시
        hash_obj = hashlib.sha256(signature.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def run(
        self,
        user_id: UUID,
        key: str,
        method: str,
        path: str,
        body: dict,
        fn: Callable[[], Dict[str, Any]],
        ttl: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Idempotency 래퍼
        - 키 선점 시도
        - 중복 요청 처리 (COMPLETED → 저장된 응답 반환, IN_PROGRESS → 409, 다른 시그니처 → 409)
        - 최초 요청 시 실제 유스케이스 실행 후 성공 응답 저장
        """
        if ttl is None:
            ttl = self.DEFAULT_TTL
        
        # 요청 시그니처 계산
        request_hash = self.compute_request_hash(method, path, body)
        
        # 기존 레코드 조회
        existing_record = self.idempotency_repo.get(user_id, key)
        
        if existing_record:
            # 기존 레코드가 있는 경우
            if existing_record.status == IdempotencyStatusType.COMPLETED:
                # 완료된 요청의 재시도
                if existing_record.request_hash == request_hash:
                    # 같은 시그니처면 저장된 응답 반환
                    if existing_record.response_body is not None and existing_record.response_code is not None:
                        return existing_record.response_body
                    else:
                        # 응답이 저장되지 않은 경우 (이상 케이스)
                        raise ValidationError(
                            message="Invalid idempotency record",
                            detail="Completed record missing response data"
                        )
                else:
                    # 다른 시그니처면 키 재사용 에러
                    raise ConflictError(
                        message="Idempotency key reused",
                        detail="The same idempotency key was used with a different request"
                    )
            
            elif existing_record.status == IdempotencyStatusType.IN_PROGRESS:
                # 처리 중인 요청
                if existing_record.request_hash == request_hash:
                    # 같은 시그니처면 처리 중 에러
                    raise ConflictError(
                        message="Request in progress",
                        detail="A request with this idempotency key is currently being processed"
                    )
                else:
                    # 다른 시그니처면 키 재사용 에러
                    raise ConflictError(
                        message="Idempotency key reused",
                        detail="The same idempotency key was used with a different request"
                    )
            
            elif existing_record.status == IdempotencyStatusType.FAILED:
                # 실패한 요청은 재시도 허용 (새 레코드 생성)
                pass
        
        # 키 선점 시도
        record = self.idempotency_repo.try_acquire(
            user_id=user_id,
            key=key,
            method=method,
            path=path,
            request_hash=request_hash,
            ttl=ttl
        )
        
        if record is None:
            # 선점 실패 (동시 요청으로 인한 UNIQUE 충돌)
            # 다시 조회하여 상태 확인
            existing_record = self.idempotency_repo.get(user_id, key)
            if existing_record:
                if existing_record.status == IdempotencyStatusType.IN_PROGRESS:
                    if existing_record.request_hash == request_hash:
                        raise ConflictError(
                            message="Request in progress",
                            detail="A request with this idempotency key is currently being processed"
                        )
                    else:
                        raise ConflictError(
                            message="Idempotency key reused",
                            detail="The same idempotency key was used with a different request"
                        )
                elif existing_record.status == IdempotencyStatusType.COMPLETED:
                    if existing_record.request_hash == request_hash:
                        if existing_record.response_body is not None and existing_record.response_code is not None:
                            return existing_record.response_body
                        else:
                            raise ValidationError(
                                message="Invalid idempotency record",
                                detail="Completed record missing response data"
                            )
                    else:
                        raise ConflictError(
                            message="Idempotency key reused",
                            detail="The same idempotency key was used with a different request"
                        )
            else:
                # 예상치 못한 상황
                raise ConflictError(
                    message="Failed to acquire idempotency key",
                    detail="Unable to process request due to concurrent access"
                )
        
        # 최초 요청 실행
        try:
            result = fn()
            
            # 성공 응답 저장 (2xx 상태 코드만 저장)
            # result가 dict가 아닌 경우 dict로 변환 시도
            if not isinstance(result, dict):
                if hasattr(result, 'model_dump'):
                    # mode='json'을 사용하여 JSON 직렬화 가능한 형태로 변환
                    response_body = result.model_dump(mode='json')
                elif hasattr(result, 'dict'):
                    response_body = result.dict()
                    # dict() 결과도 JSON 직렬화 가능한 형태로 변환
                    response_body = self._to_json_serializable(response_body)
                else:
                    # 기본적으로 dict로 변환 시도
                    response_body = {"data": str(result)}
            else:
                # dict인 경우에도 JSON 직렬화 가능한 형태로 변환
                response_body = self._to_json_serializable(result)
            
            # 성공 응답 저장 (2xx로 가정, 실제로는 HTTP 상태 코드를 받아야 함)
            # 여기서는 기본적으로 200으로 저장
            # fn() 내부에서 트랜잭션이 커밋되었으므로, mark_completed 후 명시적으로 커밋 필요
            self.idempotency_repo.mark_completed(
                record=record,
                response_code=200,
                response_body=response_body
            )
            # mark_completed 후 명시적으로 커밋 (fn()의 트랜잭션과 별도로 커밋)
            self.db.commit()
            
            return response_body
            
        except Exception as e:
            # 실패 처리
            try:
                self.idempotency_repo.mark_failed(record)
                self.db.commit()
            except Exception:
                # mark_failed 실패 시에도 rollback 보장
                self.db.rollback()
            raise
