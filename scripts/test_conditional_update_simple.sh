#!/bin/bash
# 조건부 UPDATE 간단 테스트 스크립트

# 환경 변수 확인
if [ -z "$EVENT_ID" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "필수 환경 변수를 설정하세요:"
    echo "  export EVENT_ID=<event-id>"
    echo "  export ADMIN_TOKEN=<admin-token>"
    exit 1
fi

BASE_URL="${BASE_URL:-http://localhost:8000}"
PROPOSAL_ID="${PROPOSAL_ID}"
MEMBERSHIP_ID="${MEMBERSHIP_ID}"

echo "=========================================="
echo "조건부 UPDATE 동시성 테스트"
echo "=========================================="
echo "BASE_URL: $BASE_URL"
echo "EVENT_ID: $EVENT_ID"
echo "PROPOSAL_ID: $PROPOSAL_ID"
echo "MEMBERSHIP_ID: $MEMBERSHIP_ID"
echo ""

# Proposal 승인 테스트
if [ -n "$PROPOSAL_ID" ]; then
    echo "[Proposal 승인 동시성 테스트]"
    echo "동시에 5번 승인 요청 전송..."
    
    for i in {1..5}; do
        curl -s -X PATCH \
            "${BASE_URL}/v1/events/${EVENT_ID}/assumption-proposals/${PROPOSAL_ID}/status" \
            -H "Authorization: Bearer ${ADMIN_TOKEN}" \
            -H "Content-Type: application/json" \
            -d '{"status": "ACCEPTED"}' \
            -w "\n[요청 $i] HTTP %{http_code}\n" \
            -o /dev/null &
    done
    
    wait
    echo ""
else
    echo "[Proposal 승인 테스트] 건너뜀 (PROPOSAL_ID 미설정)"
fi

# Membership 승인 테스트
if [ -n "$MEMBERSHIP_ID" ]; then
    echo "[Membership 승인 동시성 테스트]"
    echo "동시에 5번 승인 요청 전송..."
    
    for i in {1..5}; do
        curl -s -X PATCH \
            "${BASE_URL}/v1/events/${EVENT_ID}/memberships/${MEMBERSHIP_ID}/approve" \
            -H "Authorization: Bearer ${ADMIN_TOKEN}" \
            -w "\n[요청 $i] HTTP %{http_code}\n" \
            -o /dev/null &
    done
    
    wait
    echo ""
else
    echo "[Membership 승인 테스트] 건너뜀 (MEMBERSHIP_ID 미설정)"
fi

echo "=========================================="
echo "테스트 완료"
echo "=========================================="
echo ""
echo "예상 결과:"
echo "  - 한 번만 200 OK (성공)"
echo "  - 나머지는 409 Conflict (이미 처리됨)"
