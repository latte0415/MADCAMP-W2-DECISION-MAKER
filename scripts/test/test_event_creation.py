"""
이벤트 생성 API 테스트

테스트 항목:
- POST /v1/events - 이벤트 생성
- POST /v1/events/entrance-code/check - 입장 코드 중복 확인
- GET /v1/events/entrance-code/generate - 랜덤 입장 코드 생성
"""

import requests
from scripts.test.base import BaseAPITester


class EventCreationAPITester(BaseAPITester):
    """이벤트 생성 API 테스트 클래스"""
    
    def test_events_create(self) -> bool:
        """POST /v1/events - 이벤트 생성"""
        self.print_test("이벤트 생성")
        
        entrance_code = self.generate_entrance_code()
        
        payload = {
            "decision_subject": "API 테스트용 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "conclusion_is_auto_approved_by_votes": False,
            "membership_is_auto_approved": False,
            "options": [
                {"content": "옵션 1"},
                {"content": "옵션 2"},
                {"content": "옵션 3"}
            ],
            "assumptions": [
                {"content": "전제 1"},
                {"content": "전제 2"}
            ],
            "criteria": [
                {"content": "기준 1"},
                {"content": "기준 2"},
                {"content": "기준 3"}
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events",
            headers=self.admin_headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["id", "decision_subject", "entrance_code", "event_status"]
            )
            
            # 응답 검증
            assert data["decision_subject"] == payload["decision_subject"], "주제가 일치해야 합니다"
            assert data["entrance_code"] == entrance_code, "입장 코드가 일치해야 합니다"
            assert data["event_status"] == "NOT_STARTED", "초기 상태는 NOT_STARTED여야 합니다"
            assert data["admin_id"] is not None, "admin_id가 있어야 합니다"
            
            # 상태 저장
            self.event_id = str(data["id"])
            self.entrance_code = entrance_code
            
            self.print_result(True, f"이벤트 생성 성공: {self.event_id}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_entrance_code_check(self) -> bool:
        """POST /v1/events/entrance-code/check - 입장 코드 중복 확인"""
        self.print_test("입장 코드 중복 확인")
        
        # 사용 가능한 코드 확인
        test_code = self.generate_entrance_code()
        
        payload = {
            "entrance_code": test_code
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/entrance-code/check",
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["entrance_code", "is_available"]
            )
            
            # 응답 검증
            assert data["entrance_code"] == test_code, "입장 코드가 일치해야 합니다"
            assert isinstance(data["is_available"], bool), "is_available은 boolean이어야 합니다"
            
            # 이미 사용 중인 코드 확인 (이벤트 생성 후)
            if self.entrance_code:
                payload_existing = {
                    "entrance_code": self.entrance_code
                }
                response_existing = requests.post(
                    f"{self.base_url}/v1/events/entrance-code/check",
                    json=payload_existing
                )
                data_existing = self.assert_response(response_existing, 200)
                assert data_existing["is_available"] == False, "이미 사용 중인 코드는 사용 불가능해야 합니다"
            
            self.print_result(True, f"입장 코드 확인 성공: {test_code} (사용 가능: {data['is_available']})")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_entrance_code_generate(self) -> bool:
        """GET /v1/events/entrance-code/generate - 랜덤 입장 코드 생성"""
        self.print_test("랜덤 입장 코드 생성")
        
        response = requests.get(
            f"{self.base_url}/v1/events/entrance-code/generate"
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["code"]
            )
            
            # 응답 검증
            code = data["code"]
            assert len(code) == 6, "코드는 6자리여야 합니다"
            assert code.isalnum(), "코드는 영문자와 숫자만 포함해야 합니다"
            assert code.isupper() or code.isdigit() or any(c.isdigit() for c in code), "코드는 대문자와 숫자만 포함해야 합니다"
            
            self.print_result(True, f"랜덤 입장 코드 생성 성공: {code}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_events_create_error_duplicate_entrance_code(self) -> bool:
        """POST /v1/events - 중복 입장 코드 에러"""
        self.print_test("이벤트 생성 - 중복 입장 코드 에러")
        
        # 먼저 이벤트 생성
        entrance_code = self.generate_entrance_code()
        payload = {
            "decision_subject": "첫 번째 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "conclusion_is_auto_approved_by_votes": False,
            "membership_is_auto_approved": False,
            "options": [{"content": "옵션 1"}],
            "assumptions": [{"content": "전제 1"}],
            "criteria": [{"content": "기준 1"}]
        }
        requests.post(f"{self.base_url}/v1/events", headers=self.admin_headers, json=payload)
        
        # 같은 입장 코드로 다시 생성 시도
        payload2 = {
            "decision_subject": "두 번째 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
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
            json=payload2
        )
        
        try:
            self.assert_error_response(response, 409, expected_message_contains="입장 코드")
            self.print_result(True, "중복 입장 코드 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_create_error_invalid_entrance_code(self) -> bool:
        """POST /v1/events - 잘못된 입장 코드 형식 에러"""
        self.print_test("이벤트 생성 - 잘못된 입장 코드 형식 에러")
        
        payload = {
            "decision_subject": "테스트 이벤트",
            "entrance_code": "abc",  # 6자리가 아님
            "max_membership": 10,
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
        
        try:
            self.assert_error_response(response, 422)  # FastAPI validation error
            self.print_result(True, "잘못된 입장 코드 형식 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_create_error_invalid_max_membership(self) -> bool:
        """POST /v1/events - 잘못된 max_membership 에러"""
        self.print_test("이벤트 생성 - 잘못된 max_membership 에러")
        
        entrance_code = self.generate_entrance_code()
        payload = {
            "decision_subject": "테스트 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 0,  # 1 미만
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
        
        try:
            self.assert_error_response(response, 422)  # FastAPI validation error
            self.print_result(True, "잘못된 max_membership 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_create_error_no_auth(self) -> bool:
        """POST /v1/events - 인증 없음 에러"""
        self.print_test("이벤트 생성 - 인증 없음 에러")
        
        entrance_code = self.generate_entrance_code()
        payload = {
            "decision_subject": "테스트 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
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
            json=payload
        )
        
        try:
            self.assert_error_response(response, 401)
            self.print_result(True, "인증 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 이벤트 생성 API 테스트 실행"""
        results = {}
        
        # 성공 케이스
        results["create"] = self.test_events_create()
        results["entrance_code_check"] = self.test_entrance_code_check()
        results["entrance_code_generate"] = self.test_entrance_code_generate()
        
        # 에러 케이스
        results["create_error_duplicate_entrance_code"] = self.test_events_create_error_duplicate_entrance_code()
        results["create_error_invalid_entrance_code"] = self.test_events_create_error_invalid_entrance_code()
        results["create_error_invalid_max_membership"] = self.test_events_create_error_invalid_max_membership()
        results["create_error_no_auth"] = self.test_events_create_error_no_auth()
        
        return results
