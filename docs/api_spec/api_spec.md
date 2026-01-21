# API 스펙 문서

현재 구현된 API 엔드포인트 명세서입니다.

## 목차

- [공통 정보](#공통-정보)
- [Idempotency (멱등성)](#idempotency-멱등성)
- [인증 API](#인증-api-v1auth)
- [이벤트 API](#이벤트-api-v1)
- [개발용 API](#개발용-api-dev)
- [기타](#기타)

---

## API 요약

### 인증 API (`/auth`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/auth/signup` | 회원가입 | ❌ |
| POST | `/auth/login` | 로그인 (이메일/비밀번호) | ❌ |
| POST | `/auth/google` | 구글 로그인 | ❌ |
| POST | `/auth/refresh` | 액세스 토큰 갱신 | 🍪 |
| POST | `/auth/logout` | 로그아웃 | 🍪 |
| GET | `/auth/me` | 현재 사용자 정보 조회 | 🔐 |
| PATCH | `/auth/me/name` | 사용자 이름 업데이트 | 🔐 |
| GET | `/auth/check-email` | 이메일 중복 확인 | ❌ |
| POST | `/auth/password-reset/request` | 비밀번호 재설정 요청 | ❌ |
| POST | `/auth/password-reset/confirm` | 비밀번호 재설정 확인 | ❌ |

**범례:**
- ❌ 인증 불필요
- 🔐 Bearer Token 필수
- 🍪 Refresh Token 쿠키 사용

### 이벤트 API (`/v1`)

#### 홈/참가 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/participated` | 참가한 이벤트 목록 조회 | 🔐 |

#### 이벤트 생성 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/v1/events` | 이벤트 생성 | 🔐 |
| POST | `/v1/events/entrance-code/check` | 입장 코드 중복 확인 | ❌ |
| GET | `/v1/events/entrance-code/generate` | 랜덤 입장 코드 생성 | ❌ |

#### 이벤트 참가/조회 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/v1/events/entry` | 이벤트 입장 (코드로 참가) | 🔐 |
| GET | `/v1/events/{event_id}/overview` | 이벤트 오버뷰 정보 조회 | 🔐 |

#### 이벤트 상세 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}` | 이벤트 상세 조회 | 🔐 |
| POST | `/v1/events/{event_id}/assumption-proposals` | 전제 제안 생성 | 🔐 |
| POST | `/v1/events/{event_id}/assumption-proposals/{proposal_id}/votes` | 전제 제안 투표 생성 | 🔐 |
| DELETE | `/v1/events/{event_id}/assumption-proposals/{proposal_id}/votes` | 전제 제안 투표 삭제 | 🔐 |
| POST | `/v1/events/{event_id}/criteria-proposals` | 기준 제안 생성 | 🔐 |
| POST | `/v1/events/{event_id}/criteria-proposals/{proposal_id}/votes` | 기준 제안 투표 생성 | 🔐 |
| DELETE | `/v1/events/{event_id}/criteria-proposals/{proposal_id}/votes` | 기준 제안 투표 삭제 | 🔐 |
| POST | `/v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals` | 결론 제안 생성 | 🔐 |
| POST | `/v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes` | 결론 제안 투표 생성 | 🔐 |
| DELETE | `/v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes` | 결론 제안 투표 삭제 | 🔐 |

#### 제안 상태 변경 (관리자용)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| PATCH | `/v1/events/{event_id}/assumption-proposals/{proposal_id}/status` | 전제 제안 상태 변경 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}/criteria-proposals/{proposal_id}/status` | 기준 제안 상태 변경 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}/conclusion-proposals/{proposal_id}/status` | 결론 제안 상태 변경 | 🔐 (관리자) |

#### 코멘트 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}/criteria/{criterion_id}/comments/count` | 코멘트 수 조회 | 🔐 |
| GET | `/v1/events/{event_id}/criteria/{criterion_id}/comments` | 코멘트 목록 조회 | 🔐 |
| POST | `/v1/events/{event_id}/criteria/{criterion_id}/comments` | 코멘트 생성 | 🔐 |
| PATCH | `/v1/events/{event_id}/comments/{comment_id}` | 코멘트 수정 | 🔐 |
| DELETE | `/v1/events/{event_id}/comments/{comment_id}` | 코멘트 삭제 | 🔐 |

#### 실시간 동기화 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}/stream` | 실시간 업데이트 스트림 (SSE) | 🔐 |

#### 투표 관련
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}/votes/me` | 본인 투표 내역 조회 | 🔐 |
| POST | `/v1/events/{event_id}/votes` | 투표 생성/업데이트 | 🔐 |
| GET | `/v1/events/{event_id}/votes/result` | 투표 결과 조회 | 🔐 |

#### 이벤트 설정 관련 (관리자용)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}/setting` | 이벤트 설정 조회 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}` | 이벤트 설정 수정 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}/status` | 이벤트 상태 변경 | 🔐 (관리자) |

#### 멤버십 관리 (관리자용)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/v1/events/{event_id}/memberships` | 멤버십 목록 조회 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}/memberships/{membership_id}/approve` | 멤버십 승인 | 🔐 (관리자) |
| PATCH | `/v1/events/{event_id}/memberships/{membership_id}/reject` | 멤버십 거부 | 🔐 (관리자) |
| POST | `/v1/events/{event_id}/memberships/bulk-approve` | 멤버십 일괄 승인 | 🔐 (관리자) |
| POST | `/v1/events/{event_id}/memberships/bulk-reject` | 멤버십 일괄 거부 | 🔐 (관리자) |

### 개발용 API (`/dev`)

개발 및 테스트를 위한 CRUD API입니다.

| 카테고리 | Endpoints | 설명 |
|----------|-----------|------|
| Events | `GET/POST/PATCH /dev/events` | 이벤트 CRUD |
| Assumptions | `GET/POST/PATCH/DELETE /dev/assumptions` | 전제 CRUD |
| Criteria | `GET/POST/PATCH/DELETE /dev/criteria` | 기준 CRUD |
| Options | `GET/POST/PATCH/DELETE /dev/options` | 선택지 CRUD |
| Memberships | `GET/POST/PATCH/DELETE /dev/memberships` | 멤버십 CRUD |

자세한 내용은 [`dev_api_spec.md`](./dev_api_spec.md)를 참고하세요.

### 기타

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/` | 루트 엔드포인트 | ❌ |
| GET | `/health` | 헬스 체크 | ❌ |

### 통계

- **총 구현된 API**: 49개
  - 인증 API: 10개
  - 이벤트 API: 37개
    - 홈/참가: 1개
    - 생성: 3개
    - 참가/조회: 2개
    - 상세/제안: 10개
    - 제안 상태 변경: 3개
    - 코멘트: 5개
    - 투표: 3개
    - 설정: 3개
    - 멤버십: 5개
    - 이벤트 상태 변경: 1개
  - 개발용 API: 여러 개 (별도 문서 참조)
  - 기타: 2개

- **미구현 API**: 0개

---

## 공통 정보

### Base URL
- 로컬: `http://localhost:8000`
- 프로덕션: 환경에 따라 결정

### 인증 방식
대부분의 API는 Bearer Token 인증을 사용합니다.

**헤더 형식:**
```
Authorization: Bearer <access_token>
```

**Refresh Token:**
- Refresh token은 HTTP-only 쿠키로 관리됩니다.
- 쿠키 이름: `refresh_token`
- Path: `/auth` (refresh, logout 엔드포인트에서 사용)

### 공통 응답 형식

**성공 응답:**
- 각 API별로 정의된 response model 반환

**에러 응답:**
```json
{
  "detail": "에러 메시지"
}
```

**주요 HTTP 상태 코드:**
- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `409 Conflict`: 리소스 충돌 (예: 이메일 중복)
- `500 Internal Server Error`: 서버 오류

---

## Idempotency (멱등성)

### 개요

일부 API 엔드포인트는 네트워크 오류, 타임아웃 등으로 인한 중복 요청을 방지하기 위해 **Idempotency-Key** 헤더를 사용합니다. 같은 키로 동일한 요청을 재시도하면 서버는 저장된 응답을 즉시 반환하여 중복 처리를 방지합니다.

### Idempotency-Key 헤더

**헤더 이름:** `Idempotency-Key`

**헤더 값:** 고유한 문자열 (권장: UUID v4)

**예시:**
```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### 환경별 동작

- **개발 환경**: 헤더가 없으면 자동으로 UUID 생성 (테스트 편의성)
- **운영 환경**: 헤더가 없으면 `400 Bad Request` 에러 반환

### Idempotency가 적용된 엔드포인트

다음 엔드포인트들은 `Idempotency-Key` 헤더가 **필수**입니다:

#### 제안 생성/수정
- `POST /v1/events/{event_id}/assumption-proposals` - 전제 제안 생성
- `POST /v1/events/{event_id}/criteria-proposals` - 기준 제안 생성
- `POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals` - 결론 제안 생성

#### 투표
- `POST /v1/events/{event_id}/votes` - 최종 투표 생성/업데이트

#### 제안 상태 변경 (관리자)
- `PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status` - 전제 제안 상태 변경
- `PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status` - 기준 제안 상태 변경
- `PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status` - 결론 제안 상태 변경

#### 멤버십 관리 (관리자)
- `PATCH /v1/events/{event_id}/memberships/{membership_id}/approve` - 멤버십 승인
- `PATCH /v1/events/{event_id}/memberships/{membership_id}/reject` - 멤버십 거부

### 동작 방식

#### 1. 최초 요청
```
POST /v1/events/{event_id}/votes
Headers:
  Authorization: Bearer <token>
  Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Body:
  {
    "option_id": "uuid",
    "criterion_ids": ["uuid1", "uuid2"]
  }
```

서버는 요청을 처리하고 응답을 저장한 후 반환합니다.

#### 2. 재시도 (동일한 키와 요청)
```
POST /v1/events/{event_id}/votes
Headers:
  Authorization: Bearer <token>
  Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Body:
  {
    "option_id": "uuid",
    "criterion_ids": ["uuid1", "uuid2"]
  }
```

서버는 저장된 응답을 즉시 반환합니다. (중복 처리 없음)

#### 3. 다른 요청에 같은 키 사용 (에러)
```
POST /v1/events/{event_id}/votes
Headers:
  Authorization: Bearer <token>
  Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Body:
  {
    "option_id": "uuid",
    "criterion_ids": ["uuid3", "uuid4"]  // 다른 요청
  }
```

**응답:** `409 Conflict`
```json
{
  "detail": "Idempotency key reused"
}
```

#### 4. 처리 중인 요청 재시도 (에러)
요청이 아직 처리 중일 때 같은 키로 재시도하면:

**응답:** `409 Conflict`
```json
{
  "detail": "Request in progress"
}
```

### 프론트엔드 구현 가이드

#### 1. Idempotency-Key 생성

각 요청마다 고유한 키를 생성합니다. 권장 방법:

```typescript
// UUID v4 생성 (브라우저)
function generateIdempotencyKey(): string {
  return crypto.randomUUID();
}

// 또는 uuid 라이브러리 사용
import { v4 as uuidv4 } from 'uuid';
const idempotencyKey = uuidv4();
```

#### 2. API 호출 래퍼 함수

```typescript
async function apiCallWithIdempotency<T>(
  url: string,
  options: RequestInit,
  idempotencyKey?: string
): Promise<T> {
  const headers = new Headers(options.headers);
  
  // Idempotency-Key가 필요한 엔드포인트인지 확인
  if (requiresIdempotencyKey(url, options.method)) {
    if (!idempotencyKey) {
      idempotencyKey = generateIdempotencyKey();
    }
    headers.set('Idempotency-Key', idempotencyKey);
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`);
  }
  
  return response.json();
}

// Idempotency-Key가 필요한 엔드포인트 확인
function requiresIdempotencyKey(url: string, method?: string): boolean {
  if (method !== 'POST' && method !== 'PATCH') {
    return false;
  }
  
  const idempotencyRequiredPaths = [
    '/assumption-proposals',
    '/criteria-proposals',
    '/conclusion-proposals',
    '/votes',
    '/events/',
  ];
  
  return idempotencyRequiredPaths.some(path => url.includes(path));
}
```

#### 3. 재시도 로직

네트워크 오류나 타임아웃 발생 시 **같은 키**로 재시도:

```typescript
async function createVoteWithRetry(
  eventId: string,
  voteData: VoteCreateRequest,
  maxRetries: number = 3
): Promise<VoteResponse> {
  const idempotencyKey = generateIdempotencyKey();
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await apiCallWithIdempotency(
        `/v1/events/${eventId}/votes`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAccessToken()}`,
          },
          body: JSON.stringify(voteData),
        },
        idempotencyKey // 같은 키로 재시도
      );
    } catch (error) {
      // 네트워크 오류인 경우에만 재시도
      if (attempt < maxRetries - 1 && isNetworkError(error)) {
        await delay(1000 * (attempt + 1)); // 지수 백오프
        continue;
      }
      throw error;
    }
  }
  
  throw new Error('Max retries exceeded');
}
```

#### 4. 에러 처리

```typescript
try {
  await createVoteWithRetry(eventId, voteData);
} catch (error) {
  if (error.response?.status === 409) {
    const detail = error.response.data?.detail || '';
    
    if (detail.includes('Idempotency key reused')) {
      // 다른 요청에 같은 키를 사용한 경우
      // 새로운 키로 재시도하거나 사용자에게 알림
      console.error('Idempotency key conflict. Please try again.');
    } else if (detail.includes('Request in progress')) {
      // 요청이 처리 중인 경우
      // 잠시 후 재시도하거나 사용자에게 대기 알림
      console.warn('Request is being processed. Please wait.');
    }
  }
  // 다른 에러 처리...
}
```

#### 5. React Hook 예시

```typescript
import { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

function useIdempotentApiCall<T>() {
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null);
  
  const callApi = async (
    url: string,
    options: RequestInit
  ): Promise<T> => {
    // 새로운 요청이면 새 키 생성
    const key = idempotencyKey || uuidv4();
    setIdempotencyKey(key);
    
    const headers = new Headers(options.headers);
    headers.set('Idempotency-Key', key);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 성공 시 키 초기화 (다음 요청을 위해)
      setIdempotencyKey(null);
      
      return data;
    } catch (error) {
      // 네트워크 오류 시 키 유지 (재시도 가능)
      throw error;
    }
  };
  
  const resetKey = () => {
    setIdempotencyKey(null);
  };
  
  return { callApi, resetKey };
}

// 사용 예시
function VoteButton({ eventId, voteData }: Props) {
  const { callApi, resetKey } = useIdempotentApiCall<VoteResponse>();
  const [loading, setLoading] = useState(false);
  
  const handleVote = async () => {
    setLoading(true);
    try {
      await callApi(`/v1/events/${eventId}/votes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(voteData),
      });
      
      // 성공 시 키가 자동으로 초기화됨
      alert('투표가 완료되었습니다.');
    } catch (error) {
      // 네트워크 오류 시 사용자가 재시도 버튼을 누르면
      // 같은 키로 자동 재시도됨
      alert('투표 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <button onClick={handleVote} disabled={loading}>
      {loading ? '투표 중...' : '투표하기'}
    </button>
  );
}
```

### 주의사항

1. **키 재사용 금지**: 한 번 사용한 키는 다른 요청에 사용하면 안 됩니다.
2. **요청 바디 일치**: 같은 키로 재시도할 때는 요청 바디가 완전히 동일해야 합니다.
3. **키 저장**: 재시도를 위해 키를 일시적으로 저장해두는 것을 권장합니다.
4. **TTL**: Idempotency 키는 24시간 후 만료됩니다. 만료 후에는 새로운 키를 사용해야 합니다.
5. **사용자 경험**: 네트워크 오류 시 자동 재시도 로직을 구현하여 사용자 경험을 개선하세요.

### 요약

- ✅ 각 요청마다 고유한 `Idempotency-Key` 생성 (UUID v4 권장)
- ✅ 네트워크 오류 시 **같은 키**로 재시도
- ✅ 성공한 요청의 키는 재사용하지 않음
- ✅ 다른 요청에는 **새로운 키** 사용
- ✅ `409 Conflict` 에러 시 적절히 처리

---

## 인증 API (`/auth`)

### POST /auth/signup

회원가입

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Validation:**
- `email`: 이메일 형식 필수
- `password`: 8-20자

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": null,
    "is_active": true
  }
}
```

**에러:**
- `409 Conflict`: 이미 사용 중인 이메일

---

### POST /auth/login

로그인 (이메일/비밀번호)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": null,
    "is_active": true
  }
}
```

**에러:**
- `401 Unauthorized`: 이메일/비밀번호가 일치하지 않음
- `403 Forbidden`: 
  - 비활성화된 사용자
  - 구글 계정과 연결된 이메일 (구글로 로그인 필요)

---

### POST /auth/google

구글 로그인

**Request Body:**
```json
{
  "id_token": "google_id_token_jwt"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": null,
    "is_active": true
  }
}
```

**에러:**
- `401 Unauthorized`: 구글 토큰 오류
- `403 Forbidden`: 비활성화된 사용자

---

### POST /auth/refresh

액세스 토큰 갱신

**쿠키:**
- `refresh_token`: HTTP-only 쿠키로 자동 전송

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": null,
    "is_active": true
  }
}
```

**에러:**
- `401 Unauthorized`: Refresh token이 없거나 유효하지 않음

**참고:**
- Refresh token rotation 적용 (새로운 refresh token이 쿠키로 설정됨)

---

### POST /auth/logout

로그아웃

**쿠키:**
- `refresh_token`: HTTP-only 쿠키로 자동 전송

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

### GET /auth/me

현재 사용자 정보 조회

**인증:** Bearer Token 필수

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "홍길동",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### PATCH /auth/me/name

사용자 이름 업데이트

**인증:** Bearer Token 필수

**Request Body:**
```json
{
  "name": "홍길동"
}
```

**Validation:**
- `name`: 1-100자 (필수)

**Response:** `200 OK`
```json
{
  "message": "이름이 성공적으로 업데이트되었습니다."
}
```

**에러:**
- `404 Not Found`: 사용자를 찾을 수 없음
- `400 Bad Request`: 이름 형식 오류 (1-100자)

**참고:**
- 회원가입 시 이름은 받지 않으며, 메인 화면에서 팝업으로 요청할 수 있습니다.
- 이름은 NULL 가능하며, 없을 경우 `null`로 반환됩니다.

---

### GET /auth/check-email

이메일 중복 확인

**Query Parameters:**
- `email` (EmailStr, 필수): 확인할 이메일 주소

**Response:** `200 OK`
```json
{
  "exists": true
}
```

**참고:**
- 이메일이 존재하면 `exists: true`, 없으면 `exists: false`를 반환합니다.
- 인증이 필요하지 않습니다.

---

### POST /auth/password-reset/request

비밀번호 재설정 요청

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "비밀번호 재설정 링크를 이메일로 전송했습니다."
}
```

**에러:**
- `404 Not Found`: 사용자가 존재하지 않음
- `403 Forbidden`: 비활성화된 사용자
- `502 Bad Gateway`: 이메일 전송 실패

---

### POST /auth/password-reset/confirm

비밀번호 재설정 확인

**Request Body:**
```json
{
  "token": "reset_token",
  "new_password": "newpassword123"
}
```

**Validation:**
- `token`: 비밀번호 재설정 토큰
- `new_password`: 8-20자

**Response:** `200 OK`
```json
{
  "message": "비밀번호가 성공적으로 재설정되었습니다."
}
```

**에러:**
- `401 Unauthorized`: 유효하지 않은 리셋 토큰
- `403 Forbidden`: 비활성화된 사용자

**참고:**
- 비밀번호 재설정 시 모든 refresh token이 무효화됩니다.

---

## 이벤트 API (`/v1`)

### GET /v1/events/participated

참가한 이벤트 목록 조회

**인증:** Bearer Token 필수

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "decision_subject": "이벤트 제목",
    "event_status": "NOT_STARTED",
    "admin_id": "uuid",
    "admin_name": "admin@example.com",
    "entrance_code": "ABC123",
    "participant_count": 5,
    "is_admin": false,
    "membership_status": "ACCEPTED"
  }
]
```

---

### POST /v1/events

이벤트 생성

**인증:** Bearer Token 필수

**Request Body:**
```json
{
  "decision_subject": "의사결정 주제",
  "entrance_code": "ABC123",
  "assumption_is_auto_approved_by_votes": true,
  "criteria_is_auto_approved_by_votes": true,
  "membership_is_auto_approved": true,
  "conclusion_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 3,
  "criteria_min_votes_required": 3,
  "conclusion_approval_threshold_percent": 50,
  "max_membership": 10,
  "options": [
    { "content": "선택지 1" },
    { "content": "선택지 2" }
  ],
  "assumptions": [
    { "content": "전제 1" }
  ],
  "criteria": [
    { "content": "기준 1" }
  ]
}
```

**Validation:**
- `entrance_code`: 6자리 대문자/숫자 (^[A-Z0-9]{6}$)
- `max_membership`: 1 이상
- `conclusion_approval_threshold_percent`: 1-100 (optional)

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "decision_subject": "의사결정 주제",
  "entrance_code": "ABC123",
  "assumption_is_auto_approved_by_votes": true,
  "criteria_is_auto_approved_by_votes": true,
  "membership_is_auto_approved": true,
  "conclusion_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 3,
  "criteria_min_votes_required": 3,
  "conclusion_approval_threshold_percent": 50,
  "event_status": "NOT_STARTED",
  "max_membership": 10,
  "admin_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

**참고:**
- 이벤트 생성자에게 자동으로 관리자 멤버십이 생성됩니다.

---

### POST /v1/events/entrance-code/check

입장 코드 중복 확인

**Request Body:**
```json
{
  "entrance_code": "ABC123"
}
```

**Response:** `200 OK`
```json
{
  "entrance_code": "ABC123",
  "is_available": true
}
```

---

### GET /v1/events/entrance-code/generate

랜덤 입장 코드 생성

**Response:** `200 OK`
```json
{
  "code": "XYZ789"
}
```

---

### POST /v1/events/entry

이벤트 입장 (코드로 참가)

**인증:** Bearer Token 필수

**Request Body:**
```json
{
  "entrance_code": "ABC123"
}
```

**Response:** `201 Created`
```json
{
  "message": "참가 신청이 완료되었습니다.",
  "event_id": "uuid"
}
```

**에러:**
- `404 Not Found`: 입장 코드에 해당하는 이벤트 없음
- `409 Conflict`: 이미 참가 중이거나 참가 신청 중

---

### GET /v1/events/{event_id}/overview

이벤트 오버뷰 정보 조회

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "event": {
    "id": "uuid",
    "decision_subject": "의사결정 주제",
    "event_status": "NOT_STARTED",
    "entrance_code": "ABC123"
  },
  "options": [
    {
      "id": "uuid",
      "content": "선택지 1"
    }
  ],
  "admin": {
    "id": "uuid",
    "email": "admin@example.com"
  },
  "participant_count": 5,
  "membership_status": "ACCEPTED",
  "can_enter": true
}
```

---

### GET /v1/events/{event_id}/setting

이벤트 설정 조회 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "decision_subject": "의사결정 주제",
  "options": [
    {
      "id": "uuid",
      "content": "선택지 1"
    }
  ],
  "assumptions": [
    {
      "id": "uuid",
      "content": "전제 1"
    }
  ],
  "criteria": [
    {
      "id": "uuid",
      "content": "기준 1"
    }
  ],
  "max_membership": 10,
  "assumption_is_auto_approved_by_votes": true,
  "assumption_min_votes_required": 3,
  "criteria_is_auto_approved_by_votes": true,
  "criteria_min_votes_required": 3,
  "conclusion_approval_threshold_percent": 50,
  "membership_is_auto_approved": true,
  "entrance_code": "ABC123"
}
```

---

### PATCH /v1/events/{event_id}

이벤트 설정 수정 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:** (모든 필드 optional)
```json
{
  "decision_subject": "수정된 주제",
  "max_membership": 20,
  "options": [
    { "id": null, "content": "새 선택지" },
    { "id": "uuid", "content": "수정된 선택지" },
    { "id": "uuid", "content": null }
  ],
  "assumptions": [
    { "id": null, "content": "새 전제" },
    { "id": "uuid", "content": "수정된 전제" },
    { "id": "uuid", "content": null }
  ],
  "criteria": [
    { "id": null, "content": "새 기준" },
    { "id": "uuid", "content": "수정된 기준" },
    { "id": "uuid", "content": null }
  ],
  "assumption_is_auto_approved_by_votes": false,
  "assumption_min_votes_required": 5,
  "criteria_is_auto_approved_by_votes": false,
  "criteria_min_votes_required": 5,
  "conclusion_approval_threshold_percent": 60,
  "membership_is_auto_approved": false
}
```

**수정 규칙:**
- 기본 정보 (except 최대 인원): `NOT_STARTED`인 경우만 수정 가능
- 최대 인원: `FINISHED`가 아닐 때 수정 가능 (현재 인원보다 작을 수 없음)
- 투표 허용 정책 + 입장 정책: `FINISHED`가 아닐 때 수정 가능
- options/assumptions/criteria:
  - `id: null, content: "..."` → 추가
  - `id: "uuid", content: "..."` → 수정
  - `id: "uuid", content: null` → 삭제

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "decision_subject": "수정된 주제",
  ...
}
```

**참고:**
- 이 엔드포인트는 Idempotency-Key를 사용하지 않습니다.

---

### PATCH /v1/events/{event_id}/memberships/{membership_id}/approve

멤버십 승인 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `membership_id` (UUID): 멤버십 ID

**Idempotency-Key:** 필수 헤더

**Response:** `200 OK`
```json
{
  "message": "Membership approved successfully",
  "membership_id": "uuid",
  "membership_status": "ACCEPTED"
}
```

**에러:**
- `400 Bad Request`: 최대 인원 초과

---

### PATCH /v1/events/{event_id}/memberships/{membership_id}/reject

멤버십 거부 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `membership_id` (UUID): 멤버십 ID

**Idempotency-Key:** 필수 헤더

**Response:** `200 OK`
```json
{
  "message": "Membership rejected successfully",
  "membership_id": "uuid",
  "membership_status": "REJECTED"
}
```

---

### POST /v1/events/{event_id}/memberships/bulk-approve

멤버십 일괄 승인 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "message": "Bulk approval completed",
  "approved_count": 5,
  "failed_count": 2
}
```

---

### POST /v1/events/{event_id}/memberships/bulk-reject

멤버십 일괄 거부 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "message": "Bulk rejection completed",
  "rejected_count": 3
}
```

---

### GET /v1/events/{event_id}/memberships

멤버십 목록 조회 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
[
  {
    "user_id": "uuid",
    "membership_id": "uuid",
    "name": "사용자 이름",
    "email": "user@example.com",
    "status": "ACCEPTED",
    "created_at": "2024-01-01T00:00:00Z",
    "joined_at": "2024-01-01T01:00:00Z",
    "is_me": false,
    "is_admin": true
  }
]
```

---

### GET /v1/events/{event_id}

이벤트 상세 조회

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "decision_subject": "의사결정 주제",
  "event_status": "IN_PROGRESS",
  "is_admin": false,
  "options": [
    {
      "id": "uuid",
      "content": "선택지 1"
    }
  ],
  "assumptions": [
    {
      "id": "uuid",
      "content": "전제 1",
      "is_deleted": false,
      "is_modified": false,
      "original_content": null,
      "modified_at": null,
      "deleted_at": null,
      "proposals": [...]
    }
  ],
  "criteria": [
    {
      "id": "uuid",
      "content": "기준 1",
      "conclusion": null,
      "is_deleted": false,
      "is_modified": false,
      "original_content": null,
      "modified_at": null,
      "deleted_at": null,
      "proposals": [...],
      "conclusion_proposals": [...]
    }
  ],
  "assumption_creation_proposals": [...],
  "criteria_creation_proposals": [...],
  "current_participants_count": 10,
  "voted_participants_count": 8
}
```

**참고:**
- 각 제안에 대한 투표 정보 포함
- ACCEPTED 멤버십만 조회 가능
- `current_participants_count`: 현재 참가 인원 수 (ACCEPTED 멤버십 기준)
- `voted_participants_count`: 투표 완료 인원 수 (최종 투표 완료 기준)

---

### POST /v1/events/{event_id}/assumption-proposals

전제 제안 생성

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "proposal_category": "CREATION",
  "assumption_id": null,
  "proposal_content": "새 전제 내용",
  "reason": "이유 (선택)"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "assumption_id": null,
  "proposal_status": "PENDING",
  "proposal_category": "CREATION",
  "proposal_content": "새 전제 내용",
  "reason": "이유",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 0,
  "has_voted": false
}
```

**에러:**
- `400 Bad Request`: 이벤트가 IN_PROGRESS 상태가 아님
- `403 Forbidden`: ACCEPTED 멤버십이 아님
- `409 Conflict`: 중복 제안 존재

---

### POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes

전제 제안 투표 생성

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `201 Created`
```json
{
  "message": "Vote created successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 5
}
```

**에러:**
- `400 Bad Request`: 제안이 PENDING 상태가 아님
- `409 Conflict`: 이미 투표함

---

### DELETE /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes

전제 제안 투표 삭제

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `200 OK`
```json
{
  "message": "Vote deleted successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 4
}
```

**에러:**
- `404 Not Found`: 투표를 찾을 수 없음

---

### POST /v1/events/{event_id}/criteria-proposals

기준 제안 생성

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "proposal_category": "MODIFICATION",
  "criteria_id": "uuid",
  "proposal_content": "수정된 기준 내용",
  "reason": "이유 (선택)"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "criteria_id": "uuid",
  "proposal_status": "PENDING",
  "proposal_category": "MODIFICATION",
  "proposal_content": "수정된 기준 내용",
  "reason": "이유",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 0,
  "has_voted": false
}
```

---

### POST /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes

기준 제안 투표 생성

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `201 Created`
```json
{
  "message": "Vote created successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 5
}
```

---

### DELETE /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes

기준 제안 투표 삭제

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `200 OK`
```json
{
  "message": "Vote deleted successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 4
}
```

---

### POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals

결론 제안 생성

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `criterion_id` (UUID): 기준 ID

**Request Body:**
```json
{
  "proposal_content": "결론 내용"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "criterion_id": "uuid",
  "proposal_status": "PENDING",
  "proposal_content": "결론 내용",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 0,
  "has_voted": false
}
```

---

### POST /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes

결론 제안 투표 생성

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `201 Created`
```json
{
  "message": "Vote created successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 5
}
```

---

### DELETE /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes

결론 제안 투표 삭제

**인증:** Bearer Token 필수

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Response:** `200 OK`
```json
{
  "message": "Vote deleted successfully",
  "vote_id": "uuid",
  "proposal_id": "uuid",
  "vote_count": 4
}
```

---

### PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status

전제 제안 상태 변경 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Request Body:**
```json
{
  "status": "ACCEPTED"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "assumption_id": null,
  "proposal_status": "ACCEPTED",
  "proposal_category": "CREATION",
  "proposal_content": "새 전제 내용",
  "reason": "이유",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 5,
  "has_voted": false
}
```

**에러:**
- `400 Bad Request`: 제안이 PENDING 상태가 아님
- `403 Forbidden`: 관리자 권한 없음
- `404 Not Found`: 제안을 찾을 수 없음

**참고:**
- PENDING 상태만 변경 가능
- ACCEPTED 시 제안이 자동으로 적용됨
- status는 `ACCEPTED` 또는 `REJECTED`만 허용

---

### PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status

기준 제안 상태 변경 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Request Body:**
```json
{
  "status": "ACCEPTED"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "criteria_id": "uuid",
  "proposal_status": "ACCEPTED",
  "proposal_category": "MODIFICATION",
  "proposal_content": "수정된 기준 내용",
  "reason": "이유",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 5,
  "has_voted": false
}
```

**참고:**
- PENDING 상태만 변경 가능
- ACCEPTED 시 제안이 자동으로 적용됨

---

### PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status

결론 제안 상태 변경 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `proposal_id` (UUID): 제안 ID

**Request Body:**
```json
{
  "status": "ACCEPTED"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "criterion_id": "uuid",
  "proposal_status": "ACCEPTED",
  "proposal_content": "결론 내용",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "uuid",
  "vote_count": 5,
  "has_voted": false
}
```

**참고:**
- PENDING 상태만 변경 가능
- ACCEPTED 시 제안이 자동으로 적용됨

---

### GET /v1/events/{event_id}/criteria/{criterion_id}/comments/count

코멘트 수 조회

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `criterion_id` (UUID): 기준 ID

**Response:** `200 OK`
```json
{
  "count": 10
}
```

---

### GET /v1/events/{event_id}/criteria/{criterion_id}/comments

코멘트 목록 조회

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `criterion_id` (UUID): 기준 ID

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "criterion_id": "uuid",
    "content": "코멘트 내용",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": null,
    "created_by": "uuid",
    "creator": {
      "id": "uuid",
      "name": "홍길동",
      "email": "user@example.com"
    }
  }
]
```

**참고:**
- 최신순으로 정렬됨
- 작성자 정보 포함

---

### POST /v1/events/{event_id}/criteria/{criterion_id}/comments

코멘트 생성

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `criterion_id` (UUID): 기준 ID

**Request Body:**
```json
{
  "content": "코멘트 내용"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "criterion_id": "uuid",
  "content": "코멘트 내용",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null,
  "created_by": "uuid",
  "creator": {
    "id": "uuid",
    "name": "홍길동",
    "email": "user@example.com"
  }
}
```

---

### PATCH /v1/events/{event_id}/comments/{comment_id}

코멘트 수정

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요, 본인 코멘트만)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `comment_id` (UUID): 코멘트 ID

**Request Body:**
```json
{
  "content": "수정된 코멘트 내용"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "criterion_id": "uuid",
  "content": "수정된 코멘트 내용",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z",
  "created_by": "uuid",
  "creator": {
    "id": "uuid",
    "name": "홍길동",
    "email": "user@example.com"
  }
}
```

**에러:**
- `403 Forbidden`: 본인이 작성한 코멘트가 아님

---

### DELETE /v1/events/{event_id}/comments/{comment_id}

코멘트 삭제

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요, 본인 코멘트만)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID
- `comment_id` (UUID): 코멘트 ID

**Response:** `204 No Content`

**에러:**
- `403 Forbidden`: 본인이 작성한 코멘트가 아님

---

### GET /v1/events/{event_id}/stream

실시간 업데이트 스트림 (Server-Sent Events)

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Query Parameters:**
- `last_event_id` (UUID, 선택): 마지막으로 받은 이벤트 ID (재연결 시 사용)

**Headers:**
- `Authorization: Bearer <access_token>` (필수)
- `Last-Event-ID: <event_id>` (재연결 시, 쿼리 파라미터보다 우선)

**Response:** `200 OK` (`text/event-stream`)

**응답 형식**:
```
id: <outbox_event_id>
data: {"id": "...", "event_type": "...", "payload": {...}, "created_at": "..."}

```

**이벤트 타입**:
- `proposal.created.v1`: Proposal 생성
  - `payload`: `{"proposal_id": "uuid", "proposal_type": "assumption" | "criteria" | "conclusion"}`
- `proposal.vote.created.v1`: Proposal 투표 생성
  - `payload`: `{"proposal_id": "uuid", "proposal_type": "assumption" | "criteria" | "conclusion"}`
- `proposal.vote.deleted.v1`: Proposal 투표 삭제
  - `payload`: `{"proposal_id": "uuid", "proposal_type": "assumption" | "criteria" | "conclusion"}`
- `proposal.approved.v1`: Proposal 승인
  - `payload`: `{"proposal_id": "uuid", "proposal_type": "assumption" | "criteria" | "conclusion", "event_id": "uuid", "approved_by": "uuid" | null}`
- `proposal.rejected.v1`: Proposal 거부
  - `payload`: `{"proposal_id": "uuid", "proposal_type": "assumption" | "criteria" | "conclusion", "event_id": "uuid", "rejected_by": "uuid"}`
- `comment.created.v1`: 코멘트 생성
  - `payload`: `{"comment_id": "uuid", "criterion_id": "uuid"}`

**Heartbeat**:
서버는 30초마다 `: ping` 형태의 heartbeat를 전송합니다.

**재연결**:
- 네트워크 오류 시 `retry: 5000` 헤더가 전송됩니다.
- `Last-Event-ID` 헤더 또는 쿼리 파라미터를 사용하여 마지막 이벤트 이후부터 다시 받을 수 있습니다.

**에러:**
- `403 Forbidden`: ACCEPTED 멤버십이 아님

**참고:**
- 프론트엔드 사용 가이드는 [`frontend_realtime_guide.md`](../frontend_realtime_guide.md)를 참고하세요.
- ID 기반 커서를 사용하여 누락/중복 없이 이벤트를 전송합니다.
- 이벤트는 1초마다 폴링되며, 새로운 이벤트가 있을 때만 전송됩니다.

---

### GET /v1/events/{event_id}/votes/me

본인 투표 내역 조회

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "option_id": "uuid",
  "criterion_order": ["uuid1", "uuid2", "uuid3"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z",
  "decision_subject": "의사결정 주제",
  "options": [
    {
      "id": "uuid",
      "content": "선택지 1"
    }
  ],
  "criteria": [
    {
      "id": "uuid",
      "content": "기준 1"
    }
  ]
}
```

**참고:**
- 투표하지 않은 경우 `option_id`가 `null`로 반환됨
- `criterion_order`는 기준 ID 리스트 (순서대로, 0번째 = 1순위)

---

### POST /v1/events/{event_id}/votes

투표 생성/업데이트 (upsert 패턴)

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Idempotency-Key:** 필수 헤더

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "option_id": "uuid",
  "criterion_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Validation:**
- `option_id`: 해당 이벤트의 선택지여야 함
- `criterion_ids`: 
  - 모든 기준이 해당 이벤트의 기준이어야 함
  - 중복 불가
  - 빈 리스트 불가
  - 모든 활성화된 기준이 포함되어야 함

**Response:** `201 Created`
```json
{
  "option_id": "uuid",
  "criterion_order": ["uuid1", "uuid2", "uuid3"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**에러:**
- `400 Bad Request`: 
  - 이벤트가 IN_PROGRESS 상태가 아님
  - 잘못된 option_id 또는 criterion_ids
  - 모든 활성화된 기준이 포함되지 않음
- `403 Forbidden`: ACCEPTED 멤버십이 아님
- `404 Not Found`: option 또는 criterion을 찾을 수 없음

**참고:**
- 이미 투표한 경우 기존 투표를 삭제하고 새로 생성 (업데이트)
- IN_PROGRESS 상태에서만 투표 가능

---

### GET /v1/events/{event_id}/votes/result

투표 결과 조회

**인증:** Bearer Token 필수 (ACCEPTED 멤버십 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Response:** `200 OK`
```json
{
  "total_participants_count": 10,
  "voted_participants_count": 8,
  "option_vote_counts": [
    {
      "option_id": "uuid",
      "option_content": "선택지 1",
      "vote_count": 5
    },
    {
      "option_id": "uuid",
      "option_content": "선택지 2",
      "vote_count": 3
    }
  ],
  "first_priority_criteria": [
    {
      "criterion_id": "uuid",
      "criterion_content": "기준 1",
      "count": 6
    },
    {
      "criterion_id": "uuid",
      "criterion_content": "기준 2",
      "count": 2
    }
  ],
  "weighted_criteria": [
    {
      "criterion_id": "uuid",
      "criterion_content": "기준 1",
      "count": 15
    },
    {
      "criterion_id": "uuid",
      "criterion_content": "기준 2",
      "count": 8
    }
  ]
}
```

**에러:**
- `400 Bad Request`: 이벤트가 FINISHED 상태가 아님
- `403 Forbidden`: ACCEPTED 멤버십이 아님

**참고:**
- FINISHED 상태에서만 조회 가능
- `total_participants_count`: 전체 참가 인원 (ACCEPTED 멤버십 기준)
- `voted_participants_count`: 투표 참여 인원 (최종 투표 완료한 사용자 수)
- `first_priority_criteria`: 1순위로 가장 많이 선택된 기준 (내림차순)
- `weighted_criteria`: 우선순위별 가중치 점수 (1위=3점, 2위=2점, 3위=1점, 내림차순)

---

### PATCH /v1/events/{event_id}/status

이벤트 상태 변경 (관리자용)

**인증:** Bearer Token 필수 (관리자 권한 필요)

**Path Parameters:**
- `event_id` (UUID): 이벤트 ID

**Request Body:**
```json
{
  "status": "IN_PROGRESS"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "IN_PROGRESS",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**상태 전이 규칙:**
- `NOT_STARTED` → `IN_PROGRESS` (시작)
- `IN_PROGRESS` → `PAUSED` (일시정지)
- `IN_PROGRESS` → `FINISHED` (종료)
- `PAUSED` → `IN_PROGRESS` (재개)
- `PAUSED` → `FINISHED` (종료)
- `FINISHED` → 변경 불가

**에러:**
- `400 Bad Request`: 잘못된 상태 전이
- `403 Forbidden`: 관리자 권한 없음

**참고:**
- 이 엔드포인트는 Idempotency-Key를 사용하지 않습니다.

---

## 개발용 API (`/dev`)

개발 및 테스트를 위한 CRUD API입니다. 자세한 내용은 [`dev_api_spec.md`](./dev_api_spec.md)를 참고하세요.

주요 엔드포인트:
- `/dev/events` - 이벤트 CRUD
- `/dev/assumptions` - 전제 CRUD
- `/dev/criteria` - 기준 CRUD
- `/dev/options` - 선택지 CRUD
- `/dev/memberships` - 멤버십 CRUD

---

## 기타

### GET /

루트 엔드포인트

**Response:** `200 OK`
```json
{
  "message": "Hello World"
}
```

---

### GET /health

헬스 체크

**Response:** `200 OK`
```json
{
  "status": "ok"
}
```

---

---

## 데이터 타입

### EventStatusType
- `NOT_STARTED`: 시작 전
- `IN_PROGRESS`: 진행 중
- `PAUSED`: 일시 중지
- `FINISHED`: 종료

### MembershipStatusType
- `PENDING`: 승인 대기
- `ACCEPTED`: 승인됨
- `REJECTED`: 거부됨

### ProposalStatusType
- `PENDING`: 대기 중
- `ACCEPTED`: 승인됨
- `REJECTED`: 거부됨
- `DELETED`: 삭제됨

### ProposalCategoryType
- `CREATION`: 생성
- `MODIFICATION`: 수정
- `DELETION`: 삭제
