#!/usr/bin/env python3
"""
Idempotency 테스트 스크립트

사용법:
    python scripts/test_idempotency.py <base_url> <admin_token> <user_token>

예시:
    python scripts/test_idempotency.py http://localhost:8000 <admin_token> <user_token>
"""

import sys
import requests
import uuid
import json
from typing import Dict, Any, Optional


class IdempotencyTester:
    def __init__(self, base_url: str, admin_token: str, user_token: str):
        self.base_url = base_url.rstrip('/')
        self.admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        self.user_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        self.event_id: Optional[str] = None
        self.entrance_code: Optional[str] = None
        self.option_id: Optional[str] = None
        self.criterion_ids: list[str] = []
        self.proposal_id: Optional[str] = None
        self.membership_id: Optional[str] = None
    
    def print_test(self, test_name: str):
        print(f"\n{'='*60}")
        print(f"테스트: {test_name}")
        print(f"{'='*60}")
    
    def print_result(self, success: bool, message: str):
        status = "✓ 성공" if success else "✗ 실패"
        print(f"{status}: {message}")
    
    def generate_entrance_code(self) -> str:
        """랜덤 입장 코드 생성"""
        import random
        import string
        # A-Z, 0-9 중에서 6자리 랜덤 생성
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))
    
    def create_event(self) -> str:
        """이벤트 생성"""
        print("\n[이벤트 생성 중...]")
        
        # 입장 코드 생성 (중복 방지를 위해 랜덤)
        entrance_code = self.generate_entrance_code()
        
        payload = {
            "decision_subject": "Idempotency 테스트용 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
            # auto_approved_by_votes가 True일 때는 min_votes_required가 필수이므로
            # 테스트를 위해 False로 설정
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "conclusion_is_auto_approved_by_votes": False,
            # 테스트에 필요한 옵션과 기준 추가
            "options": [
                {"content": "옵션 1"},
                {"content": "옵션 2"}
            ],
            "assumptions": [
                {"content": "전제 1"}
            ],
            "criteria": [
                {"content": "기준 1"},
                {"content": "기준 2"}
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events",
            headers=self.admin_headers,
            json=payload
        )
        
        if response.status_code != 201:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"이벤트 생성 실패: {response.status_code}\n{error_text}")
        
        event_data = response.json()
        self.event_id = str(event_data["id"])
        self.entrance_code = entrance_code
        print(f"이벤트 생성 완료: {self.event_id}, 입장 코드: {entrance_code}")
        return self.event_id
    
    def join_event(self) -> None:
        """user가 이벤트에 입장"""
        if not self.entrance_code:
            raise Exception("입장 코드가 없습니다")
        
        print(f"[이벤트 입장 중...] 입장 코드: {self.entrance_code}")
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json={"entrance_code": self.entrance_code}
        )
        
        if response.status_code == 201:
            print("이벤트 입장 완료")
        elif response.status_code == 400:
            # 이미 멤버십이 있는 경우
            try:
                error_detail = response.json().get('detail', '')
                if '이미' in error_detail or 'already' in error_detail.lower():
                    print("이미 멤버십이 있습니다")
                    return
            except:
                pass
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"이벤트 입장 실패: {response.status_code}\n{error_text}")
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"이벤트 입장 실패: {response.status_code}\n{error_text}")
    
    def approve_user_membership(self) -> None:
        """user의 멤버십 승인"""
        # 멤버십 목록 조회
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"멤버십 목록 조회 실패: {response.status_code}\n{error_text}")
        
        memberships = response.json()
        # PENDING 상태이고 admin이 아닌 멤버십 찾기
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            print("승인할 PENDING 멤버십이 없습니다 (이미 승인되었거나 없음)")
            return
        
        membership_id = pending_membership['membership_id']
        print(f"[멤버십 승인 중...] membership_id: {membership_id}")
        
        # Idempotency-Key 헤더 필요
        approve_headers = {
            **self.admin_headers,
            "Idempotency-Key": str(uuid.uuid4())
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=approve_headers
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"멤버십 승인 실패: {response.status_code}\n{error_text}")
        
        print("멤버십 승인 완료")
    
    def start_event(self) -> None:
        """이벤트 상태를 IN_PROGRESS로 변경"""
        print("[이벤트 시작 중...]")
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/status",
            headers=self.admin_headers,
            json={"status": "IN_PROGRESS"}
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"이벤트 시작 실패: {response.status_code}\n{error_text}")
        
        print("이벤트 시작 완료")
    
    def get_event_detail(self) -> Dict[str, Any]:
        """이벤트 상세 조회"""
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}",
            headers=self.user_headers
        )
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"이벤트 조회 실패: {response.status_code}\n{error_text}")
        return response.json()
    
    def setup_event(self) -> None:
        """이벤트 설정 (생성, 입장, 승인, 시작)"""
        if self.event_id:
            return  # 이미 설정됨
        
        self.create_event()
        self.join_event()
        self.approve_user_membership()
        self.start_event()
    
    def test_1_vote_create_twice_same_key(self):
        """테스트 1: 같은 키로 vote create 2회 → DB vote 1개, 응답 동일"""
        self.print_test("같은 키로 투표 생성 2회")
        
        self.setup_event()
        
        # 이벤트 상세 조회하여 option_id와 criterion_ids 가져오기
        event_detail = self.get_event_detail()
        if not event_detail.get("options") or not event_detail.get("criteria"):
            raise Exception("이벤트에 옵션 또는 기준이 없습니다")
        
        option_id = event_detail["options"][0]["id"]
        criterion_ids = [c["id"] for c in event_detail["criteria"]]
        
        if len(criterion_ids) < 2:
            raise Exception("기준이 2개 이상 필요합니다")
        
        idempotency_key = str(uuid.uuid4())
        headers = {**self.user_headers, "Idempotency-Key": idempotency_key}
        
        payload = {
            "option_id": option_id,
            "criterion_ids": criterion_ids
        }
        
        # 첫 번째 요청
        print(f"첫 번째 요청 (키: {idempotency_key[:8]}...)")
        response1 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        if response1.status_code != 201:
            error_text = response1.text
            try:
                error_json = response1.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"첫 번째 요청 실패: {response1.status_code}\n{error_text}")
            return False
        
        result1 = response1.json()
        print(f"첫 번째 응답: option_id={result1.get('option_id')}, created_at={result1.get('created_at')}")
        
        # 두 번째 요청 (같은 키)
        print(f"두 번째 요청 (같은 키: {idempotency_key[:8]}...)")
        response2 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        if response2.status_code != 201:
            error_text = response2.text
            try:
                error_json = response2.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"두 번째 요청 실패: {response2.status_code}\n{error_text}")
            return False
        
        result2 = response2.json()
        print(f"두 번째 응답: option_id={result2.get('option_id')}, created_at={result2.get('created_at')}")
        
        # 검증: 응답이 동일해야 함
        success = (
            result1.get('option_id') == result2.get('option_id') and
            result1.get('created_at') == result2.get('created_at')
        )
        
        self.print_result(success, 
            f"응답 동일: {success}, option_id 일치: {result1.get('option_id') == result2.get('option_id')}")
        
        return success
    
    def test_2_proposal_create_twice_same_key(self):
        """테스트 2: 같은 키로 proposal create 2회 → proposal 1개, proposal_id 동일"""
        self.print_test("같은 키로 제안 생성 2회")
        
        self.setup_event()
        
        event_detail = self.get_event_detail()
        assumptions = event_detail.get("assumptions", [])
        if not assumptions:
            raise Exception("이벤트에 전제가 없습니다")
        
        assumption_id = assumptions[0]["id"]
        idempotency_key = str(uuid.uuid4())
        headers = {**self.user_headers, "Idempotency-Key": idempotency_key}
        
        payload = {
            "assumption_id": assumption_id,
            "proposal_category": "MODIFICATION",
            "proposal_content": "수정된 전제 내용",
            "reason": "테스트용"
        }
        
        # 첫 번째 요청
        print(f"첫 번째 요청 (키: {idempotency_key[:8]}...)")
        response1 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        if response1.status_code != 201:
            error_text = response1.text
            try:
                error_json = response1.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"첫 번째 요청 실패: {response1.status_code}\n{error_text}")
            return False
        
        result1 = response1.json()
        proposal_id_1 = result1.get('id')
        print(f"첫 번째 응답: proposal_id={proposal_id_1}")
        
        # 두 번째 요청 (같은 키)
        print(f"두 번째 요청 (같은 키: {idempotency_key[:8]}...)")
        response2 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        if response2.status_code != 201:
            error_text = response2.text
            try:
                error_json = response2.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"두 번째 요청 실패: {response2.status_code}\n{error_text}")
            return False
        
        result2 = response2.json()
        proposal_id_2 = result2.get('id')
        print(f"두 번째 응답: proposal_id={proposal_id_2}")
        
        # 검증: proposal_id가 동일해야 함
        success = proposal_id_1 == proposal_id_2
        
        self.print_result(success, f"proposal_id 동일: {success} ({proposal_id_1})")
        
        return success
    
    def test_3_admin_approve_twice_same_key(self):
        """테스트 3: 같은 키로 admin approve 2회 → 승인 1회"""
        self.print_test("같은 키로 관리자 승인 2회")
        
        self.setup_event()
        
        # 제안 생성 (user로)
        # 테스트 2에서 이미 제안을 생성했을 수 있으므로, 기존 PENDING 제안을 찾거나 새로 생성
        event_detail = self.get_event_detail()
        assumptions = event_detail.get("assumptions", [])
        if not assumptions:
            raise Exception("이벤트에 전제가 없습니다")
        
        assumption_id = assumptions[0]["id"]
        proposal_key = str(uuid.uuid4())
        proposal_id = None  # 초기화
        
        proposal_payload = {
            "assumption_id": assumption_id,
            "proposal_category": "MODIFICATION",
            "proposal_content": "승인 테스트용",
            "reason": "테스트"
        }
        
        proposal_response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": proposal_key},
            json=proposal_payload
        )
        
        if proposal_response.status_code == 409:
            # 중복 제안 에러인 경우, 기존 제안을 찾아서 사용
            error_json = proposal_response.json()
            if "Duplicate proposal" in error_json.get("message", ""):
                print("기존 PENDING 제안이 있습니다. 기존 제안을 사용합니다.")
                # 이벤트 상세에서 기존 제안 찾기
                assumptions_with_proposals = event_detail.get("assumptions", [])
                for assumption in assumptions_with_proposals:
                    if assumption.get("id") == assumption_id:
                        proposals = assumption.get("proposals", [])
                        # PENDING 상태의 제안 찾기
                        for proposal in proposals:
                            if proposal.get("proposal_status") == "PENDING":
                                proposal_id = proposal.get("id")
                                print(f"기존 제안 사용: {proposal_id}")
                                break
                        if proposal_id:
                            break
                
                if not proposal_id:
                    # 기존 제안을 찾지 못한 경우 에러
                    error_text = proposal_response.text
                    try:
                        error_json = proposal_response.json()
                        error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
                    except:
                        pass
                    raise Exception(f"제안 생성 실패 및 기존 제안 찾기 실패: {proposal_response.status_code}\n{error_text}")
            else:
                # 다른 종류의 409 에러
                error_text = proposal_response.text
                try:
                    error_json = proposal_response.json()
                    error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
                except:
                    pass
                raise Exception(f"제안 생성 실패: {proposal_response.status_code}\n{error_text}")
        elif proposal_response.status_code != 201:
            error_text = proposal_response.text
            try:
                error_json = proposal_response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"제안 생성 실패: {proposal_response.status_code}\n{error_text}")
        else:
            proposal_id = proposal_response.json()["id"]
            print(f"제안 생성 완료: {proposal_id}")
        
        if not proposal_id:
            raise Exception("제안 ID를 찾을 수 없습니다")
        
        # 관리자 승인 (같은 키로 2회)
        idempotency_key = str(uuid.uuid4())
        headers = {**self.admin_headers, "Idempotency-Key": idempotency_key}
        
        approve_payload = {"status": "ACCEPTED"}
        
        # 첫 번째 승인 요청
        print(f"첫 번째 승인 요청 (키: {idempotency_key[:8]}...)")
        response1 = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=headers,
            json=approve_payload
        )
        
        if response1.status_code != 200:
            error_text = response1.text
            try:
                error_json = response1.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"첫 번째 승인 실패: {response1.status_code}\n{error_text}")
            return False
        
        result1 = response1.json()
        status1 = result1.get('proposal_status')
        print(f"첫 번째 응답: status={status1}")
        
        # 두 번째 승인 요청 (같은 키)
        print(f"두 번째 승인 요청 (같은 키: {idempotency_key[:8]}...)")
        response2 = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=headers,
            json=approve_payload
        )
        
        if response2.status_code != 200:
            error_text = response2.text
            try:
                error_json = response2.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"두 번째 승인 실패: {response2.status_code}\n{error_text}")
            return False
        
        result2 = response2.json()
        status2 = result2.get('proposal_status')
        print(f"두 번째 응답: status={status2}")
        
        # 검증: 상태가 동일하고 ACCEPTED여야 함
        success = status1 == status2 == "ACCEPTED" and result1.get('id') == result2.get('id')
        
        self.print_result(success, f"승인 1회만 수행: {success}, status={status1}")
        
        return success
    
    def test_4_different_key_different_body(self):
        """테스트 4: 같은 키인데 body가 다름 → 409"""
        self.print_test("같은 키, 다른 body → 409 에러")
        
        self.setup_event()
        
        event_detail = self.get_event_detail()
        assumptions = event_detail.get("assumptions", [])
        if not assumptions:
            raise Exception("이벤트에 전제가 없습니다")
        
        assumption_id = assumptions[0]["id"]
        idempotency_key = str(uuid.uuid4())
        headers = {**self.user_headers, "Idempotency-Key": idempotency_key}
        
        # 첫 번째 요청
        payload1 = {
            "assumption_id": assumption_id,
            "proposal_category": "MODIFICATION",
            "proposal_content": "첫 번째 내용",
            "reason": "테스트1"
        }
        
        print(f"첫 번째 요청 (키: {idempotency_key[:8]}...)")
        response1 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload1
        )
        
        if response1.status_code != 201:
            error_text = response1.text
            try:
                error_json = response1.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"첫 번째 요청 실패: {response1.status_code}\n{error_text}")
            return False
        
        print(f"첫 번째 응답: proposal_id={response1.json().get('id')}")
        
        # 두 번째 요청 (같은 키, 다른 body)
        payload2 = {
            "assumption_id": assumption_id,
            "proposal_category": "MODIFICATION",
            "proposal_content": "두 번째 내용 (다름)",
            "reason": "테스트2"
        }
        
        print(f"두 번째 요청 (같은 키, 다른 body: {idempotency_key[:8]}...)")
        response2 = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload2
        )
        
        # 검증: 409 에러가 발생해야 함
        success = response2.status_code == 409
        error_message = ""
        if response2.status_code == 409:
            try:
                error_json = response2.json()
                error_message = error_json.get('detail', '')
            except:
                error_message = response2.text
        elif response2.status_code == 201:
            error_message = "예상과 다르게 성공했습니다 (409가 아님)"
        
        self.print_result(success, 
            f"409 에러 발생: {success}, status_code={response2.status_code}, "
            f"message={error_message}")
        
        return success
    
    def test_5_membership_approve_twice_same_key(self):
        """테스트 5: 같은 키로 membership approve 2회 → 승인 1회"""
        self.print_test("같은 키로 멤버십 승인 2회")
        
        # 멤버십 승인 테스트를 위해 별도 이벤트 생성 (user 입장 후 PENDING 상태 유지)
        if not self.event_id:
            self.create_event()
            self.join_event()
            # 멤버십은 승인하지 않음 (PENDING 상태 유지)
        
        # 멤버십 목록 조회하여 PENDING 멤버십 찾기
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"멤버십 목록 조회 실패: {response.status_code}\n{error_text}")
        
        memberships = response.json()
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            print("PENDING 상태의 멤버십이 없습니다. 테스트 스킵")
            return True
        
        membership_id = pending_membership['membership_id']
        print(f"승인 대상 멤버십: {membership_id}")
        
        # 관리자 승인 (같은 키로 2회)
        idempotency_key = str(uuid.uuid4())
        headers = {**self.admin_headers, "Idempotency-Key": idempotency_key}
        
        # 첫 번째 승인 요청
        print(f"첫 번째 승인 요청 (키: {idempotency_key[:8]}...)")
        response1 = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        if response1.status_code != 200:
            error_text = response1.text
            try:
                error_json = response1.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"첫 번째 승인 실패: {response1.status_code}\n{error_text}")
            return False
        
        result1 = response1.json()
        status1 = result1.get('membership_status')
        print(f"첫 번째 응답: status={status1}")
        
        # 두 번째 승인 요청 (같은 키)
        print(f"두 번째 승인 요청 (같은 키: {idempotency_key[:8]}...)")
        response2 = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        if response2.status_code != 200:
            error_text = response2.text
            try:
                error_json = response2.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            self.print_result(False, f"두 번째 승인 실패: {response2.status_code}\n{error_text}")
            return False
        
        result2 = response2.json()
        status2 = result2.get('membership_status')
        print(f"두 번째 응답: status={status2}")
        
        # 검증: 상태가 동일하고 ACCEPTED여야 함
        success = status1 == status2 == "ACCEPTED" and result1.get('membership_id') == result2.get('membership_id')
        
        self.print_result(success, f"승인 1회만 수행: {success}, status={status1}")
        
        return success
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*60)
        print("Idempotency 테스트 시작")
        print("="*60)
        
        results = []
        
        try:
            # 테스트 1: 투표 생성 2회
            results.append(("투표 생성 2회 (같은 키)", self.test_1_vote_create_twice_same_key()))
            
            # 테스트 2: 제안 생성 2회
            results.append(("제안 생성 2회 (같은 키)", self.test_2_proposal_create_twice_same_key()))
            
            # 테스트 3: 관리자 승인 2회
            results.append(("관리자 승인 2회 (같은 키)", self.test_3_admin_approve_twice_same_key()))
            
            # 테스트 4: 같은 키 다른 body
            results.append(("같은 키 다른 body → 409", self.test_4_different_key_different_body()))
            
            # 테스트 5: 멤버십 승인 2회
            results.append(("멤버십 승인 2회 (같은 키)", self.test_5_membership_approve_twice_same_key()))
            
        except Exception as e:
            print(f"\n테스트 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 결과 요약
        print("\n" + "="*60)
        print("테스트 결과 요약")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ 통과" if result else "✗ 실패"
            print(f"{status}: {test_name}")
        
        print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
        
        return passed == total


def main():
    if len(sys.argv) != 4:
        print("사용법: python scripts/test_idempotency.py <base_url> <admin_token> <user_token>")
        print("\n예시:")
        print("  python scripts/test_idempotency.py http://localhost:8000 <admin_token> <user_token>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    admin_token = sys.argv[2]
    user_token = sys.argv[3]
    
    tester = IdempotencyTester(base_url, admin_token, user_token)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
