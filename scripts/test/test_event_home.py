"""
홈/참가 API 테스트

테스트 항목:
- GET /v1/events/participated - 참가한 이벤트 목록 조회
- POST /v1/events/entry - 이벤트 입장 (코드로 참가)
- GET /v1/events/{event_id}/overview - 이벤트 오버뷰 정보 조회
"""

import requests
from scripts.test.base import BaseAPITester


class EventHomeAPITester(BaseAPITester):
    """홈/참가 API 테스트 클래스"""
    
    def test_events_participated(self) -> bool:
        """GET /v1/events/participated - 참가한 이벤트 목록 조회"""
        self.print_test("참가한 이벤트 목록 조회")
        
        response = requests.get(
            f"{self.base_url}/v1/events/participated",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(response, 200)
            
            # 응답은 리스트여야 함
            assert isinstance(data, list), "응답은 리스트여야 합니다"
            
            # 각 이벤트 항목 검증
            for event in data:
                assert "id" in event, "이벤트에 id가 있어야 합니다"
                assert "decision_subject" in event, "이벤트에 decision_subject가 있어야 합니다"
                assert "event_status" in event, "이벤트에 event_status가 있어야 합니다"
                assert "membership_status" in event, "이벤트에 membership_status가 있어야 합니다"
            
            self.print_result(True, f"참가한 이벤트 {len(data)}개 조회 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_entry(self) -> bool:
        """POST /v1/events/entry - 이벤트 입장 (코드로 참가)"""
        self.print_test("이벤트 입장")
        
        # 이벤트가 없으면 생성
        if not self.event_id:
            self.setup_test_event()
        
        if not self.entrance_code:
            self.print_result(False, "입장 코드가 없습니다")
            return False
        
        payload = {
            "entrance_code": self.entrance_code
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            # 이미 참가 중이면 409, 새로 참가하면 201
            if response.status_code == 201:
                data = self.assert_response(response, 201, required_fields=["message", "event_id"])
                assert data["event_id"] == self.event_id, "이벤트 ID가 일치해야 합니다"
                self.print_result(True, "이벤트 입장 성공")
                return True
            elif response.status_code == 409:
                # 이미 참가 중인 경우도 정상
                self.print_result(True, "이미 참가 중인 이벤트입니다")
                return True
            else:
                self.assert_response(response, 201)
                return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_overview(self) -> bool:
        """GET /v1/events/{event_id}/overview - 이벤트 오버뷰 정보 조회"""
        self.print_test("이벤트 오버뷰 조회")
        
        # 이벤트가 없으면 생성
        if not self.event_id:
            self.setup_test_event()
            self.join_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/overview",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["event", "options", "admin", "participant_count", "membership_status", "can_enter"]
            )
            
            # event 검증
            assert "id" in data["event"], "event에 id가 있어야 합니다"
            assert "decision_subject" in data["event"], "event에 decision_subject가 있어야 합니다"
            assert data["event"]["id"] == self.event_id, "이벤트 ID가 일치해야 합니다"
            
            # options 검증
            assert isinstance(data["options"], list), "options는 리스트여야 합니다"
            for option in data["options"]:
                assert "id" in option, "옵션에 id가 있어야 합니다"
                assert "content" in option, "옵션에 content가 있어야 합니다"
            
            # admin 검증
            assert "id" in data["admin"], "admin에 id가 있어야 합니다"
            assert "email" in data["admin"], "admin에 email이 있어야 합니다"
            
            # participant_count 검증
            assert isinstance(data["participant_count"], int), "participant_count는 정수여야 합니다"
            assert data["participant_count"] >= 0, "participant_count는 0 이상이어야 합니다"
            
            # membership_status 검증
            assert data["membership_status"] in ["PENDING", "ACCEPTED", "REJECTED"], "유효한 membership_status여야 합니다"
            
            # can_enter 검증
            assert isinstance(data["can_enter"], bool), "can_enter는 boolean이어야 합니다"
            
            self.print_result(True, f"이벤트 오버뷰 조회 성공: {data['event']['decision_subject']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_events_entry_error_invalid_code(self) -> bool:
        """POST /v1/events/entry - 존재하지 않는 입장 코드 에러"""
        self.print_test("이벤트 입장 - 존재하지 않는 입장 코드 에러")
        
        # 6자 이하의 유효하지 않은 코드 사용 (validation error가 아닌 404를 테스트하기 위해)
        # 실제로 존재하지 않는 6자리 코드 사용
        payload = {
            "entrance_code": "XXXXXX"  # 존재하지 않는 코드
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            # 404 (존재하지 않음) 또는 422 (validation error) 모두 가능
            if response.status_code == 422:
                # validation error인 경우도 정상 (잘못된 형식)
                self.assert_error_response(response, 422)
            else:
                self.assert_error_response(response, 404)
            self.print_result(True, "존재하지 않는 입장 코드 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_entry_error_already_joined(self) -> bool:
        """POST /v1/events/entry - 이미 참가 중 에러"""
        self.print_test("이벤트 입장 - 이미 참가 중 에러")
        
        # 이벤트 생성 및 입장
        if not self.event_id:
            self.setup_test_event()
        
        if not self.entrance_code:
            self.print_result(False, "입장 코드가 없습니다")
            return False
        
        # 첫 번째 입장
        payload = {
            "entrance_code": self.entrance_code
        }
        requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json=payload
        )
        
        # 두 번째 입장 시도
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            # 409는 정상 동작 (이미 참가 중)
            if response.status_code == 409:
                self.print_result(True, "이미 참가 중 에러 확인 성공 (409)")
                return True
            else:
                self.assert_error_response(response, 409)
                return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_entry_error_no_auth(self) -> bool:
        """POST /v1/events/entry - 인증 없음 에러"""
        self.print_test("이벤트 입장 - 인증 없음 에러")
        
        if not self.event_id:
            self.setup_test_event()
        
        if not self.entrance_code:
            self.print_result(False, "입장 코드가 없습니다")
            return False
        
        payload = {
            "entrance_code": self.entrance_code
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 401)
            self.print_result(True, "인증 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_overview_error_nonexistent_event(self) -> bool:
        """GET /v1/events/{event_id}/overview - 존재하지 않는 이벤트 에러"""
        self.print_test("이벤트 오버뷰 조회 - 존재하지 않는 이벤트 에러")
        
        import uuid
        fake_event_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{self.base_url}/v1/events/{fake_event_id}/overview",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "존재하지 않는 이벤트 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_events_overview_error_no_auth(self) -> bool:
        """GET /v1/events/{event_id}/overview - 인증 없음 에러"""
        self.print_test("이벤트 오버뷰 조회 - 인증 없음 에러")
        
        if not self.event_id:
            self.setup_test_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/overview"
        )
        
        try:
            self.assert_error_response(response, 401)
            self.print_result(True, "인증 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 홈/참가 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["participated"] = safe_run("test_events_participated", self.test_events_participated)
        results["entry"] = safe_run("test_events_entry", self.test_events_entry)
        results["overview"] = safe_run("test_events_overview", self.test_events_overview)
        
        # 에러 케이스
        results["entry_error_invalid_code"] = safe_run("test_events_entry_error_invalid_code", self.test_events_entry_error_invalid_code)
        results["entry_error_already_joined"] = safe_run("test_events_entry_error_already_joined", self.test_events_entry_error_already_joined)
        results["entry_error_no_auth"] = safe_run("test_events_entry_error_no_auth", self.test_events_entry_error_no_auth)
        results["overview_error_nonexistent_event"] = safe_run("test_events_overview_error_nonexistent_event", self.test_events_overview_error_nonexistent_event)
        results["overview_error_no_auth"] = safe_run("test_events_overview_error_no_auth", self.test_events_overview_error_no_auth)
        
        return results
