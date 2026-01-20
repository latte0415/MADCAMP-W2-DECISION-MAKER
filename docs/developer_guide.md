# 개발자 가이드

> 이 문서는 프로젝트 개발을 위한 실용적인 가이드를 제공합니다.

---

## 목차

- [시작하기](#시작하기)
- [프로젝트 구조](#프로젝트-구조)
- [개발 워크플로우](#개발-워크플로우)
- [코딩 컨벤션](#코딩-컨벤션)
- [새로운 기능 추가하기](#새로운-기능-추가하기)
- [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
- [테스트](#테스트)
- [디버깅](#디버깅)
- [자주 묻는 질문](#자주-묻는-질문)

---

## 시작하기

### 환경 설정

1. **Python 버전**: Python 3.11 이상

2. **가상 환경 생성**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 설정**:
   `.env` 파일 생성:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ENVIRONMENT=development
   ```

5. **데이터베이스 설정**:
   ```bash
   # 마이그레이션 실행
   alembic upgrade head
   ```

6. **서버 실행**:
   ```bash
   uvicorn main:app --reload
   ```

---

## 프로젝트 구조

### 디렉토리 구조

```
backend/
├── app/
│   ├── routers/              # HTTP 라우터
│   │   ├── auth.py
│   │   ├── event/
│   │   │   ├── home.py
│   │   │   ├── creation.py
│   │   │   ├── detail.py
│   │   │   └── ...
│   │   └── dev/              # 개발용 라우터
│   ├── services/             # 비즈니스 로직
│   │   ├── auth.py
│   │   └── event/
│   │       ├── base.py       # 공통 서비스
│   │       ├── home_service.py
│   │       └── ...
│   ├── repositories/         # 데이터 접근
│   │   ├── event_repository.py
│   │   ├── content/
│   │   └── proposal/
│   ├── models/               # ORM 모델
│   │   ├── auth.py          # 사용자, 인증 관련 모델
│   │   ├── event.py         # 이벤트, 멤버십, 선택지 모델
│   │   ├── content.py       # 전제, 기준 모델
│   │   ├── proposal.py      # 제안 모델
│   │   ├── vote.py          # 투표 모델
│   │   ├── comment.py       # 코멘트 모델
│   │   └── idempotency.py   # 멱등성 레코드 모델
│   ├── schemas/              # Pydantic 스키마
│   │   ├── auth.py
│   │   └── event/
│   ├── dependencies/         # 의존성 주입
│   │   ├── auth.py
│   │   ├── repositories.py
│   │   └── services.py
│   ├── exceptions.py         # 커스텀 예외
│   └── db.py                # DB 설정
├── migrations/               # Alembic 마이그레이션
├── docs/                     # 문서
├── main.py                   # FastAPI 앱
└── requirements.txt
```

---

## 개발 워크플로우

### 1. 새로운 API 엔드포인트 추가

#### Step 1: Schema 정의

`app/schemas/event/` 디렉토리에 요청/응답 스키마 정의:

```python
# app/schemas/event/example.py
from pydantic import BaseModel
from uuid import UUID

class ExampleRequest(BaseModel):
    name: str
    description: str | None = None

class ExampleResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
```

#### Step 2: Repository 메서드 추가 (필요 시)

`app/repositories/` 디렉토리에 데이터 접근 메서드 추가:

```python
# app/repositories/example_repository.py
class ExampleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_example(self, example: Example) -> Example:
        self.db.add(example)
        self.db.flush()
        return example
```

#### Step 3: Service 메서드 추가

`app/services/event/` 디렉토리에 비즈니스 로직 추가:

```python
# app/services/event/example_service.py
class ExampleService(EventBaseService):
    def create_example(
        self,
        event_id: UUID,
        request: ExampleRequest,
        user_id: UUID
    ) -> ExampleResponse:
        # 검증
        event = self.get_event_with_all_relations(event_id)
        self._validate_membership_accepted(user_id, event_id, "create example")
        
        # 비즈니스 로직
        example = Example(
            event_id=event_id,
            name=request.name,
            description=request.description,
            created_by=user_id
        )
        created = self.repos.example.create_example(example)
        self.db.commit()
        
        # 응답 생성
        return ExampleResponse(
            id=created.id,
            name=created.name,
            created_at=created.created_at
        )
```

#### Step 4: Router 엔드포인트 추가

`app/routers/event/` 디렉토리에 엔드포인트 추가:

```python
# app/routers/event/example.py
from fastapi import APIRouter, Depends
from app.models import User
from app.services.event.example_service import ExampleService
from app.schemas.event.example import ExampleRequest, ExampleResponse
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_example_service

router = APIRouter(tags=["events-example"])

@router.post(
    "/events/{event_id}/examples",
    response_model=ExampleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_example(
    event_id: UUID,
    request: ExampleRequest,
    current_user: User = Depends(get_current_user),
    example_service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    return example_service.create_example(
        event_id=event_id,
        request=request,
        user_id=current_user.id
    )
```

#### Step 5: 의존성 주입 설정

`app/dependencies/services.py`에 Service 의존성 추가:

```python
def get_example_service(
    db: Session = Depends(get_db),
    repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
) -> ExampleService:
    return ExampleService(db=db, repos=repos)
```

#### Step 6: Router 등록

`app/routers/event/__init__.py`에 라우터 등록:

```python
from app.routers.event import example

router.include_router(example.router)
```

---

### 2. 데이터베이스 모델 추가

#### Step 1: Model 정의

`app/models/` 디렉토리에 모델 추가:

```python
# app/models/example.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from app.db import Base

class Example(Base):
    __tablename__ = "examples"
    __table_args__ = (
        UniqueConstraint("event_id", "name", name="uq_examples_event_name"),
        CheckConstraint("LENGTH(name) > 0", name="ck_examples_name_length"),
        Index("idx_examples_event_id", "event_id"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

#### Step 2: 마이그레이션 생성

```bash
alembic revision --autogenerate -m "add examples table"
```

#### Step 3: 마이그레이션 검토 및 실행

```bash
# 마이그레이션 파일 검토
# migrations/versions/xxxx_add_examples_table.py

# 마이그레이션 실행
alembic upgrade head
```

---

## 코딩 컨벤션

### 1. 네이밍 규칙

- **클래스**: PascalCase (`EventService`, `EventRepository`)
- **함수/변수**: snake_case (`get_event_detail`, `event_id`)
- **상수**: UPPER_SNAKE_CASE (`MAX_MEMBERSHIP`)
- **파일명**: snake_case (`event_service.py`)

### 2. 타입 힌트

모든 함수에 타입 힌트 사용:

```python
def get_event_detail(
    event_id: UUID,
    user_id: UUID
) -> EventDetailResponse:
    # ...
```

### 3. Docstring

공개 함수/클래스에 docstring 작성:

```python
def get_event_detail(
    self,
    event_id: UUID,
    user_id: UUID
) -> EventDetailResponse:
    """
    이벤트 상세 조회
    
    Args:
        event_id: 이벤트 ID
        user_id: 사용자 ID
    
    Returns:
        EventDetailResponse: 이벤트 상세 정보
    
    Raises:
        NotFoundError: 이벤트를 찾을 수 없음
        ForbiddenError: ACCEPTED 멤버십이 아님
    """
```

### 4. Import 순서

1. 표준 라이브러리
2. 서드파티 라이브러리
3. 로컬 모듈

```python
# 표준 라이브러리
from uuid import UUID
from datetime import datetime

# 서드파티
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 로컬 모듈
from app.models import User
from app.services.event import EventService
```

### 5. 에러 처리

커스텀 예외 사용:

```python
from app.exceptions import NotFoundError, ValidationError

if not event:
    raise NotFoundError(
        message="Event not found",
        detail=f"Event with id {event_id} not found"
    )
```

---

## 새로운 기능 추가하기

### 예시: 새로운 투표 타입 추가

#### 1. Model 추가

```python
# app/models/vote.py
class NewVoteType(Base):
    __tablename__ = "new_vote_types"
    # ...
```

#### 2. Schema 추가

```python
# app/schemas/event/vote.py
class NewVoteTypeRequest(BaseModel):
    # ...
```

#### 3. Repository 추가

```python
# app/repositories/vote_repository.py
class VoteRepository:
    def create_new_vote_type(self, vote: NewVoteType) -> NewVoteType:
        # ...
```

#### 4. Service 추가

```python
# app/services/event/vote_service.py
class VoteService(EventBaseService):
    def create_new_vote_type(
        self,
        event_id: UUID,
        request: NewVoteTypeRequest,
        user_id: UUID
    ) -> NewVoteTypeResponse:
        # 검증
        # 비즈니스 로직
        # 응답 반환
```

#### 5. Router 추가

```python
# app/routers/event/vote.py
@router.post("/events/{event_id}/new-vote-types")
def create_new_vote_type(
    # ...
):
    # ...
```

---

## 데이터베이스 마이그레이션

### 마이그레이션 생성

```bash
# 자동 생성 (모델 변경 감지)
alembic revision --autogenerate -m "description"

# 수동 생성
alembic revision -m "description"
```

### 마이그레이션 실행

```bash
# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 업그레이드
alembic upgrade <revision>

# 한 단계 롤백
alembic downgrade -1

# 특정 버전으로 롤백
alembic downgrade <revision>
```

### 마이그레이션 파일 구조

```python
"""add examples table

Revision ID: xxxx
Revises: yyyy
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'examples',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # ...
    )

def downgrade():
    op.drop_table('examples')
```

---

## 테스트

### 테스트 구조 (권장)

```
tests/
├── test_routers/
│   ├── test_auth.py
│   └── test_event.py
├── test_services/
│   └── test_event_service.py
└── test_repositories/
    └── test_event_repository.py
```

### 테스트 예시

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_event_detail():
    response = client.get(
        "/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()
```

---

## 디버깅

### 1. 로깅

개발 환경에서 자세한 에러 정보 확인:

```python
# 개발 환경에서만 스택 트레이스 포함
if is_development():
    import traceback
    response_data["traceback"] = traceback.format_exc()
```

### 2. 데이터베이스 쿼리 확인

SQLAlchemy 로깅 활성화:

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 3. FastAPI 자동 문서

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 자주 묻는 질문

### Q1: 새로운 Repository를 추가하려면?

1. `app/repositories/`에 Repository 클래스 생성
2. `app/dependencies/repositories.py`에 의존성 함수 추가
3. `app/dependencies/aggregate_repositories.py`에 Aggregate에 추가 (필요 시)

### Q2: 공통 검증 로직을 추가하려면?

`app/services/event/base.py`의 `EventBaseService`에 메서드 추가:

```python
def _validate_custom_rule(self, event_id: UUID, user_id: UUID):
    """공통 검증 로직"""
    # ...
```

### Q3: 새로운 예외 타입을 추가하려면?

`app/exceptions.py`에 예외 클래스 추가:

```python
class CustomError(AppException):
    @property
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST
```

### Q4: 트랜잭션을 명시적으로 관리하려면?

Service 메서드에서:

```python
def create_example(self, ...):
    try:
        # 작업 수행
        self.db.commit()
    except Exception:
        self.db.rollback()
        raise
```

### Q5: N+1 쿼리 문제를 해결하려면?

Repository에서 `joinedload` 사용:

```python
from sqlalchemy.orm import joinedload

stmt = (
    select(Event)
    .options(joinedload(Event.options))
    .where(Event.id == event_id)
)
```

### Q6: assumptions/criterion의 is_deleted, is_modified 필드는 언제 사용하나요?

- `is_deleted`: 삭제 제안이 승인되어 실제로 삭제된 경우 true로 설정
- `is_modified`: 수정 제안이 승인되어 실제로 수정된 경우 true로 설정
- `original_content`: 수정 전 원본 내용을 저장 (수정된 경우에만 값이 있음)
- 이 필드들은 제안 시스템에서 실제 변경사항을 추적하기 위해 사용됩니다.

### Q7: Proposal 테이블의 UNIQUE 제약 조건이 주석 처리된 이유는?

- CREATION의 경우 `assumption_id`/`criteria_id`가 NULL이므로 UNIQUE 제약이 제대로 작동하지 않습니다.
- 따라서 중복 제안 방지는 서비스 레이어에서 처리합니다 (`get_pending_*_proposal_by_user` 메서드 사용).
- MODIFICATION/DELETION의 경우도 서비스 레이어에서 중복 체크를 수행합니다.

---

## 유용한 명령어

### 개발 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn main:app --reload

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 데이터베이스 관련

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 실행
alembic upgrade head

# 현재 버전 확인
alembic current

# 마이그레이션 히스토리
alembic history
```

### 코드 포맷팅 (권장 도구)

```bash
# Black (코드 포맷터)
black app/

# isort (import 정렬)
isort app/

# mypy (타입 체크)
mypy app/
```

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 문서](https://docs.sqlalchemy.org/en/20/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [Alembic 문서](https://alembic.sqlalchemy.org/)

---

**작성일**: 2024년
**최종 수정일**: 2024년
