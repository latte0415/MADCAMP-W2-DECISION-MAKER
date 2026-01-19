# 상속 패턴 vs 현재 설계 분석

## 현재 설계 상태

### 현재 구조
```python
# app/services/event_service.py
class EventService:
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        self.db = db
        self.repos = repos
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """공통 메서드"""
        ...
    
    def get_event_overview(self, ...):
        """기능별 메서드"""
        ...
    
    def get_event_detail(self, ...):
        """기능별 메서드"""
        ...
```

**특징:**
- ❌ 상속 구조 없음
- ❌ 공통 메서드가 base 클래스로 분리되지 않음
- ✅ 모든 메서드가 단일 클래스에 존재
- ✅ 인스턴스 메서드로 직접 호출

## 제안된 상속 패턴

### Base 클래스 주입 방식
```python
# app/services/event/base.py
class EventBaseService:
    """Event 관련 공통 서비스 로직"""
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        self.db = db
        self.repos = repos
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        ...
    
    def get_event_with_all_relations(self, event_id: UUID) -> Event:
        """이벤트 전체 조회"""
        ...
    
    def count_accepted_members(self, event_id: UUID) -> int:
        """참가 인원 카운트"""
        ...

# app/services/event/setting_service.py
class EventSettingService(EventBaseService):
    """Event_Setting 관련 서비스"""
    
    def get_event_setting(self, event_id: UUID, user_id: UUID) -> EventSettingResponse:
        # base의 verify_admin 사용
        event = self.verify_admin(event_id, user_id)
        ...
    
    def update_event(self, event_id: UUID, request: EventUpdateRequest, user_id: UUID) -> Event:
        # base의 verify_admin 사용
        event = self.verify_admin(event_id, user_id)
        ...
```

## 비교 분석

### 장점: 상속 패턴

1. **코드 재사용성**
   - 공통 로직을 한 곳에 정의
   - 중복 코드 제거

2. **유지보수성**
   - 공통 로직 변경 시 base만 수정
   - 변경 영향 범위 명확

3. **일관성**
   - 모든 서비스가 동일한 공통 메서드 사용
   - 인터페이스 통일

4. **확장성**
   - 새로운 기능 추가 시 base 상속으로 공통 기능 자동 획득

### 단점: 상속 패턴

1. **의존성 증가**
   - 각 service가 base에 의존
   - base 변경 시 모든 service 영향 가능

2. **복잡도 증가**
   - 상속 계층 구조 이해 필요
   - 디버깅 시 호출 스택 깊어짐

3. **과도한 추상화 위험**
   - 공통 메서드가 적을 경우 오버엔지니어링 가능

### 현재 설계의 문제점

1. **코드 중복 가능성**
   - 공통 메서드가 여러 곳에서 재정의될 수 있음

2. **일관성 부족**
   - 각 service가 독립적으로 구현 시 일관성 저하 가능

3. **유지보수 어려움**
   - 공통 로직 변경 시 여러 파일 수정 필요

## 권장 설계

### ✅ 상속 패턴 추천 (제안된 방식)

**이유:**
1. **공통 메서드가 명확함**: `verify_admin`, `get_event_with_all_relations`, `count_accepted_members`
2. **재사용 빈도 높음**: 여러 service에서 사용
3. **일관성 보장**: 모든 service가 동일한 방식으로 공통 기능 사용
4. **확장성**: 향후 공통 기능 추가 시 base에만 추가하면 됨

### 구현 예시

```python
# app/services/event/base.py
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.event import Event
from app.dependencies.aggregate_repositories import EventAggregateRepositories
from app.exceptions import NotFoundError, ForbiddenError

class EventBaseService:
    """Event 관련 공통 서비스 로직"""
    
    def __init__(self, db: Session, repos: EventAggregateRepositories):
        self.db = db
        self.repos = repos
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        event = self.repos.event.get_by_id(event_id)
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        
        if event.admin_id != user_id:
            raise ForbiddenError(
                message="Forbidden",
                detail="Only event administrator can perform this action"
            )
        
        return event
    
    def get_event_with_all_relations(self, event_id: UUID) -> Event:
        """이벤트 전체 조회 (모든 관계 포함)"""
        event = self.repos.event.get_event_with_all_relations(event_id)
        if not event:
            raise NotFoundError(
                message="Event not found",
                detail=f"Event with id {event_id} not found"
            )
        return event
    
    def count_accepted_members(self, event_id: UUID) -> int:
        """참가 인원 카운트"""
        return self.repos.event.count_accepted_members(event_id)

# app/services/event/setting_service.py
from app.services.event.base import EventBaseService
from app.schemas.event import EventSettingResponse, EventUpdateRequest, EventResponse
from app.models.event import Event

class EventSettingService(EventBaseService):
    """Event_Setting 관련 서비스"""
    
    def get_event_setting(self, event_id: UUID, user_id: UUID) -> EventSettingResponse:
        """이벤트 설정 편집용 정보 조회"""
        # base의 verify_admin 사용
        event = self.verify_admin(event_id, user_id)
        
        # base의 get_event_with_all_relations 사용
        event_with_all = self.get_event_with_all_relations(event_id)
        
        # 나머지 로직...
        ...
    
    def update_event(self, event_id: UUID, request: EventUpdateRequest, user_id: UUID) -> Event:
        """이벤트 정보 수정"""
        # base의 verify_admin 사용
        event = self.verify_admin(event_id, user_id)
        
        # 나머지 로직...
        ...
```

## 결론

### 현재 설계는 상속 패턴을 사용하지 않음

- 모든 메서드가 단일 클래스에 존재
- 공통 메서드가 base로 분리되지 않음

### 제안된 상속 패턴이 더 나은 설계

**이유:**
1. ✅ 공통 로직 명확히 분리
2. ✅ 코드 재사용성 향상
3. ✅ 유지보수성 향상
4. ✅ 일관성 보장
5. ✅ 확장성 향상

**구현 전략:**
1. `EventBaseService` 클래스 생성 (base.py)
2. 공통 메서드 3개 이동 (`verify_admin`, `get_event_with_all_relations`, `count_accepted_members`)
3. 각 기능별 service가 `EventBaseService` 상속
4. 공통 메서드는 `self.verify_admin()` 형태로 호출
