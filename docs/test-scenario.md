# 테스트 시나리오 문서

이 문서는 API 스펙(`docs/api_spec/api_spec.md`)과 UI 스펙(`docs/ui_specification.md`)을 기반으로 작성된 모든 테스트 시나리오를 정리합니다.

## 목차

- [인증 API](#인증-api)
- [이벤트 생성 API](#이벤트-생성-api)
- [홈/참가 API](#홈참가-api)
- [이벤트 상세/제안 API](#이벤트-상세제안-api)
- [제안 상태 변경 API](#제안-상태-변경-api)
- [코멘트 API](#코멘트-api)
- [투표 API](#투표-api)
- [이벤트 설정 API](#이벤트-설정-api)
- [멤버십 관리 API](#멤버십-관리-api)

---

## 인증 API

### POST /auth/signup

**성공 케이스**
- [x] 정상적인 이메일과 비밀번호로 회원가입

**에러 케이스**
- [ ] 409 Conflict: 이미 사용 중인 이메일로 회원가입 시도
- [ ] 400 Bad Request: 잘못된 이메일 형식 (예: "invalid-email")
- [ ] 400 Bad Request: 비밀번호 길이 오류 (8자 미만 또는 20자 초과)
- [ ] 400 Bad Request: 필수 필드 누락 (email 또는 password 없음)

### POST /auth/login

**성공 케이스**
- [x] 정상적인 이메일과 비밀번호로 로그인

**에러 케이스**
- [ ] 401 Unauthorized: 잘못된 비밀번호
- [ ] 401 Unauthorized: 존재하지 않는 사용자
- [ ] 403 Forbidden: 비활성화된 사용자
- [ ] 403 Forbidden: 구글 계정과 연결된 이메일 (구글로 로그인 필요)
- [ ] 400 Bad Request: 필수 필드 누락

### POST /auth/google

**성공 케이스**
- [ ] 정상적인 구글 토큰으로 로그인 (스킵 가능)

**에러 케이스**
- [ ] 401 Unauthorized: 유효하지 않은 구글 토큰
- [ ] 403 Forbidden: 비활성화된 사용자
- [ ] 400 Bad Request: 필수 필드 누락

### POST /auth/refresh

**성공 케이스**
- [ ] 정상적인 refresh token으로 토큰 갱신 (쿠키 필요, 스킵 가능)

**에러 케이스**
- [ ] 401 Unauthorized: refresh token이 없음
- [ ] 401 Unauthorized: 유효하지 않은 refresh token

### POST /auth/logout

**성공 케이스**
- [ ] 정상적인 로그아웃 (쿠키 필요, 스킵 가능)

**에러 케이스**
- [ ] 401 Unauthorized: refresh token이 없음

### GET /auth/me

**성공 케이스**
- [x] 정상적인 토큰으로 사용자 정보 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 401 Unauthorized: 유효하지 않은 토큰
- [ ] 404 Not Found: 사용자를 찾을 수 없음

### PATCH /auth/me/name

**성공 케이스**
- [x] 정상적인 이름으로 업데이트

**에러 케이스**
- [ ] 400 Bad Request: 이름 길이 오류 (1자 미만 또는 100자 초과)
- [ ] 400 Bad Request: 필수 필드 누락
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 사용자를 찾을 수 없음

### POST /auth/password-reset/request

**성공 케이스**
- [x] 정상적인 이메일로 비밀번호 재설정 요청

**에러 케이스**
- [ ] 404 Not Found: 존재하지 않는 사용자
- [ ] 403 Forbidden: 비활성화된 사용자
- [ ] 502 Bad Gateway: 이메일 전송 실패
- [ ] 400 Bad Request: 필수 필드 누락

### POST /auth/password-reset/confirm

**성공 케이스**
- [ ] 정상적인 토큰과 새 비밀번호로 재설정 (토큰 필요, 스킵 가능)

**에러 케이스**
- [ ] 401 Unauthorized: 유효하지 않은 리셋 토큰
- [ ] 403 Forbidden: 비활성화된 사용자
- [ ] 400 Bad Request: 비밀번호 길이 오류 (8자 미만 또는 20자 초과)
- [ ] 400 Bad Request: 필수 필드 누락

---

## 이벤트 생성 API

### POST /v1/events

**성공 케이스**
- [x] 정상적인 데이터로 이벤트 생성

**에러 케이스**
- [ ] 401 Unauthorized: 인증 토큰 없음
- [ ] 409 Conflict: 중복된 입장 코드 사용
- [ ] 400 Bad Request: 잘못된 입장 코드 형식 (6자리 대문자/숫자가 아님)
- [ ] 400 Bad Request: max_membership이 1 미만
- [ ] 400 Bad Request: conclusion_approval_threshold_percent가 1-100 범위 밖
- [ ] 400 Bad Request: 필수 필드 누락

### POST /v1/events/entrance-code/check

**성공 케이스**
- [x] 사용 가능한 입장 코드 확인
- [x] 이미 사용 중인 입장 코드 확인

**에러 케이스**
- [ ] 400 Bad Request: 잘못된 입장 코드 형식
- [ ] 400 Bad Request: 필수 필드 누락

### GET /v1/events/entrance-code/generate

**성공 케이스**
- [x] 랜덤 입장 코드 생성

**에러 케이스**
- 없음 (인증 불필요, 항상 성공)

---

## 홈/참가 API

### GET /v1/events/participated

**성공 케이스**
- [x] 정상적인 토큰으로 참가한 이벤트 목록 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 401 Unauthorized: 유효하지 않은 토큰

### POST /v1/events/entry

**성공 케이스**
- [x] 정상적인 입장 코드로 이벤트 입장
- [x] 이미 참가 중인 경우 (409는 정상 동작)

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 입장 코드
- [ ] 409 Conflict: 이미 참가 중이거나 참가 신청 중
- [ ] 400 Bad Request: 필수 필드 누락

### GET /v1/events/{event_id}/overview

**성공 케이스**
- [ ] 정상적인 이벤트 ID로 오버뷰 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 이벤트 ID

---

## 이벤트 상세/제안 API

### GET /v1/events/{event_id}

**성공 케이스**
- [x] ACCEPTED 멤버십으로 이벤트 상세 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING, REJECTED, 없음)
- [ ] 404 Not Found: 존재하지 않는 이벤트 ID

### POST /v1/events/{event_id}/assumption-proposals

**성공 케이스**
- [x] IN_PROGRESS 상태에서 전제 제안 생성

**에러 케이스**
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (NOT_STARTED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (PAUSED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (FINISHED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 409 Conflict: 중복 제안 존재
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 필수 필드 누락

### POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes

**성공 케이스**
- [x] PENDING 상태의 제안에 투표 생성

**에러 케이스**
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님 (ACCEPTED)
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님 (REJECTED)
- [ ] 409 Conflict: 이미 투표함
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

### DELETE /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes

**성공 케이스**
- [x] 정상적인 투표 삭제

**에러 케이스**
- [ ] 404 Not Found: 투표를 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

### POST /v1/events/{event_id}/criteria-proposals

**성공 케이스**
- [x] IN_PROGRESS 상태에서 기준 제안 생성

**에러 케이스**
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (NOT_STARTED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (PAUSED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (FINISHED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 409 Conflict: 중복 제안 존재
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 존재하지 않는 criteria_id (MODIFICATION/DELETION의 경우)
- [ ] 400 Bad Request: 필수 필드 누락

### POST /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes

**성공 케이스**
- [x] PENDING 상태의 제안에 투표 생성

**에러 케이스**
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님
- [ ] 409 Conflict: 이미 투표함
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

### DELETE /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes

**성공 케이스**
- [x] 정상적인 투표 삭제

**에러 케이스**
- [ ] 404 Not Found: 투표를 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

### POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals

**성공 케이스**
- [x] IN_PROGRESS 상태에서 결론 제안 생성

**에러 케이스**
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (NOT_STARTED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (PAUSED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (FINISHED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 존재하지 않는 criterion_id
- [ ] 400 Bad Request: 필수 필드 누락

### POST /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes

**성공 케이스**
- [x] PENDING 상태의 제안에 투표 생성

**에러 케이스**
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님
- [ ] 409 Conflict: 이미 투표함
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

### DELETE /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes

**성공 케이스**
- [x] 정상적인 투표 삭제

**에러 케이스**
- [ ] 404 Not Found: 투표를 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 proposal_id
- [ ] 404 Not Found: 존재하지 않는 event_id

---

## 제안 상태 변경 API

### PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status

**성공 케이스**
- [x] 관리자가 PENDING 제안을 ACCEPTED로 변경
- [x] 관리자가 PENDING 제안을 REJECTED로 변경

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님 (ACCEPTED)
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님 (REJECTED)
- [ ] 404 Not Found: 제안을 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 잘못된 status 값 (ACCEPTED, REJECTED 외)

### PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status

**성공 케이스**
- [x] 관리자가 PENDING 제안을 ACCEPTED로 변경
- [x] 관리자가 PENDING 제안을 REJECTED로 변경

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님
- [ ] 404 Not Found: 제안을 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 잘못된 status 값

### PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status

**성공 케이스**
- [x] 관리자가 PENDING 제안을 ACCEPTED로 변경
- [x] 관리자가 PENDING 제안을 REJECTED로 변경

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 제안이 PENDING 상태가 아님
- [ ] 404 Not Found: 제안을 찾을 수 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 잘못된 status 값

---

## 코멘트 API

### GET /v1/events/{event_id}/criteria/{criterion_id}/comments/count

**성공 케이스**
- [x] ACCEPTED 멤버십으로 코멘트 수 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 존재하지 않는 criterion_id

### GET /v1/events/{event_id}/criteria/{criterion_id}/comments

**성공 케이스**
- [x] ACCEPTED 멤버십으로 코멘트 목록 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 존재하지 않는 criterion_id

### POST /v1/events/{event_id}/criteria/{criterion_id}/comments

**성공 케이스**
- [x] ACCEPTED 멤버십으로 코멘트 생성

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 존재하지 않는 criterion_id
- [ ] 400 Bad Request: 필수 필드 누락

### PATCH /v1/events/{event_id}/comments/{comment_id}

**성공 케이스**
- [x] 본인이 작성한 코멘트 수정

**에러 케이스**
- [ ] 403 Forbidden: 본인이 작성한 코멘트가 아님
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님
- [ ] 404 Not Found: 존재하지 않는 comment_id
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 필수 필드 누락

### DELETE /v1/events/{event_id}/comments/{comment_id}

**성공 케이스**
- [x] 본인이 작성한 코멘트 삭제

**에러 케이스**
- [ ] 403 Forbidden: 본인이 작성한 코멘트가 아님
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님
- [ ] 404 Not Found: 존재하지 않는 comment_id
- [ ] 404 Not Found: 존재하지 않는 event_id

---

## 투표 API

### GET /v1/events/{event_id}/votes/me

**성공 케이스**
- [x] ACCEPTED 멤버십으로 본인 투표 내역 조회

**에러 케이스**
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 404 Not Found: 존재하지 않는 event_id

### POST /v1/events/{event_id}/votes

**성공 케이스**
- [x] IN_PROGRESS 상태에서 투표 생성/업데이트

**에러 케이스**
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (NOT_STARTED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (PAUSED)
- [ ] 400 Bad Request: 이벤트가 IN_PROGRESS 상태가 아님 (FINISHED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 404 Not Found: 존재하지 않는 option_id
- [ ] 404 Not Found: 존재하지 않는 criterion_id (리스트 내)
- [ ] 400 Bad Request: 모든 활성화된 기준이 포함되지 않음
- [ ] 400 Bad Request: criterion_ids에 중복이 있음
- [ ] 400 Bad Request: criterion_ids가 빈 리스트
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 필수 필드 누락

### GET /v1/events/{event_id}/votes/result

**성공 케이스**
- [x] FINISHED 상태에서 투표 결과 조회

**에러 케이스**
- [ ] 400 Bad Request: 이벤트가 FINISHED 상태가 아님 (NOT_STARTED)
- [ ] 400 Bad Request: 이벤트가 FINISHED 상태가 아님 (IN_PROGRESS)
- [ ] 400 Bad Request: 이벤트가 FINISHED 상태가 아님 (PAUSED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (PENDING)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (REJECTED)
- [ ] 403 Forbidden: ACCEPTED 멤버십이 아님 (없음)
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

---

## 이벤트 설정 API

### GET /v1/events/{event_id}/setting

**성공 케이스**
- [x] 관리자로 이벤트 설정 조회

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

### PATCH /v1/events/{event_id}

**성공 케이스**
- [x] NOT_STARTED 상태에서 기본 정보 수정
- [x] FINISHED가 아닐 때 최대 인원 수정
- [x] FINISHED가 아닐 때 투표 허용 정책 수정

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: NOT_STARTED가 아닌데 기본 정보 수정 시도 (decision_subject, options, assumptions, criteria)
- [ ] 400 Bad Request: FINISHED 상태에서 수정 시도
- [ ] 400 Bad Request: max_membership이 현재 ACCEPTED 멤버 수보다 작음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 404 Not Found: 수정하려는 option/assumption/criterion ID가 존재하지 않음

### PATCH /v1/events/{event_id}/status

**성공 케이스**
- [x] NOT_STARTED → IN_PROGRESS
- [x] IN_PROGRESS → PAUSED
- [x] IN_PROGRESS → FINISHED
- [x] PAUSED → IN_PROGRESS
- [x] PAUSED → FINISHED

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 잘못된 상태 전이 (NOT_STARTED → PAUSED)
- [ ] 400 Bad Request: 잘못된 상태 전이 (NOT_STARTED → FINISHED)
- [ ] 400 Bad Request: 잘못된 상태 전이 (IN_PROGRESS → NOT_STARTED)
- [ ] 400 Bad Request: 잘못된 상태 전이 (PAUSED → NOT_STARTED)
- [ ] 400 Bad Request: 잘못된 상태 전이 (FINISHED → 다른 상태)
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id
- [ ] 400 Bad Request: 필수 필드 누락

---

## 멤버십 관리 API

### GET /v1/events/{event_id}/memberships

**성공 케이스**
- [x] 관리자로 멤버십 목록 조회

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

### PATCH /v1/events/{event_id}/memberships/{membership_id}/approve

**성공 케이스**
- [x] 관리자가 PENDING 멤버십 승인

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 멤버십이 PENDING 상태가 아님 (ACCEPTED)
- [ ] 400 Bad Request: 멤버십이 PENDING 상태가 아님 (REJECTED)
- [ ] 400 Bad Request: 최대 인원 초과
- [ ] 404 Not Found: 존재하지 않는 membership_id
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

### PATCH /v1/events/{event_id}/memberships/{membership_id}/reject

**성공 케이스**
- [x] 관리자가 PENDING 멤버십 거부

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 400 Bad Request: 멤버십이 PENDING 상태가 아님 (ACCEPTED)
- [ ] 400 Bad Request: 멤버십이 PENDING 상태가 아님 (REJECTED)
- [ ] 404 Not Found: 존재하지 않는 membership_id
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

### POST /v1/events/{event_id}/memberships/bulk-approve

**성공 케이스**
- [x] 관리자가 모든 PENDING 멤버십 일괄 승인

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

### POST /v1/events/{event_id}/memberships/bulk-reject

**성공 케이스**
- [x] 관리자가 모든 PENDING 멤버십 일괄 거부

**에러 케이스**
- [ ] 403 Forbidden: 관리자 권한 없음
- [ ] 401 Unauthorized: 토큰 없음
- [ ] 404 Not Found: 존재하지 않는 event_id

---

## 범례

- [x] 테스트 완료
- [ ] 테스트 미완료

## 에러 코드 분류

- **400 Bad Request**: Validation 오류, 상태 전이 오류, 잘못된 요청
- **401 Unauthorized**: 인증 필요
- **403 Forbidden**: 권한 없음, 멤버십 상태 오류
- **404 Not Found**: 리소스 없음
- **409 Conflict**: 중복, 리소스 충돌
- **502 Bad Gateway**: 이메일 전송 실패 등 외부 서비스 오류
