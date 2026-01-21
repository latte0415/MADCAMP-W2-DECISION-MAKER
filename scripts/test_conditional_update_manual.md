# 조건부 UPDATE 수동 테스트 가이드

## 1. 빠른 검증 방법 (cURL 사용)

### Proposal 승인 동시성 테스트

```bash
# 1. PENDING 상태인 proposal 생성 및 ID 확인
PROPOSAL_ID="<proposal-id>"
EVENT_ID="<event-id>"
ADMIN_TOKEN="<admin-token>"
BASE_URL="http://localhost:8000"

# 2. 동시에 여러 번 승인 요청
for i in {1..5}; do
  curl -X PATCH \
    "${BASE_URL}/v1/events/${EVENT_ID}/assumption-proposals/${PROPOSAL_ID}/status" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"status": "ACCEPTED"}' \
    -w "\n[요청 $i] HTTP Status: %{http_code}\n" \
    &
done
wait

# 3. 결과 확인
# 예상 결과:
# - 한 번만 200 OK (승인 성공)
# - 나머지는 409 Conflict (이미 처리됨)
```

### Membership 승인 동시성 테스트

```bash
MEMBERSHIP_ID="<membership-id>"

# 동시에 여러 번 승인 요청
for i in {1..5}; do
  curl -X PATCH \
    "${BASE_URL}/v1/events/${EVENT_ID}/memberships/${MEMBERSHIP_ID}/approve" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -w "\n[요청 $i] HTTP Status: %{http_code}\n" \
    &
done
wait
```

## 2. Python 스크립트 사용 (권장)

```bash
# 환경 변수 설정
export BASE_URL="http://localhost:8000"
export EVENT_ID="<event-id>"
export PROPOSAL_ID="<proposal-id>"  # PENDING 상태
export MEMBERSHIP_ID="<membership-id>"  # PENDING 상태
export ADMIN_TOKEN="<admin-token>"

# 스크립트 실행
python scripts/test_conditional_update.py
```

## 3. 테스트 시나리오

### 시나리오 1: Proposal 동시 승인

**준비:**
1. 이벤트 생성
2. PENDING 상태인 assumption proposal 생성
3. 관리자 토큰 준비

**실행:**
- 같은 proposal_id로 승인 요청을 동시에 5번 전송

**예상 결과:**
- ✅ 1개 요청: 200 OK (승인 성공)
- ✅ 4개 요청: 409 Conflict (이미 승인됨)
- ✅ DB 확인: proposal.proposal_status = 'ACCEPTED' (한 번만 변경)
- ✅ apply 로직 실행: 1번만 실행

**검증:**
```sql
-- Proposal 상태 확인
SELECT id, proposal_status, accepted_at 
FROM assumption_proposals 
WHERE id = '<proposal-id>';

-- 결과: proposal_status가 'ACCEPTED'이고 accepted_at이 설정됨
```

### 시나리오 2: Membership 동시 승인

**준비:**
1. 이벤트 생성
2. PENDING 상태인 membership 생성
3. 관리자 토큰 준비

**실행:**
- 같은 membership_id로 승인 요청을 동시에 5번 전송

**예상 결과:**
- ✅ 1개 요청: 200 OK (승인 성공)
- ✅ 4개 요청: 409 Conflict (이미 승인됨)

**검증:**
```sql
-- Membership 상태 확인
SELECT id, membership_status, joined_at 
FROM event_memberships 
WHERE id = '<membership-id>';

-- 결과: membership_status가 'ACCEPTED'이고 joined_at이 설정됨
```

### 시나리오 3: 자동 승인 (동시 투표)

**준비:**
1. 이벤트 생성 (auto_approved=True, min_votes_required=3)
2. PENDING 상태인 proposal 생성
3. 투표 2개 추가 (현재 투표 수: 2)

**실행:**
- 동시에 2명이 투표 (임계값 3 도달)

**예상 결과:**
- ✅ 투표는 2개 모두 성공 (200 OK)
- ✅ 승인 상태 전이: 1번만 성공 (조건부 UPDATE)
- ✅ apply 로직: 1번만 실행

**검증:**
```sql
-- Proposal 상태 확인
SELECT id, proposal_status, accepted_at 
FROM assumption_proposals 
WHERE id = '<proposal-id>';

-- 투표 수 확인
SELECT COUNT(*) FROM assumption_proposal_votes 
WHERE assumption_proposal_id = '<proposal-id>';

-- 결과: proposal_status='ACCEPTED', votes=4개
```

## 4. DB 직접 확인

### Proposal 상태 확인

```sql
-- 모든 proposal 상태 확인
SELECT 
    id, 
    proposal_status, 
    accepted_at,
    created_at,
    updated_at
FROM assumption_proposals
WHERE event_id = '<event-id>'
ORDER BY created_at DESC;

-- 특정 proposal의 상태 전이 이력 확인
-- (타임스탬프로 중복 처리 확인)
SELECT 
    proposal_status,
    accepted_at,
    COUNT(*) as count
FROM assumption_proposals
WHERE id = '<proposal-id>'
GROUP BY proposal_status, accepted_at;
```

### Membership 상태 확인

```sql
-- 모든 membership 상태 확인
SELECT 
    id,
    user_id,
    membership_status,
    joined_at,
    created_at,
    updated_at
FROM event_memberships
WHERE event_id = '<event-id>'
ORDER BY created_at DESC;
```

## 5. 로그 확인 (개발 환경)

서버 로그에서 다음을 확인:

1. **트랜잭션 로그:**
   - 조건부 UPDATE 실행 여부
   - 반환값 (None vs Proposal/Membership)

2. **에러 로그:**
   - ConflictError 발생 횟수
   - 예상: 동시 요청 중 1개만 성공, 나머지는 ConflictError

3. **후속 처리 로그:**
   - apply 로직 실행 횟수 (1번만 실행되어야 함)

## 6. 예상 결과 요약

### 정상 작동 시:
- ✅ 동시 요청 5개 중 1개만 성공 (200 OK)
- ✅ 나머지 4개는 ConflictError (409 Conflict)
- ✅ DB 상태 변경: 1번만 수행
- ✅ 후속 처리 (apply 등): 1번만 실행

### 문제 발생 시:
- ❌ 여러 요청이 모두 성공 (200 OK)
- ❌ DB 상태가 여러 번 변경됨
- ❌ 후속 처리가 여러 번 실행됨

## 7. 트러블슈팅

### 모든 요청이 성공하는 경우:
- 조건부 UPDATE가 제대로 작동하지 않음
- Repository 메서드 확인 필요

### 모든 요청이 ConflictError인 경우:
- 이미 승인/거절된 상태
- PENDING 상태인 proposal/membership으로 다시 테스트

### 일부만 성공하는데 1개가 아닌 경우:
- 동시성 제어가 부분적으로만 작동
- 트랜잭션 격리 수준 확인 필요
