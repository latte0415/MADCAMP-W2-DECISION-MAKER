# Docker 환경에서 조건부 UPDATE 테스트

## Docker 환경 확인

프로젝트는 Docker Compose를 사용하므로 다음 중 하나로 접근 가능합니다:

### 옵션 1: Caddy 프록시를 통해 (포트 80)
```bash
export BASE_URL="http://localhost"
# 또는
export BASE_URL="http://localhost:80"
```

### 옵션 2: API 컨테이너에 직접 접근
```bash
# API 컨테이너의 포트 확인 필요
export BASE_URL="http://localhost:8000"
# 또는 Docker 내부 네트워크에서
export BASE_URL="http://api:8000"
```

## API 경로 확인

**중요:** 모든 event 라우터는 `/v1` prefix가 있습니다.

- ❌ 잘못된 경로: `/events/{event_id}/...`
- ✅ 올바른 경로: `/v1/events/{event_id}/...`

## 테스트 실행

### 1. Docker 컨테이너 상태 확인

```bash
# 컨테이너 실행 중인지 확인
docker-compose ps

# API 컨테이너가 정상 작동하는지 확인
curl http://localhost/health
# 또는
curl http://localhost/v1/health
```

### 2. 환경 변수 설정

```bash
# Caddy를 통해 접근 (포트 80)
export BASE_URL="http://localhost"
# 또는 API 직접 접근
export BASE_URL="http://localhost:8000"

export EVENT_ID="<your-event-id>"
export PROPOSAL_ID="<pending-proposal-id>"
export MEMBERSHIP_ID="<pending-membership-id>"
export ADMIN_TOKEN="<admin-token>"
```

### 3. 간단한 연결 테스트

```bash
# API 연결 테스트
curl "${BASE_URL}/health"
# 또는
curl "${BASE_URL}/v1/health"

# 이벤트 조회 테스트
curl -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     "${BASE_URL}/v1/events/${EVENT_ID}"

# Proposal 조회 테스트
curl -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     "${BASE_URL}/v1/events/${EVENT_ID}"
```

### 4. 동시성 테스트 실행

```bash
# Python 스크립트 사용
python scripts/test_conditional_update.py

# 또는 Bash 스크립트 사용
./scripts/test_conditional_update_simple.sh
```

## Docker 컨테이너 내부에서 테스트

만약 호스트에서 접근이 안 되면, 컨테이너 내부에서 실행:

```bash
# API 컨테이너 내부로 들어가기
docker-compose exec api bash

# 컨테이너 내부에서
export BASE_URL="http://localhost:8000"
export EVENT_ID="<event-id>"
# ... 나머지 환경 변수
python scripts/test_conditional_update.py
```

## 트러블슈팅

### 404 에러가 계속 발생하는 경우

1. **API 경로 확인:**
   ```bash
   # 올바른 경로인지 확인 (반드시 /v1 prefix 필요)
   curl "${BASE_URL}/v1/events/${EVENT_ID}"
   ```

2. **컨테이너 로그 확인:**
   ```bash
   # API 컨테이너 로그 확인
   docker-compose logs api
   
   # 특정 엔드포인트 접근 시 로그 확인
   docker-compose logs -f api
   ```

3. **네트워크 확인:**
   ```bash
   # 컨테이너 간 네트워크 확인
   docker network ls
   docker network inspect <network-name>
   ```

### Connection refused 에러

- 컨테이너가 실행 중인지 확인
- 포트가 올바른지 확인 (80 또는 8000)
- 방화벽 설정 확인

### 인증 에러 (401)

- 토큰이 유효한지 확인
- 토큰 만료 시간 확인
- Authorization 헤더 형식 확인: `Bearer <token>`
