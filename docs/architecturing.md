# 아키텍처 문서

> 이 문서는 프로젝트의 전체 아키텍처와 설계 원칙을 설명합니다.

---

## 목차

- [아키텍처 개요](#아키텍처-개요)
- [레이어 구조](#레이어-구조)
- [주요 설계 패턴](#주요-설계-패턴)
- [의존성 주입](#의존성-주입)
- [데이터베이스 설계](#데이터베이스-설계)
- [에러 처리](#에러-처리)
- [인증 및 보안](#인증-및-보안)

---

## 아키텍처 개요

### 전체 구조

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)**를 기반으로 하며, **의존성 주입(Dependency Injection)** 패턴을 사용합니다.

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (main.py, CORS, Error Handlers)        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            Router Layer                 │
│  (HTTP 요청/응답 처리, 라우팅)          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            Service Layer                │
│  (비즈니스 로직, 검증, 트랜잭션 관리)   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Repository Layer               │
│  (데이터 접근, 쿼리 실행)               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            Model Layer                  │
│  (SQLAlchemy ORM 모델)                  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         PostgreSQL Database             │
└─────────────────────────────────────────┘
```

### 기술 스택

- **프레임워크**: FastAPI 0.128.0
- **ORM**: SQLAlchemy 2.0.45
- **데이터베이스**: PostgreSQL
- **마이그레이션**: Alembic 1.18.1
- **검증**: Pydantic 2.12.5
- **인증**: JWT (python-jose), bcrypt
- **서버**: Uvicorn

---

## 레이어 구조

### 1. Router Layer (`app/routers/`)

**역할**: HTTP 요청/응답 처리, 라우팅, 인증 검증

**구조**:
```
routers/
├── auth.py              # 인증 관련 라우터
├── event/               # 이벤트 관련 라우터
│   ├── home.py         # 홈 화면
│   ├── creation.py      # 이벤트 생성
│   ├── entry.py        # 이벤트 입장
│   ├── detail.py       # 이벤트 상세
│   ├── setting.py      # 이벤트 설정
│   ├── comment.py      # 코멘트
│   └── vote.py         # 투표
└── dev/                # 개발용 라우터
```

**특징**:
- FastAPI의 `APIRouter` 사용
- 의존성 주입으로 Service 레이어 호출
- 인증은 `get_current_user` 의존성으로 처리
- 최소한의 로직만 포함 (비즈니스 로직은 Service로 위임)

**예시**:
```python
@router.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event_detail(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
    return event_service.get_event_detail(
        event_id=event_id,
        user_id=current_user.id
    )
```

---

### 2. Service Layer (`app/services/`)

**역할**: 비즈니스 로직, 검증, 트랜잭션 관리, 권한 확인

**구조**:
```
services/
├── auth.py              # 인증 서비스
└── event/               # 이벤트 관련 서비스
    ├── base.py          # 공통 서비스 (EventBaseService)
    ├── home_service.py
    ├── creation_service.py
    ├── overview_service.py
    ├── detail_service.py
    ├── setting_service.py
    ├── membership_service.py
    ├── proposal_service.py
    ├── comment_service.py
    ├── vote_service.py
    └── __init__.py      # 통합 서비스 (EventService)
```

**특징**:
- **Base Service 패턴**: `EventBaseService`에서 공통 로직 제공
- **통합 Service 패턴**: `EventService`가 여러 서브 서비스를 조합
- Repository를 통한 데이터 접근
- 커스텀 예외를 통한 에러 처리
- 트랜잭션 관리 (`self.db.commit()`)

**Base Service 예시**:
```python
class EventBaseService:
    """Event 관련 공통 서비스 로직"""
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        # ...
    
    def _validate_membership_accepted(self, user_id: UUID, event_id: UUID, operation: str):
        """멤버십 ACCEPTED 상태 검증"""
        # ...
    
    def _validate_event_in_progress(self, event_id: UUID, operation: str) -> Event:
        """이벤트가 IN_PROGRESS 상태인지 검증"""
        # ...
```

---

### 3. Repository Layer (`app/repositories/`)

**역할**: 데이터 접근, 쿼리 실행, ORM 추상화

**구조**:
```
repositories/
├── auth.py                      # 인증 관련 리포지토리
├── event_repository.py          # 이벤트 리포지토리
├── membership_repository.py    # 멤버십 리포지토리
├── vote_repository.py           # 투표 리포지토리
├── content/                     # 콘텐츠 관련 리포지토리
│   ├── assumption.py
│   ├── criterion.py
│   ├── option.py
│   └── comment.py
└── proposal/                    # 제안 관련 리포지토리
    ├── generic.py              # 제너릭 리포지토리
    ├── assumption.py
    ├── criteria.py
    └── conclusion.py
```

**특징**:
- **Aggregate Repository 패턴**: 관련 리포지토리를 묶어서 제공
- **제너릭 Repository 패턴**: 공통 메서드를 제너릭으로 구현
- SQLAlchemy 쿼리 작성
- N+1 쿼리 방지 (joinedload 사용)

**Aggregate Repository 예시**:
```python
class EventAggregateRepositories:
    """Event 관련 모든 Repository를 하나로 묶은 Aggregate"""
    
    def __init__(self, db: Session):
        self.event = EventRepository(db)
        self.option = OptionRepository(db)
        self.assumption = AssumptionRepository(db)
        self.criterion = CriterionRepository(db)
        self.comment = CommentRepository(db)
        self.proposal = ProposalRepository(db)
```

**제너릭 Repository 예시**:
```python
class ProposalRepositoryGeneric:
    """Proposal 리포지토리의 제너릭 메서드를 제공하는 Base 클래스"""
    
    def approve_proposal_if_pending_generic(
        self,
        proposal_id: UUID,
        accepted_at: datetime,
        proposal_class: Type[ProposalType]
    ) -> ProposalType | None:
        """조건부 승인 (WHERE id = :id AND status = 'PENDING')"""
        # ...
```

---

### 4. Model Layer (`app/models/`)

**역할**: 데이터베이스 스키마 정의, ORM 모델

**구조**:
```
models/
├── auth.py          # 사용자, 인증 관련 모델
├── event.py         # 이벤트, 멤버십, 선택지 모델
├── content.py       # 전제, 기준 모델
├── proposal.py      # 제안 모델
├── vote.py          # 투표 모델
└── comment.py       # 코멘트 모델
```

**특징**:
- SQLAlchemy 2.0 스타일 (Mapped 타입 힌트)
- 관계 정의 (relationship)
- 제약 조건 (UniqueConstraint, CheckConstraint)
- 인덱스 정의

**예시**:
```python
class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("entrance_code", name="uq_events_entrance_code"),
        CheckConstraint("LENGTH(entrance_code) = 6", name="ck_events_entrance_code_length"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    decision_subject: Mapped[str] = mapped_column(Text, nullable=False)
    # ...
```

---

### 5. Schema Layer (`app/schemas/`)

**역할**: 요청/응답 검증, 직렬화

**구조**:
```
schemas/
├── auth.py          # 인증 관련 스키마
├── dev/             # 개발용 스키마
└── event/           # 이벤트 관련 스키마
    ├── common.py
    ├── home.py
    ├── creation.py
    ├── overview.py
    ├── detail.py
    ├── setting.py
    ├── proposal.py
    ├── comment.py
    └── vote.py
```

**특징**:
- Pydantic BaseModel 사용
- 요청/응답 스키마 분리
- 타입 검증 및 직렬화

---

## 주요 설계 패턴

### 1. 의존성 주입 (Dependency Injection)

FastAPI의 `Depends`를 사용하여 의존성을 주입합니다.

**의존성 체인**:
```
Router → Service → Repository → Database
```

**예시**:
```python
# Router에서 Service 주입
@router.get("/events/{event_id}")
def get_event_detail(
    event_service: EventService = Depends(get_event_service),
):
    # ...

# Service에서 Repository 주입
class EventService(EventBaseService):
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        super().__init__(db, repos)
```

---

### 2. Aggregate Repository 패턴

관련된 여러 Repository를 하나의 Aggregate로 묶어서 제공합니다.

**장점**:
- 의존성 주입 단순화
- 관련 리포지토리를 함께 관리
- Service에서 `self.repos.event`, `self.repos.option` 등으로 접근

**구현**:
```python
class EventAggregateRepositories:
    def __init__(self, db: Session):
        self.event = EventRepository(db)
        self.option = OptionRepository(db)
        # ...
```

---

### 3. Base Service 패턴

공통 서비스 로직을 Base 클래스에 정의합니다.

**장점**:
- 코드 중복 제거
- 일관된 검증 로직
- 공통 메서드 재사용

**구현**:
```python
class EventBaseService:
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """관리자 권한 확인"""
        # ...
    
    def _validate_membership_accepted(self, user_id: UUID, event_id: UUID, operation: str):
        """멤버십 검증"""
        # ...
```

---

### 4. 통합 Service 패턴

여러 서브 서비스를 하나의 통합 서비스로 제공합니다.

**장점**:
- 기존 코드 호환성 유지
- 서브 서비스 분리로 유지보수 용이

**구현**:
```python
class EventService(EventBaseService):
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        super().__init__(db, repos)
        self._home_service = EventHomeService(db, repos)
        self._detail_service = EventDetailService(db, repos)
        # ...
    
    def get_event_detail(self, event_id, user_id):
        return self._detail_service.get_event_detail(event_id, user_id)
```

---

### 5. 제너릭 Repository 패턴

공통 메서드를 제너릭으로 구현하여 코드 중복을 제거합니다.

**구현**:
```python
class ProposalRepositoryGeneric:
    def approve_proposal_if_pending_generic(
        self,
        proposal_id: UUID,
        accepted_at: datetime,
        proposal_class: Type[ProposalType]
    ) -> ProposalType | None:
        """조건부 승인 (제너릭)"""
        # ...
```

---

## 의존성 주입

### 의존성 주입 구조

```
app/dependencies/
├── __init__.py              # 재export
├── auth.py                  # 인증 관련 의존성
├── repositories.py          # Repository 의존성
├── services.py              # Service 의존성
├── aggregate_repositories.py # Aggregate Repository 의존성
└── error_handlers.py        # 에러 핸들러 등록
```

### 의존성 주입 흐름

1. **Router 레이어**:
   ```python
   @router.get("/events/{event_id}")
   def get_event_detail(
       event_service: EventService = Depends(get_event_service),
   ):
   ```

2. **Service 의존성**:
   ```python
   def get_event_service(
       db: Session = Depends(get_db),
       repos: EventAggregateRepositories = Depends(get_event_aggregate_repositories),
   ) -> EventService:
       return EventService(db=db, repos=repos)
   ```

3. **Repository 의존성**:
   ```python
   def get_event_aggregate_repositories(
       db: Session = Depends(get_db)
   ) -> EventAggregateRepositories:
       return EventAggregateRepositories(db)
   ```

---

## 데이터베이스 설계

### ORM 사용

- **SQLAlchemy 2.0**: 최신 스타일 사용
- **Alembic**: 마이그레이션 관리
- **PostgreSQL**: 프로덕션 데이터베이스

### 주요 테이블

- `users`: 사용자
- `events`: 이벤트
- `event_memberships`: 이벤트 멤버십
- `options`: 선택지
- `assumptions`: 전제 (is_deleted, is_modified, original_content 필드 포함)
- `criterion`: 기준 (is_deleted, is_modified, original_content 필드 포함)
- `assumption_proposals`: 전제 제안
- `criteria_proposals`: 기준 제안
- `conclusion_proposals`: 결론 제안
- `assumption_proposal_votes`: 전제 제안 투표
- `criterion_proposal_votes`: 기준 제안 투표
- `conclusion_proposal_votes`: 결론 제안 투표
- `option_votes`: 선택지 투표
- `criterion_priorities`: 기준 우선순위
- `comments`: 코멘트
- `idempotency_records`: 멱등성 레코드 (Idempotency-Key 관리)

### 제약 조건

- **UNIQUE 제약**: 중복 방지 (예: `UNIQUE(proposal_id, created_by)`)
  - 일부 proposal 테이블의 UNIQUE 제약은 주석 처리되어 있으며, 서비스 레이어에서 중복 체크 수행
- **CHECK 제약**: 데이터 무결성 (예: `LENGTH(entrance_code) = 6`)
  - `entrance_code` 형식 검증: `^[A-Z0-9]{6}$`
  - 자동 승인 정책 관련 조건부 제약 (예: `assumption_is_auto_approved_by_votes = true → assumption_min_votes_required IS NOT NULL`)
  - `conclusion_approval_threshold_percent` 범위 검증 (1-100)
- **외래 키**: 참조 무결성
- **인덱스**: 성능 최적화를 위한 인덱스 (예: `idx_assumptions_event_id`, `idx_assumptions_created_by`)

### 주요 모델 필드 추가 사항

- **assumptions/criterion 테이블**:
  - `is_deleted`: 삭제 제안이 승인되어 실제로 삭제된 경우 true
  - `is_modified`: 수정 제안이 승인되어 실제로 수정된 경우 true
  - `original_content`: 수정 전 원본 내용 (수정된 경우에만 값이 있음)

---

## 에러 처리

### 커스텀 예외 계층

```python
AppException (기본)
├── NotFoundError (404)
├── ValidationError (400)
├── ConflictError (409)
├── ForbiddenError (403)
└── InternalError (500)
```

### 전역 예외 핸들러

- `AppException`: 커스텀 애플리케이션 예외
- `IntegrityError`: 데이터베이스 무결성 에러
- `OperationalError`: 데이터베이스 연결 에러
- `Exception`: 일반 예외 (예상치 못한 에러)

**에러 응답 형식**:
```json
{
  "error": "NotFoundError",
  "message": "Event not found",
  "detail": "Event with id {event_id} not found"
}
```

---

## 인증 및 보안

### 인증 방식

- **JWT (JSON Web Token)**: 액세스 토큰
- **Refresh Token**: HTTP-only 쿠키로 관리
- **비밀번호 해싱**: bcrypt 사용

### 인증 흐름

1. 로그인 → 액세스 토큰 + 리프레시 토큰 발급
2. API 요청 → `Authorization: Bearer <access_token>` 헤더
3. 토큰 만료 → 리프레시 토큰으로 갱신

### 권한 관리

- **이벤트 관리자**: `event.admin_id == user_id`
- **멤버십 상태**: `PENDING`, `ACCEPTED`, `REJECTED`
- **이벤트 상태**: `NOT_STARTED`, `IN_PROGRESS`, `PAUSED`, `FINISHED`

---

## 프로젝트 구조 요약

```
backend/
├── app/
│   ├── routers/          # HTTP 라우터
│   ├── services/         # 비즈니스 로직
│   ├── repositories/     # 데이터 접근
│   ├── models/           # ORM 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── dependencies/     # 의존성 주입
│   ├── exceptions.py    # 커스텀 예외
│   └── db.py            # 데이터베이스 설정
├── migrations/           # Alembic 마이그레이션
├── docs/                 # 문서
├── main.py              # FastAPI 앱 진입점
├── requirements.txt      # 의존성 목록
└── alembic.ini          # Alembic 설정
```

---

## 설계 원칙

### 1. 관심사의 분리 (Separation of Concerns)

- **Router**: HTTP 요청/응답 처리만
- **Service**: 비즈니스 로직
- **Repository**: 데이터 접근
- **Model**: 데이터 구조

### 2. 단일 책임 원칙 (Single Responsibility Principle)

- 각 클래스는 하나의 책임만 가짐
- 서브 서비스로 기능 분리

### 3. 의존성 역전 원칙 (Dependency Inversion Principle)

- 고수준 모듈이 저수준 모듈에 의존하지 않음
- 인터페이스(의존성)를 통한 추상화

### 4. DRY (Don't Repeat Yourself)

- Base Service로 공통 로직 추출
- 제너릭 Repository로 중복 제거

### 5. 확장성 고려

- Aggregate Repository로 관련 리포지토리 묶기
- 서브 서비스 분리로 기능 추가 용이

---

## 성능 최적화

### 1. N+1 쿼리 방지

- `joinedload` 사용
- 한 번의 쿼리로 관련 데이터 로드

### 2. 인덱스 활용

- 자주 조회되는 컬럼에 인덱스 추가
- UNIQUE 제약으로 중복 방지

### 3. 조건부 업데이트

- `WHERE id = :id AND status = 'PENDING'` 조건으로 중복 방지
- 락 없이 동시성 제어

---

## 확장 가능성

### 향후 추가 가능한 기능

1. **비동기 처리**: Outbox 패턴으로 알림/이메일 발송
2. **캐싱**: Redis를 통한 캐시 레이어
3. **실시간 동기화**: WebSocket 또는 SSE
4. **로깅**: 구조화된 로깅 시스템
5. **모니터링**: 메트릭 수집 및 알림

---

**작성일**: 2024년
**최종 수정일**: 2024년
