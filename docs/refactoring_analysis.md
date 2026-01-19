# Event 모듈 리팩토링 공통 의존성 분석

## 1. Service 메서드 사용 패턴

### 공통으로 사용되는 메서드 (여러 Router에서 사용)

| 메서드 | 사용 위치 | 공통도 |
|--------|----------|--------|
| `verify_admin()` | Event_Setting (get_event_setting, update_event, get_event_memberships) | ⭐⭐⭐ 높음 |
| `get_event_with_all_relations()` | Event_Setting, Event_Detail | ⭐⭐ 중간 |
| `get_event_with_relations()` | Event_Overview | ⭐ 낮음 |
| `count_accepted_members()` | Home, Event_Overview, Event_Setting (update) | ⭐⭐ 중간 |
| `get_membership_status()` | Event_Overview, Event_Detail | ⭐⭐ 중간 |
| `check_entrance_code_availability()` | Event_Creation (check, generate) | ⭐ 낮음 |
| `get_random_code()` | Event_Creation (generate) | ⭐ 낮음 |

### 기능별로만 사용되는 메서드

| 기능 | 메서드 | 독립성 |
|------|--------|--------|
| **Home** | `get_events_participated()` | ✅ 독립 |
| **Event_Creation** | `create_event()`, `attach_options()`, `attach_assumptions()`, `attach_criteria()`, `_create_event_from_request()` | ✅ 독립 |
| **Event_Overview** | `get_event_overview()` | ✅ 독립 |
| **Event_Detail** | `get_event_detail()` | ✅ 독립 |
| **Event_Setting** | `get_event_setting()`, `update_event()`, `_update_options()`, `_update_assumptions()`, `_update_criteria()` | ⚠️ `verify_admin()` 공통 사용 |

## 2. Schema 공통 사용 패턴

### 공통으로 사용되는 Schema

| Schema | 사용 위치 | 공통도 |
|--------|----------|--------|
| `OptionInfo` | Event_Overview, Event_Setting, Event_Detail | ⭐⭐⭐ 높음 |
| `AdminInfo` | Event_Overview | ⭐ 낮음 |
| `EventResponse` | Event_Creation, Event_Setting (update) | ⭐⭐ 중간 |
| `OptionAttachRequest` | Event_Creation | ⭐ 낮음 |
| `AssumptionAttachRequest` | Event_Creation | ⭐ 낮음 |
| `CriterionAttachRequest` | Event_Creation | ⭐ 낮음 |
| `AssumptionInfo` | Event_Setting | ⭐ 낮음 |
| `CriterionInfo` | Event_Setting | ⭐ 낮음 |

### 기능별로만 사용되는 Schema

| 기능 | Schema | 독립성 |
|------|--------|--------|
| **Home** | `EventListItemResponse` | ✅ 독립 |
| **Event_Creation** | `EventCreateRequest`, `EntranceCodeCheckRequest`, `EntranceCodeCheckResponse`, `EntranceCodeGenerateResponse` | ✅ 독립 |
| **Event_Overview** | `EventOverviewResponse`, `EntranceCodeEntryRequest`, `EventEntryResponse` | ✅ 독립 |
| **Event_Detail** | `EventDetailResponse`, `AssumptionProposalInfo`, `CriteriaProposalInfo`, `ConclusionProposalInfo`, `AssumptionWithProposals`, `CriterionWithProposals`, `ProposalVoteInfo` | ✅ 독립 |
| **Event_Setting** | `EventSettingResponse`, `EventUpdateRequest`, `OptionUpdateItem`, `AssumptionUpdateItem`, `CriterionUpdateItem` | ✅ 독립 |
| **Membership** | `MembershipResponse`, `BulkMembershipResponse`, `MembershipListItemResponse` | ✅ 독립 |

## 3. Router 공통 패턴

### 공통 의존성

| 의존성 | 사용 위치 | 공통도 |
|--------|----------|--------|
| `EventService` | 모든 Router | ⭐⭐⭐ 높음 |
| `MembershipService` | Event_Creation, Event_Overview, Event_Setting | ⭐⭐ 중간 |
| `get_current_user` | 모든 Router | ⭐⭐⭐ 높음 |
| `get_event_service` | 모든 Router | ⭐⭐⭐ 높음 |

## 4. Repository 공통 사용 패턴

### 공통으로 사용되는 Repository 메서드

| Repository | 메서드 | 사용 위치 | 공통도 |
|-----------|--------|----------|--------|
| `event` | `get_by_id()` | verify_admin (여러 곳에서 사용) | ⭐⭐⭐ 높음 |
| `event` | `get_event_with_all_relations()` | Event_Setting, Event_Detail | ⭐⭐ 중간 |
| `event` | `get_event_with_relations()` | Event_Overview | ⭐ 낮음 |
| `event` | `count_accepted_members()` | Home, Event_Overview, Event_Setting | ⭐⭐ 중간 |
| `event` | `get_membership_status()` | Event_Overview, Event_Detail | ⭐⭐ 중간 |
| `proposal` | 모든 메서드 | Event_Detail만 사용 | ⭐ 낮음 |

## 5. 공통 로직 분석

### 높은 공통도 (Base Service로 추출 권장)

1. **`verify_admin()`** - 관리자 권한 확인
   - Event_Setting의 모든 기능에서 사용
   - 재사용 가능성이 높음

2. **`get_event_with_all_relations()`** - 이벤트 전체 조회
   - Event_Setting, Event_Detail에서 사용
   - 공통 유틸리티로 추출 가능

3. **`count_accepted_members()`** - 참가 인원 카운트
   - Home, Event_Overview, Event_Setting에서 사용
   - 공통 유틸리티로 추출 가능

### 중간 공통도 (선택적 추출)

1. **`get_membership_status()`** - 멤버십 상태 조회
   - Event_Overview, Event_Detail에서 사용
   - 공통 유틸리티로 추출 가능하나 필수는 아님

### 낮은 공통도 (분리 가능)

1. **Event_Creation 관련 메서드들** - 완전 독립
2. **Event_Detail 관련 메서드들** - 완전 독립
3. **Event_Overview 관련 메서드들** - 완전 독립

## 6. 결론 및 권장사항

### 공통 의존성 요약

- **공통 Service 메서드**: 3개 (`verify_admin`, `get_event_with_all_relations`, `count_accepted_members`)
- **공통 Schema**: 1개 (`OptionInfo`)
- **공통 의존성**: `EventService`, `get_current_user`, `get_event_service` (모든 Router에서 사용)

### 리팩토링 전략

#### ✅ 추천: 기능별 분리 + 공통 모듈 추출

```
app/
├── services/
│   ├── event/
│   │   ├── __init__.py
│   │   ├── base.py              # 공통 로직 (verify_admin, 공통 조회 메서드)
│   │   ├── home_service.py      # Home 관련
│   │   ├── creation_service.py  # Event_Creation 관련
│   │   ├── overview_service.py  # Event_Overview 관련
│   │   ├── detail_service.py    # Event_Detail 관련
│   │   └── setting_service.py   # Event_Setting 관련
│   └── event_service.py         # (기존 파일, 점진적 마이그레이션)
│
├── schemas/
│   ├── event/
│   │   ├── __init__.py
│   │   ├── common.py            # 공통 스키마 (OptionInfo 등)
│   │   ├── home.py
│   │   ├── creation.py
│   │   ├── overview.py
│   │   ├── detail.py
│   │   └── setting.py
│   └── event.py                 # (기존 파일, 점진적 마이그레이션)
```

### 공통 모듈 구성

#### `services/event/base.py`
```python
class EventBaseService:
    """Event 관련 공통 서비스 로직"""
    
    def verify_admin(self, event_id: UUID, user_id: UUID) -> Event:
        """이벤트 관리자 권한 확인"""
        ...
    
    def get_event_with_all_relations(self, event_id: UUID) -> Event:
        """이벤트 전체 조회 (모든 관계 포함)"""
        ...
    
    def count_accepted_members(self, event_id: UUID) -> int:
        """참가 인원 카운트"""
        ...
```

#### `schemas/event/common.py`
```python
class OptionInfo(BaseModel):
    """선택지 정보 (공통)"""
    ...
```

### 분리 우선순위

1. **1단계**: 공통 모듈 추출 (`base.py`, `common.py`)
2. **2단계**: 독립적인 기능부터 분리 (Home, Event_Creation, Event_Overview, Event_Detail)
3. **3단계**: 공통 의존성이 있는 기능 분리 (Event_Setting)

### 예상 효과

- **파일 크기 감소**: 770줄 → 각 파일 100-200줄
- **응집도 향상**: 기능별로 명확히 분리
- **재사용성 향상**: 공통 로직을 base로 추출
- **유지보수성 향상**: 변경 영향 범위 축소
