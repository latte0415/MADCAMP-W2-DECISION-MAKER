"""
멤버십 관리 API 테스트 (관리자용)

테스트 항목:
- GET /v1/events/{event_id}/memberships - 멤버십 목록 조회
- PATCH /v1/events/{event_id}/memberships/{membership_id}/approve - 멤버십 승인
- PATCH /v1/events/{event_id}/memberships/{membership_id}/reject - 멤버십 거부
- POST /v1/events/{event_id}/memberships/bulk-approve - 멤버십 일괄 승인
- POST /v1/events/{event_id}/memberships/bulk-reject - 멤버십 일괄 거부
"""

import requests
from scripts.test.base import BaseAPITester


class MembershipAPITester(BaseAPITester):
    """멤버십 관리 API 테스트 클래스 (관리자용)"""
    
    def test_memberships_list(self) -> bool:
        """GET /v1/events/{event_id}/memberships - 멤버십 목록 조회"""
        self.print_test("멤버십 목록 조회")
        
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        
        try:
            data = self.assert_response(response, 200)
            
            assert isinstance(data, list), "응답은 리스트여야 합니다"
            
            # 각 멤버십 검증
            for membership in data:
                assert "user_id" in membership, "멤버십에 user_id가 있어야 합니다"
                assert "membership_id" in membership, "멤버십에 membership_id가 있어야 합니다"
                assert "status" in membership, "멤버십에 status가 있어야 합니다"
                assert membership["status"] in ["PENDING", "ACCEPTED", "REJECTED"], "유효한 상태여야 합니다"
            
            self.print_result(True, f"멤버십 목록 조회 성공: {len(data)}개")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_membership_approve(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/approve - 멤버십 승인"""
        self.print_test("멤버십 승인")
        
        # 멤버십이 없으면 생성
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        # PENDING 상태의 멤버십 찾기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            self.print_result(True, "승인할 PENDING 멤버십이 없습니다 (스킵)")
            return True
        
        membership_id = pending_membership['membership_id']
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "membership_id", "membership_status"]
            )
            
            assert data["membership_status"] == "ACCEPTED", "멤버십 상태가 ACCEPTED여야 합니다"
            assert data["membership_id"] == membership_id, "멤버십 ID가 일치해야 합니다"
            
            self.membership_id = membership_id
            
            self.print_result(True, f"멤버십 승인 성공: {membership_id}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_membership_reject(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/reject - 멤버십 거부"""
        self.print_test("멤버십 거부")
        
        # 새로운 이벤트 생성 및 입장 (거부할 멤버십 준비)
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        # PENDING 상태의 멤버십 찾기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            self.print_result(True, "거부할 PENDING 멤버십이 없습니다 (스킵)")
            return True
        
        membership_id = pending_membership['membership_id']
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/reject",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "membership_id", "membership_status"]
            )
            
            assert data["membership_status"] == "REJECTED", "멤버십 상태가 REJECTED여야 합니다"
            assert data["membership_id"] == membership_id, "멤버십 ID가 일치해야 합니다"
            
            self.print_result(True, f"멤버십 거부 성공: {membership_id}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_bulk_approve(self) -> bool:
        """POST /v1/events/{event_id}/memberships/bulk-approve - 멤버십 일괄 승인"""
        self.print_test("멤버십 일괄 승인")
        
        # 새로운 이벤트 생성 및 입장 (승인할 멤버십 준비)
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/bulk-approve",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "approved_count", "failed_count"]
            )
            
            assert isinstance(data["approved_count"], int), "approved_count는 정수여야 합니다"
            assert isinstance(data["failed_count"], int), "failed_count는 정수여야 합니다"
            assert data["approved_count"] >= 0, "approved_count는 0 이상이어야 합니다"
            assert data["failed_count"] >= 0, "failed_count는 0 이상이어야 합니다"
            
            self.print_result(
                True,
                f"멤버십 일괄 승인 성공: 승인={data['approved_count']}, 실패={data['failed_count']}"
            )
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_bulk_reject(self) -> bool:
        """POST /v1/events/{event_id}/memberships/bulk-reject - 멤버십 일괄 거부"""
        self.print_test("멤버십 일괄 거부")
        
        # 새로운 이벤트 생성 및 입장 (거부할 멤버십 준비)
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/bulk-reject",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "rejected_count"]
            )
            
            assert isinstance(data["rejected_count"], int), "rejected_count는 정수여야 합니다"
            assert data["rejected_count"] >= 0, "rejected_count는 0 이상이어야 합니다"
            
            self.print_result(True, f"멤버십 일괄 거부 성공: 거부={data['rejected_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_memberships_list_error_not_admin(self) -> bool:
        """GET /v1/events/{event_id}/memberships - 관리자 아님 에러"""
        self.print_test("멤버십 목록 조회 - 관리자 아님 에러")
        
        if not self.event_id:
            self.setup_test_event()
        
        # user로 조회 시도
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_approve_error_not_admin(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/approve - 관리자 아님 에러"""
        self.print_test("멤버십 승인 - 관리자 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 새 이벤트 생성 및 입장 (독립적인 테스트를 위해)
        # 자동 승인 비활성화하여 PENDING 상태 유지
        self.setup_test_event(auto_approve=False)
        self.join_event()
        
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status != "PENDING":
            # 이미 승인된 경우, 새 이벤트 생성
            self.event_id = None
            self.entrance_code = None
            self.setup_test_event(auto_approve=False)
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        if membership_status != "PENDING":
            self.print_result(False, f"멤버십이 PENDING 상태가 아닙니다. 현재 상태: {membership_status}")
            return False
        
        # 멤버십 ID 가져오기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            self.print_result(False, "승인할 PENDING 멤버십이 없습니다")
            return False
        
        membership_id = pending_membership['membership_id']
        
        # user로 승인 시도
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_approve_error_max_exceeded(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/approve - 최대 인원 초과 에러"""
        self.print_test("멤버십 승인 - 최대 인원 초과 에러")
        
        # 최대 인원이 1인 이벤트 생성 (admin이 이미 멤버이므로 user는 승인 불가)
        entrance_code = self.generate_entrance_code()
        payload = {
            "decision_subject": "최대 인원 1인 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 1,  # 최대 인원 1명 (admin만 가능)
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "conclusion_is_auto_approved_by_votes": False,
            "membership_is_auto_approved": False,
            "options": [{"content": "옵션 1"}],
            "assumptions": [{"content": "전제 1"}],
            "criteria": [{"content": "기준 1"}]
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events",
            headers=self.admin_headers,
            json=payload
        )
        data = self.assert_response(response, 201)
        event_id = str(data["id"])
        
        # user 입장
        entry_response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json={"entrance_code": entrance_code}
        )
        if entry_response.status_code not in [201, 409]:  # 409는 이미 입장한 경우
            self.print_result(False, f"이벤트 입장 실패: {entry_response.status_code}")
            return False
        
        # 멤버십 목록 조회
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            self.print_result(False, "승인할 PENDING 멤버십이 없습니다")
            return False
        
        membership_id = pending_membership['membership_id']
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        try:
            # 409 Conflict (멤버십 한계 도달) 또는 400 Bad Request 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains="인원")
            else:
                self.assert_error_response(response, 400, expected_message_contains="인원")
            self.print_result(True, "최대 인원 초과 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_approve_error_not_pending(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/approve - PENDING 아님 에러"""
        self.print_test("멤버십 승인 - PENDING 아님 에러")
        
        # 새 이벤트 생성 및 멤버십 승인 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        self.approve_user_membership()
        
        # 이미 승인된 멤버십 ID 가져오기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        accepted_membership = None
        for m in memberships:
            if m.get('status') == 'ACCEPTED' and not m.get('is_admin'):
                accepted_membership = m
                break
        
        if not accepted_membership:
            self.print_result(False, "ACCEPTED 멤버십이 없습니다")
            return False
        
        membership_id = accepted_membership['membership_id']
        
        # 이미 승인된 멤버십을 다시 승인 시도
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=headers
        )
        
        try:
            # 409 Conflict (이미 승인됨) 또는 400 Bad Request 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains="approved")
            else:
                self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_reject_error_not_admin(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/reject - 관리자 아님 에러"""
        self.print_test("멤버십 거부 - 관리자 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 새 이벤트 생성 및 입장 (독립적인 테스트를 위해)
        # 자동 승인 비활성화하여 PENDING 상태 유지
        self.setup_test_event(auto_approve=False)
        self.join_event()
        
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status != "PENDING":
            # 이미 승인된 경우, 새 이벤트 생성
            self.event_id = None
            self.entrance_code = None
            self.setup_test_event(auto_approve=False)
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        if membership_status != "PENDING":
            self.print_result(False, f"멤버십이 PENDING 상태가 아닙니다. 현재 상태: {membership_status}")
            return False
        
        # 멤버십 ID 가져오기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            self.print_result(False, "거부할 PENDING 멤버십이 없습니다")
            return False
        
        membership_id = pending_membership['membership_id']
        
        # user로 거부 시도
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/reject",
            headers=headers
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_memberships_reject_error_not_pending(self) -> bool:
        """PATCH /v1/events/{event_id}/memberships/{membership_id}/reject - PENDING 아님 에러"""
        self.print_test("멤버십 거부 - PENDING 아님 에러")
        
        # 새 이벤트 생성 및 멤버십 승인 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        self.approve_user_membership()
        
        # 이미 승인된 멤버십 ID 가져오기
        memberships_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        memberships = self.assert_response(memberships_response, 200)
        
        accepted_membership = None
        for m in memberships:
            if m.get('status') == 'ACCEPTED' and not m.get('is_admin'):
                accepted_membership = m
                break
        
        if not accepted_membership:
            self.print_result(False, "ACCEPTED 멤버십이 없습니다")
            return False
        
        membership_id = accepted_membership['membership_id']
        
        # 이미 승인된 멤버십을 거부 시도
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/reject",
            headers=headers
        )
        
        try:
            # 409 Conflict (이미 승인됨) 또는 400 Bad Request 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains="approved")
            else:
                self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 멤버십 관리 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["list"] = safe_run("test_memberships_list", self.test_memberships_list)
        results["approve"] = safe_run("test_membership_approve", self.test_membership_approve)
        results["reject"] = safe_run("test_membership_reject", self.test_membership_reject)
        results["bulk_approve"] = safe_run("test_memberships_bulk_approve", self.test_memberships_bulk_approve)
        results["bulk_reject"] = safe_run("test_memberships_bulk_reject", self.test_memberships_bulk_reject)
        
        # 에러 케이스
        results["list_error_not_admin"] = safe_run("test_memberships_list_error_not_admin", self.test_memberships_list_error_not_admin)
        results["approve_error_not_admin"] = safe_run("test_memberships_approve_error_not_admin", self.test_memberships_approve_error_not_admin)
        results["approve_error_max_exceeded"] = safe_run("test_memberships_approve_error_max_exceeded", self.test_memberships_approve_error_max_exceeded)
        results["approve_error_not_pending"] = safe_run("test_memberships_approve_error_not_pending", self.test_memberships_approve_error_not_pending)
        results["reject_error_not_admin"] = safe_run("test_memberships_reject_error_not_admin", self.test_memberships_reject_error_not_admin)
        results["reject_error_not_pending"] = safe_run("test_memberships_reject_error_not_pending", self.test_memberships_reject_error_not_pending)
        
        return results
