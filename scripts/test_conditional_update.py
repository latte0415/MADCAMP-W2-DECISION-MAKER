#!/usr/bin/env python3
"""
조건부 UPDATE 동시성 테스트 스크립트

테스트 시나리오:
1. 동시에 같은 proposal/membership에 승인/거절 요청
2. 하나만 성공하고 나머지는 ConflictError 반환 확인
3. 상태가 한 번만 변경되었는지 확인

사용법:
    python scripts/test_conditional_update.py

주의: 
    - 실제 DB에 연결되어 있어야 함
    - 테스트용 이벤트와 proposal/membership이 필요
"""
import asyncio
import aiohttp
import json
from typing import List, Tuple
from uuid import UUID


async def test_concurrent_proposal_approval(
    base_url: str,
    event_id: str,
    proposal_id: str,
    admin_token: str,
    num_requests: int = 5
) -> Tuple[int, int]:
    """
    동시에 같은 proposal에 승인 요청을 여러 번 보냄
    
    Returns:
        (성공 횟수, 실패 횟수)
    """
    url = f"{base_url}/v1/events/{event_id}/assumption-proposals/{proposal_id}/status"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    payload = {"status": "ACCEPTED"}
    
    async def send_request(session: aiohttp.ClientSession, request_id: int):
        try:
            async with session.patch(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return ("success", await response.json())
                elif response.status == 409:
                    return ("conflict", await response.json())
                else:
                    return ("error", {"status": response.status, "text": await response.text()})
        except Exception as e:
            return ("error", {"error": str(e)})
    
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r[0] == "success")
    conflict_count = sum(1 for r in results if r[0] == "conflict")
    error_count = sum(1 for r in results if r[0] == "error")
    
    # 성공한 응답에서 proposal_status 확인
    approved_status = None
    for status, data in results:
        if status == "success" and isinstance(data, dict):
            approved_status = data.get("proposal_status")
            break
    
    print(f"\n[Proposal 승인 동시성 테스트]")
    print(f"  총 요청: {num_requests}")
    print(f"  성공: {success_count} (예상: 1)")
    print(f"  Conflict: {conflict_count} (예상: {num_requests - 1})")
    print(f"  에러: {error_count} (예상: 0)")
    
    if approved_status:
        print(f"  승인된 상태: {approved_status}")
    
    if success_count == 1 and conflict_count == num_requests - 1:
        print("  ✅ 테스트 통과: 조건부 UPDATE가 정상 작동")
        if approved_status == "ACCEPTED":
            print("  ✅ Proposal 상태가 올바르게 ACCEPTED로 변경됨")
    else:
        print("  ❌ 테스트 실패: 조건부 UPDATE가 제대로 작동하지 않음")
        for i, (status, data) in enumerate(results):
            print(f"    요청 {i+1}: {status} - {data}")
    
    return success_count, conflict_count


async def test_concurrent_membership_approval(
    base_url: str,
    event_id: str,
    membership_id: str,
    admin_token: str,
    num_requests: int = 5
) -> Tuple[int, int]:
    """
    동시에 같은 membership에 승인 요청을 여러 번 보냄
    """
    url = f"{base_url}/v1/events/{event_id}/memberships/{membership_id}/approve"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async def send_request(session: aiohttp.ClientSession, request_id: int):
        try:
            async with session.patch(url, headers=headers) as response:
                if response.status == 200:
                    return ("success", await response.json())
                elif response.status == 409:
                    return ("conflict", await response.json())
                else:
                    return ("error", {"status": response.status, "text": await response.text()})
        except Exception as e:
            return ("error", {"error": str(e)})
    
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r[0] == "success")
    conflict_count = sum(1 for r in results if r[0] == "conflict")
    error_count = sum(1 for r in results if r[0] == "error")
    
    print(f"\n[Membership 승인 동시성 테스트]")
    print(f"  총 요청: {num_requests}")
    print(f"  성공: {success_count} (예상: 1)")
    print(f"  Conflict: {conflict_count} (예상: {num_requests - 1})")
    print(f"  에러: {error_count} (예상: 0)")
    
    if success_count == 1 and conflict_count == num_requests - 1:
        print("  ✅ 테스트 통과: 조건부 UPDATE가 정상 작동")
    else:
        print("  ❌ 테스트 실패: 조건부 UPDATE가 제대로 작동하지 않음")
        for i, (status, data) in enumerate(results):
            print(f"    요청 {i+1}: {status} - {data}")
    
    return success_count, conflict_count


async def test_proposal_status_after_approval(
    base_url: str,
    event_id: str,
    proposal_id: str,
    admin_token: str
) -> bool:
    """
    승인 후 proposal 상태를 확인하여 한 번만 변경되었는지 검증
    EventDetailResponse에서 proposal을 찾아 상태 확인
    """
    url = f"{base_url}/v1/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                proposal_id_uuid = proposal_id
                
                # assumptions에서 proposal 찾기
                status = None
                for assumption in data.get("assumptions", []):
                    for proposal in assumption.get("proposals", []):
                        if proposal.get("id") == proposal_id_uuid:
                            status = proposal.get("proposal_status")
                            break
                    if status:
                        break
                
                # assumption_creation_proposals에서도 찾기
                if not status:
                    for proposal in data.get("assumption_creation_proposals", []):
                        if proposal.get("id") == proposal_id_uuid:
                            status = proposal.get("proposal_status")
                            break
                
                # criteria_proposals에서도 찾기
                if not status:
                    for criterion in data.get("criteria", []):
                        for proposal in criterion.get("proposals", []):
                            if proposal.get("id") == proposal_id_uuid:
                                status = proposal.get("proposal_status")
                                break
                        if status:
                            break
                        for proposal in criterion.get("conclusion_proposals", []):
                            if proposal.get("id") == proposal_id_uuid:
                                status = proposal.get("proposal_status")
                                break
                        if status:
                            break
                
                # criteria_creation_proposals에서도 찾기
                if not status:
                    for proposal in data.get("criteria_creation_proposals", []):
                        if proposal.get("id") == proposal_id_uuid:
                            status = proposal.get("proposal_status")
                            break
                
                if status == "ACCEPTED":
                    print(f"\n[Proposal 상태 확인]")
                    print(f"  Proposal ID: {proposal_id}")
                    print(f"  현재 상태: {status}")
                    print(f"  ✅ 상태가 올바르게 변경됨")
                    return True
                elif status:
                    print(f"\n[Proposal 상태 확인]")
                    print(f"  Proposal ID: {proposal_id}")
                    print(f"  현재 상태: {status}")
                    print(f"  ❌ 예상: ACCEPTED, 실제: {status}")
                    return False
                else:
                    print(f"\n[Proposal 상태 확인]")
                    print(f"  Proposal ID: {proposal_id}")
                    print(f"  ❌ Proposal을 찾을 수 없음")
                    return False
            else:
                print(f"\n[Proposal 상태 확인]")
                print(f"  ❌ 상태 조회 실패: {response.status}")
                text = await response.text()
                print(f"  응답: {text}")
                return False


async def main():
    """
    메인 테스트 함수
    
    환경 변수 설정:
        BASE_URL: API 기본 URL (예: http://localhost:8000)
        EVENT_ID: 테스트할 이벤트 ID
        PROPOSAL_ID: 테스트할 제안 ID (PENDING 상태여야 함)
        MEMBERSHIP_ID: 테스트할 멤버십 ID (PENDING 상태여야 함)
        ADMIN_TOKEN: 관리자 인증 토큰
    """
    import os
    
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    event_id = os.getenv("EVENT_ID")
    proposal_id = os.getenv("PROPOSAL_ID")
    membership_id = os.getenv("MEMBERSHIP_ID")
    admin_token = os.getenv("ADMIN_TOKEN")
    
    if not all([event_id, admin_token]):
        print("필수 환경 변수가 설정되지 않았습니다:")
        print("  EVENT_ID: 테스트할 이벤트 ID")
        print("  ADMIN_TOKEN: 관리자 인증 토큰")
        print("\n선택적 환경 변수:")
        print("  PROPOSAL_ID: 제안 승인 테스트용 (PENDING 상태)")
        print("  MEMBERSHIP_ID: 멤버십 승인 테스트용 (PENDING 상태)")
        print("  BASE_URL: API 기본 URL (기본값: http://localhost:8000)")
        return
    
    print("=" * 60)
    print("조건부 UPDATE 동시성 테스트")
    print("=" * 60)
    
    # Proposal 승인 테스트
    if proposal_id:
        # 동시 요청 테스트 (테스트 내에서 상태 확인 포함)
        await test_concurrent_proposal_approval(
            base_url, event_id, proposal_id, admin_token, num_requests=5
        )
        
        # 추가로 EventDetailResponse에서 상태 확인
        await test_proposal_status_after_approval(
            base_url, event_id, proposal_id, admin_token
        )
    else:
        print("\n[Proposal 승인 테스트] 건너뜀 (PROPOSAL_ID 미설정)")
    
    # Membership 승인 테스트
    if membership_id:
        await test_concurrent_membership_approval(
            base_url, event_id, membership_id, admin_token, num_requests=5
        )
    else:
        print("\n[Membership 승인 테스트] 건너뜀 (MEMBERSHIP_ID 미설정)")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
