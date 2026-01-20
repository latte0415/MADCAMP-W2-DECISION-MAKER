# Dev API 스펙 문서

개발 및 테스트를 위한 CRUD API 스펙입니다. 모든 엔드포인트는 `/dev` prefix가 붙습니다.

## 목차

- [Event API](#event-api)
- [Assumption API](#assumption-api)
- [Criterion API](#criterion-api)
- [Option API](#option-api)
- [EventMembership API](#eventmembership-api)

---

## Event API

### GET /dev/events

이벤트 목록 조회

**Query Parameters:**
- `skip` (int, optional): 건너뛸 개수. 기본값: 0
- `limit` (int, optional): 반환할 최대 개수. 기본값: 100

**Response:**
- Status Code: `200 OK`
- Body: `EventResponse[]`

### GET /dev/events/{event_id}

이벤트 단일 조회

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `200 OK`
- Body: `EventResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### POST /dev/events

이벤트 생성

**Request Body:**
```json
{
  "decision_subject": "string",
  "entrance_code": "string (6자리 대문자/숫자)",
  "assumption_is_auto_approved_by_votes": true,
  "criteria_is_auto_approved_by_votes": true,
  "membership_is_auto_approved": true,
  "conclusion_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 0,
  "criteria_min_votes_required": 0,
  "conclusion_approval_threshold_percent": 50,
  "event_status": "NOT_STARTED",
  "max_membership": 10,
  "admin_id": "uuid"
}
```

**Response:**
- Status Code: `201 Created`
- Body: `EventResponse`

### PATCH /dev/events/{event_id}

이벤트 수정

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:** (모든 필드 optional)
```json
{
  "decision_subject": "string",
  "assumption_is_auto_approved_by_votes": true,
  "criteria_is_auto_approved_by_votes": true,
  "membership_is_auto_approved": true,
  "conclusion_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 0,
  "criteria_min_votes_required": 0,
  "conclusion_approval_threshold_percent": 50,
  "event_status": "IN_PROGRESS",
  "max_membership": 10
}
```

**Response:**
- Status Code: `200 OK`
- Body: `EventResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### DELETE /dev/events/{event_id}

이벤트 삭제

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `204 No Content`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

---

## Assumption API

### GET /dev/events/{event_id}/assumptions

이벤트별 전제 목록 조회

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `200 OK`
- Body: `AssumptionResponse[]`

### GET /dev/assumptions/{assumption_id}

전제 단일 조회

**Path Parameters:**
- `assumption_id` (UUID): 전제 ID

**Response:**
- Status Code: `200 OK`
- Body: `AssumptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Assumption with id {assumption_id} not found"}`

### POST /dev/events/{event_id}/assumptions

전제 생성

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "content": "string",
  "event_id": "uuid",
  "created_by": "uuid"
}
```

**Response:**
- Status Code: `201 Created`
- Body: `AssumptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### PATCH /dev/assumptions/{assumption_id}

전제 수정

**Path Parameters:**
- `assumption_id` (UUID): 전제 ID

**Request Body:** (모든 필드 optional)
```json
{
  "content": "string",
  "updated_by": "uuid"
}
```

**Response:**
- Status Code: `200 OK`
- Body: `AssumptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Assumption with id {assumption_id} not found"}`

### DELETE /dev/assumptions/{assumption_id}

전제 삭제

**Path Parameters:**
- `assumption_id` (UUID): 전제 ID

**Response:**
- Status Code: `204 No Content`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Assumption with id {assumption_id} not found"}`

---

## Criterion API

### GET /dev/events/{event_id}/criteria

이벤트별 기준 목록 조회

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `200 OK`
- Body: `CriterionResponse[]`

### GET /dev/criteria/{criterion_id}

기준 단일 조회

**Path Parameters:**
- `criterion_id` (UUID): 기준 ID

**Response:**
- Status Code: `200 OK`
- Body: `CriterionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Criterion with id {criterion_id} not found"}`

### POST /dev/events/{event_id}/criteria

기준 생성

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "content": "string",
  "event_id": "uuid",
  "created_by": "uuid"
}
```

**Response:**
- Status Code: `201 Created`
- Body: `CriterionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### PATCH /dev/criteria/{criterion_id}

기준 수정

**Path Parameters:**
- `criterion_id` (UUID): 기준 ID

**Request Body:** (모든 필드 optional)
```json
{
  "content": "string",
  "conclusion": "string",
  "updated_by": "uuid"
}
```

**Response:**
- Status Code: `200 OK`
- Body: `CriterionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Criterion with id {criterion_id} not found"}`

### DELETE /dev/criteria/{criterion_id}

기준 삭제

**Path Parameters:**
- `criterion_id` (UUID): 기준 ID

**Response:**
- Status Code: `204 No Content`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Criterion with id {criterion_id} not found"}`

---

## Option API

### GET /dev/events/{event_id}/options

이벤트별 선택지 목록 조회

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `200 OK`
- Body: `OptionResponse[]`

### GET /dev/options/{option_id}

선택지 단일 조회

**Path Parameters:**
- `option_id` (UUID): 선택지 ID

**Response:**
- Status Code: `200 OK`
- Body: `OptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Option with id {option_id} not found"}`

### POST /dev/events/{event_id}/options

선택지 생성

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "content": "string",
  "event_id": "uuid",
  "created_by": "uuid"
}
```

**Response:**
- Status Code: `201 Created`
- Body: `OptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### PATCH /dev/options/{option_id}

선택지 수정

**Path Parameters:**
- `option_id` (UUID): 선택지 ID

**Request Body:** (모든 필드 optional)
```json
{
  "content": "string"
}
```

**Response:**
- Status Code: `200 OK`
- Body: `OptionResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Option with id {option_id} not found"}`

### DELETE /dev/options/{option_id}

선택지 삭제

**Path Parameters:**
- `option_id` (UUID): 선택지 ID

**Response:**
- Status Code: `204 No Content`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Option with id {option_id} not found"}`

---

## EventMembership API

### GET /dev/events/{event_id}/memberships

이벤트별 멤버십 목록 조회

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:**
- Status Code: `200 OK`
- Body: `EventMembershipResponse[]`

### GET /dev/memberships/{membership_id}

멤버십 단일 조회

**Path Parameters:**
- `membership_id` (UUID): 멤버십 ID

**Response:**
- Status Code: `200 OK`
- Body: `EventMembershipResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "EventMembership with id {membership_id} not found"}`

### POST /dev/events/{event_id}/memberships

멤버십 생성

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "membership_status": "PENDING",
  "user_id": "uuid",
  "event_id": "uuid"
}
```

**Response:**
- Status Code: `201 Created`
- Body: `EventMembershipResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "Event with id {event_id} not found"}`

### PATCH /dev/memberships/{membership_id}

멤버십 수정

**Path Parameters:**
- `membership_id` (UUID): 멤버십 ID

**Request Body:** (모든 필드 optional)
```json
{
  "membership_status": "APPROVED",
  "joined_at": "2024-01-01T00:00:00Z"
}
```

**Response:**
- Status Code: `200 OK`
- Body: `EventMembershipResponse`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "EventMembership with id {membership_id} not found"}`

### DELETE /dev/memberships/{membership_id}

멤버십 삭제

**Path Parameters:**
- `membership_id` (UUID): 멤버십 ID

**Response:**
- Status Code: `204 No Content`

**Error:**
- Status Code: `404 Not Found`
- Body: `{"detail": "EventMembership with id {membership_id} not found"}`

---

## Response 스키마

### EventResponse
```json
{
  "id": "uuid",
  "decision_subject": "string",
  "entrance_code": "string",
  "assumption_is_auto_approved_by_votes": true,
  "criteria_is_auto_approved_by_votes": true,
  "membership_is_auto_approved": true,
  "conclusion_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 0,
  "criteria_min_votes_required": 0,
  "conclusion_approval_threshold_percent": 50,
  "event_status": "NOT_STARTED",
  "max_membership": 10,
  "admin_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### AssumptionResponse
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "content": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "updated_at": "2024-01-01T00:00:00Z",
  "updated_by": "uuid"
}
```

### CriterionResponse
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "content": "string",
  "conclusion": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "updated_at": "2024-01-01T00:00:00Z",
  "updated_by": "uuid"
}
```

### OptionResponse
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "content": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### EventMembershipResponse
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "event_id": "uuid",
  "membership_status": "PENDING",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "joined_at": "2024-01-01T00:00:00Z"
}
```

---

## Enum 타입

### EventStatusType
- `NOT_STARTED`
- `IN_PROGRESS`
- `PAUSED`
- `FINISHED`

### MembershipStatusType
- `PENDING`
- `APPROVED`
- `REJECTED`

---

## 참고사항

- 모든 엔드포인트는 `/dev` prefix를 사용합니다.
- UUID는 RFC 4122 형식입니다.
- 날짜/시간은 ISO 8601 형식(UTC)입니다.
- 모든 엔드포인트는 현재 인증 없이 동작합니다 (개발용).
- `updated_at` 필드는 PATCH 요청 시 자동으로 현재 시간으로 업데이트됩니다 (Assumption, Criterion, Option, EventMembership).
