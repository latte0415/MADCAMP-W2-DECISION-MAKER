# Idempotency 테스트 가이드

## 개요

`test_idempotency.py` 스크립트는 Idempotency 기능이 올바르게 동작하는지 테스트합니다.

## 사용법

```bash
python scripts/test_idempotency.py <base_url> <admin_token> <user_token>
```

### 예시

```bash
python scripts/test_idempotency.py http://localhost:8000 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YTllYjg3Ny0zZWRhLTRmMzktYmUxZi0yNjgwNjU5NWE4NTUiLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzY4ODkxNjU4LCJleHAiOjE3Njg4OTI1NTgsImVtYWlsIjoidXNlcjFAdGVzdC5jb20ifQ.-fxOliHaXkQfREouX_Tq92SEgyy9nf5srf-uTtPji_M eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YjBiN2NjNy1lNDE3LTQyZjUtYmI0ZC1iMzVkYTkzY2Q0ZTIiLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzY4ODkxNjM5LCJleHAiOjE3Njg4OTI1MzksImVtYWlsIjoidXNlcjNAdGVzdC5jb20ifQ.gmq_8tGKMHzvIOMADo5sSB9jz1h_tT2amekMBjdU3nQ
```

## 테스트 시나리오

스크립트는 다음 5가지 테스트를 자동으로 수행합니다:

### 1. 투표 생성 2회 (같은 키)
- 같은 `Idempotency-Key`로 투표 생성 요청을 2회 수행
- **기대 결과**: DB에 투표가 1개만 생성되고, 두 응답이 동일해야 함

### 2. 제안 생성 2회 (같은 키)
- 같은 `Idempotency-Key`로 제안 생성 요청을 2회 수행
- **기대 결과**: DB에 제안이 1개만 생성되고, 두 응답의 `proposal_id`가 동일해야 함

### 3. 관리자 승인 2회 (같은 키)
- 같은 `Idempotency-Key`로 제안 승인 요청을 2회 수행
- **기대 결과**: 승인이 1회만 수행되고, 두 응답이 동일해야 함

### 4. 같은 키, 다른 body → 409
- 같은 `Idempotency-Key`로 다른 내용의 요청을 2회 수행
- **기대 결과**: 두 번째 요청에서 409 (Conflict) 에러가 발생해야 함

### 5. 멤버십 승인 2회 (같은 키)
- 같은 `Idempotency-Key`로 멤버십 승인 요청을 2회 수행
- **기대 결과**: 승인이 1회만 수행되고, 두 응답이 동일해야 함

## 사전 준비

1. **서버 실행**: 백엔드 서버가 실행 중이어야 합니다
2. **토큰 준비**: 
   - 관리자 토큰 (이벤트 생성, 승인 등에 사용)
   - 일반 사용자 토큰 (투표, 제안 생성에 사용)
3. **이벤트 데이터**: 스크립트가 자동으로 테스트용 이벤트를 생성합니다

## 주의사항

- 스크립트는 테스트용 이벤트를 자동으로 생성합니다
- 각 테스트는 독립적으로 실행되지만, 같은 이벤트를 재사용합니다
- 멤버십 승인 테스트는 PENDING 상태의 멤버십이 있어야 합니다 (없으면 스킵)

## 출력 예시

```
============================================================
Idempotency 테스트 시작
============================================================

============================================================
테스트: 같은 키로 투표 생성 2회
============================================================
첫 번째 요청 (키: a1b2c3d4...)
첫 번째 응답: option_id=xxx, created_at=2024-01-01T00:00:00
두 번째 요청 (같은 키: a1b2c3d4...)
두 번째 응답: option_id=xxx, created_at=2024-01-01T00:00:00
✓ 성공: 응답 동일: True, option_id 일치: True

...

============================================================
테스트 결과 요약
============================================================
✓ 통과: 투표 생성 2회 (같은 키)
✓ 통과: 제안 생성 2회 (같은 키)
✓ 통과: 관리자 승인 2회 (같은 키)
✓ 통과: 같은 키 다른 body → 409
✓ 통과: 멤버십 승인 2회 (같은 키)

총 5개 테스트 중 5개 통과 (100.0%)
```

## 문제 해결

### 토큰 만료
- 토큰이 만료되면 401 에러가 발생합니다
- 새로운 토큰을 발급받아 다시 실행하세요

### 이벤트 생성 실패
- 관리자 권한이 필요합니다
- 관리자 토큰이 올바른지 확인하세요

### 멤버십 승인 테스트 스킵
- PENDING 상태의 멤버십이 없으면 자동으로 스킵됩니다
- 이는 정상 동작입니다
