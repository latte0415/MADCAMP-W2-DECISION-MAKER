"""
제안 상태 변경 API 테스트 (관리자용)

테스트 항목:
- PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status - 전제 제안 상태 변경
- PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status - 기준 제안 상태 변경
- PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status - 결론 제안 상태 변경
"""

import requests
from scripts.test.base import BaseAPITester


class ProposalStatusAPITester(BaseAPITester):
    """제안 상태 변경 API 테스트 클래스 (관리자용)"""
    
    def test_assumption_proposal_status_update(self) -> bool:
        """PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status - 전제 제안 상태 변경"""
        self.print_test("전제 제안 상태 변경")
        
        # 완전히 설정된 이벤트 준비 (제안 생성은 IN_PROGRESS 상태에서만 가능)
        self.setup_complete_event(start_event=True)
        
        # 제안이 없으면 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            self.admin_headers.get("Authorization", "").replace("Bearer ", ""),
            self.user_headers.get("Authorization", "").replace("Bearer ", "")
        )
        # 상태 공유
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "assumption_creation" not in detail_tester.proposal_ids:
            detail_tester.test_assumption_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 관리자로 상태 변경
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "proposal_status"]
            )
            
            assert data["proposal_status"] == "ACCEPTED", "제안 상태가 ACCEPTED여야 합니다"
            assert data["id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"전제 제안 상태 변경 성공: {proposal_id} -> ACCEPTED")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_status_update(self) -> bool:
        """PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status - 기준 제안 상태 변경"""
        self.print_test("기준 제안 상태 변경")
        
        # 완전히 설정된 이벤트 준비 (제안 생성은 IN_PROGRESS 상태에서만 가능)
        self.setup_complete_event(start_event=True)
        
        # 제안이 없으면 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            self.admin_headers.get("Authorization", "").replace("Bearer ", ""),
            self.user_headers.get("Authorization", "").replace("Bearer ", "")
        )
        # 상태 공유
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "criteria_modification" not in detail_tester.proposal_ids:
            detail_tester.test_criteria_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("criteria_modification")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 관리자로 상태 변경
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "proposal_status"]
            )
            
            assert data["proposal_status"] == "ACCEPTED", "제안 상태가 ACCEPTED여야 합니다"
            assert data["id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"기준 제안 상태 변경 성공: {proposal_id} -> ACCEPTED")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_status_update(self) -> bool:
        """PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status - 결론 제안 상태 변경"""
        self.print_test("결론 제안 상태 변경")
        
        # 완전히 설정된 이벤트 준비 (제안 생성은 IN_PROGRESS 상태에서만 가능)
        self.setup_complete_event(start_event=True)
        
        # 제안이 없으면 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            self.admin_headers.get("Authorization", "").replace("Bearer ", ""),
            self.user_headers.get("Authorization", "").replace("Bearer ", "")
        )
        # 상태 공유
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "conclusion" not in detail_tester.proposal_ids:
            detail_tester.test_conclusion_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("conclusion")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 관리자로 상태 변경
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "proposal_status"]
            )
            
            assert data["proposal_status"] == "ACCEPTED", "제안 상태가 ACCEPTED여야 합니다"
            assert data["id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"결론 제안 상태 변경 성공: {proposal_id} -> ACCEPTED")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_assumption_proposal_status_update_error_not_admin(self) -> bool:
        """PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status - 관리자 아님 에러"""
        self.print_test("전제 제안 상태 변경 - 관리자 아님 에러")
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "assumption_creation" not in detail_tester.proposal_ids:
            detail_tester.test_assumption_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # user로 상태 변경 시도
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_status_update_error_not_pending(self) -> bool:
        """PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status - PENDING 아님 에러"""
        self.print_test("전제 제안 상태 변경 - PENDING 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 및 승인
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        detail_tester.proposal_ids = {}  # 제안 ID 초기화
        
        # 제안 생성
        detail_tester.test_assumption_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 제안 승인
        approve_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=approve_headers,
            json={"status": "ACCEPTED"}
        )
        
        # 이미 승인된 제안 상태 변경 시도 (새로운 idempotency key 사용)
        update_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers=update_headers,
            json={"status": "REJECTED"}
        )
        
        try:
            # 이미 승인된 제안은 400 (PENDING 아님) 또는 409 (이미 승인됨) 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains=["accepted", "승인"])
            else:
                self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_status_update_error_nonexistent(self) -> bool:
        """PATCH /v1/events/{event_id}/assumption-proposals/{proposal_id}/status - 제안 없음 에러"""
        self.print_test("전제 제안 상태 변경 - 제안 없음 에러")
        
        # 이벤트 생성
        self.setup_complete_event(start_event=True)
        
        import uuid
        fake_proposal_id = str(uuid.uuid4())
        
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{fake_proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "제안 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_status_update_error_not_admin(self) -> bool:
        """PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status - 관리자 아님 에러"""
        self.print_test("기준 제안 상태 변경 - 관리자 아님 에러")
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "criteria_modification" not in detail_tester.proposal_ids:
            detail_tester.test_criteria_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("criteria_modification")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # user로 상태 변경 시도
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_status_update_error_not_pending(self) -> bool:
        """PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status - PENDING 아님 에러"""
        self.print_test("기준 제안 상태 변경 - PENDING 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 및 승인
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        detail_tester.proposal_ids = {}  # 제안 ID 초기화
        
        # 제안 생성
        detail_tester.test_criteria_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("criteria_modification")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 제안 승인
        approve_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers=approve_headers,
            json={"status": "ACCEPTED"}
        )
        
        # 이미 승인된 제안 상태 변경 시도 (새로운 idempotency key 사용)
        update_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers=update_headers,
            json={"status": "REJECTED"}
        )
        
        try:
            # 이미 승인된 제안은 400 (PENDING 아님) 또는 409 (이미 승인됨) 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains=["accepted", "승인"])
            else:
                self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_status_update_error_nonexistent(self) -> bool:
        """PATCH /v1/events/{event_id}/criteria-proposals/{proposal_id}/status - 제안 없음 에러"""
        self.print_test("기준 제안 상태 변경 - 제안 없음 에러")
        
        # 이벤트 생성
        self.setup_complete_event(start_event=True)
        
        import uuid
        fake_proposal_id = str(uuid.uuid4())
        
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{fake_proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "제안 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_status_update_error_not_admin(self) -> bool:
        """PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status - 관리자 아님 에러"""
        self.print_test("결론 제안 상태 변경 - 관리자 아님 에러")
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 (user로)
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        
        if "conclusion" not in detail_tester.proposal_ids:
            detail_tester.test_conclusion_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("conclusion")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # user로 상태 변경 시도
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="관리자")
            self.print_result(True, "관리자 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_status_update_error_not_pending(self) -> bool:
        """PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status - PENDING 아님 에러"""
        self.print_test("결론 제안 상태 변경 - PENDING 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        # 제안 생성 및 승인
        from scripts.test.test_event_detail import EventDetailAPITester
        detail_tester = EventDetailAPITester(
            self.base_url,
            admin_token=None,
            user_token=None,
            admin_email=self.admin_email,
            admin_password=self.admin_password,
            user_email=self.user_email,
            user_password=self.user_password,
            print_auth_info=False
        )
        detail_tester.event_id = self.event_id
        detail_tester.entrance_code = self.entrance_code
        detail_tester.event_status = self.event_status
        detail_tester.option_ids = self.option_ids
        detail_tester.criterion_ids = self.criterion_ids
        detail_tester.assumption_ids = self.assumption_ids
        detail_tester.proposal_ids = {}  # 제안 ID 초기화
        
        # 제안 생성
        detail_tester.test_conclusion_proposal_create()
        
        proposal_id = detail_tester.proposal_ids.get("conclusion")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 제안 승인
        approve_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers=approve_headers,
            json={"status": "ACCEPTED"}
        )
        
        # 이미 승인된 제안 상태 변경 시도 (새로운 idempotency key 사용)
        update_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers=update_headers,
            json={"status": "REJECTED"}
        )
        
        try:
            # 이미 승인된 제안은 400 (PENDING 아님) 또는 409 (이미 승인됨) 모두 가능
            if response.status_code == 409:
                self.assert_error_response(response, 409, expected_message_contains=["accepted", "승인"])
            else:
                self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_status_update_error_nonexistent(self) -> bool:
        """PATCH /v1/events/{event_id}/conclusion-proposals/{proposal_id}/status - 제안 없음 에러"""
        self.print_test("결론 제안 상태 변경 - 제안 없음 에러")
        
        # 이벤트 생성
        self.setup_complete_event(start_event=True)
        
        import uuid
        fake_proposal_id = str(uuid.uuid4())
        
        payload = {
            "status": "ACCEPTED"
        }
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{fake_proposal_id}/status",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "제안 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 제안 상태 변경 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["assumption_status_update"] = safe_run("test_assumption_proposal_status_update", self.test_assumption_proposal_status_update)
        results["criteria_status_update"] = safe_run("test_criteria_proposal_status_update", self.test_criteria_proposal_status_update)
        results["conclusion_status_update"] = safe_run("test_conclusion_proposal_status_update", self.test_conclusion_proposal_status_update)
        
        # 에러 케이스
        results["assumption_status_update_error_not_admin"] = safe_run("test_assumption_proposal_status_update_error_not_admin", self.test_assumption_proposal_status_update_error_not_admin)
        results["assumption_status_update_error_not_pending"] = safe_run("test_assumption_proposal_status_update_error_not_pending", self.test_assumption_proposal_status_update_error_not_pending)
        results["assumption_status_update_error_nonexistent"] = safe_run("test_assumption_proposal_status_update_error_nonexistent", self.test_assumption_proposal_status_update_error_nonexistent)
        results["criteria_status_update_error_not_admin"] = safe_run("test_criteria_proposal_status_update_error_not_admin", self.test_criteria_proposal_status_update_error_not_admin)
        results["criteria_status_update_error_not_pending"] = safe_run("test_criteria_proposal_status_update_error_not_pending", self.test_criteria_proposal_status_update_error_not_pending)
        results["criteria_status_update_error_nonexistent"] = safe_run("test_criteria_proposal_status_update_error_nonexistent", self.test_criteria_proposal_status_update_error_nonexistent)
        results["conclusion_status_update_error_not_admin"] = safe_run("test_conclusion_proposal_status_update_error_not_admin", self.test_conclusion_proposal_status_update_error_not_admin)
        results["conclusion_status_update_error_not_pending"] = safe_run("test_conclusion_proposal_status_update_error_not_pending", self.test_conclusion_proposal_status_update_error_not_pending)
        results["conclusion_status_update_error_nonexistent"] = safe_run("test_conclusion_proposal_status_update_error_nonexistent", self.test_conclusion_proposal_status_update_error_nonexistent)
        
        return results
