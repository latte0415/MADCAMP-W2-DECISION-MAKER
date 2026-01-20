"""
투표 API 테스트

테스트 항목:
- GET /v1/events/{event_id}/votes/me - 본인 투표 내역 조회
- POST /v1/events/{event_id}/votes - 투표 생성/업데이트
- GET /v1/events/{event_id}/votes/result - 투표 결과 조회
"""

import requests
from scripts.test.base import BaseAPITester


class VoteAPITester(BaseAPITester):
    """투표 API 테스트 클래스"""
    
    def test_votes_me(self) -> bool:
        """GET /v1/events/{event_id}/votes/me - 본인 투표 내역 조회"""
        self.print_test("본인 투표 내역 조회")
        
        # 투표 내역 조회는 멤버십 승인 후 가능 (이벤트 시작은 선택사항)
        self.setup_complete_event(start_event=False)
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/votes/me",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["option_id", "criterion_order", "decision_subject", "options", "criteria"]
            )
            
            # option_id는 null일 수 있음 (투표하지 않은 경우)
            assert data["option_id"] is None or isinstance(data["option_id"], str), "option_id는 null 또는 문자열이어야 합니다"
            assert isinstance(data["criterion_order"], list), "criterion_order는 리스트여야 합니다"
            assert isinstance(data["options"], list), "options는 리스트여야 합니다"
            assert isinstance(data["criteria"], list), "criteria는 리스트여야 합니다"
            
            self.print_result(True, f"본인 투표 내역 조회 성공 (투표 여부: {data['option_id'] is not None})")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_create(self) -> bool:
        """POST /v1/events/{event_id}/votes - 투표 생성/업데이트"""
        self.print_test("투표 생성/업데이트")
        
        # 투표는 IN_PROGRESS 상태에서만 가능
        self.setup_complete_event(start_event=True)
        
        # 이벤트 상태 확인
        current_status = self.get_event_status()
        if current_status != "IN_PROGRESS":
            self.print_result(False, f"투표는 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
            return False
        
        if not self.option_ids or not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.option_ids = [opt["id"] for opt in event_detail.get("options", [])]
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.option_ids or not self.criterion_ids:
            self.print_result(False, "옵션 또는 기준이 없습니다")
            return False
        
        if len(self.criterion_ids) < 2:
            self.print_result(False, "기준이 2개 이상 필요합니다")
            return False
        
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": self.criterion_ids
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["option_id", "criterion_order", "created_at"]
            )
            
            assert data["option_id"] == self.option_ids[0], "옵션 ID가 일치해야 합니다"
            assert data["criterion_order"] == self.criterion_ids, "기준 순서가 일치해야 합니다"
            
            self.print_result(True, f"투표 생성 성공: option={data['option_id']}, criteria={len(data['criterion_order'])}개")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_result(self) -> bool:
        """GET /v1/events/{event_id}/votes/result - 투표 결과 조회"""
        self.print_test("투표 결과 조회")
        
        # 완전히 설정된 이벤트 준비 (IN_PROGRESS 상태)
        self.setup_complete_event(start_event=True)
        
        # 투표가 없으면 생성
        if not self.option_ids or not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.option_ids = [opt["id"] for opt in event_detail.get("options", [])]
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.option_ids or not self.criterion_ids:
            self.print_result(False, "옵션 또는 기준이 없습니다")
            return False
        
        if len(self.criterion_ids) < 2:
            self.print_result(False, "기준이 2개 이상 필요합니다")
            return False
        
        # 투표 생성
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": self.criterion_ids
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 201:
            self.print_result(False, f"투표 생성 실패: {response.status_code}")
            return False
        
        # 이벤트를 FINISHED 상태로 변경 (IN_PROGRESS -> FINISHED)
        self.finish_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/votes/result",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=[
                    "total_participants_count",
                    "voted_participants_count",
                    "option_vote_counts",
                    "first_priority_criteria",
                    "weighted_criteria"
                ]
            )
            
            # 기본 필드 검증
            assert isinstance(data["total_participants_count"], int), "total_participants_count는 정수여야 합니다"
            assert isinstance(data["voted_participants_count"], int), "voted_participants_count는 정수여야 합니다"
            assert isinstance(data["option_vote_counts"], list), "option_vote_counts는 리스트여야 합니다"
            assert isinstance(data["first_priority_criteria"], list), "first_priority_criteria는 리스트여야 합니다"
            assert isinstance(data["weighted_criteria"], list), "weighted_criteria는 리스트여야 합니다"
            
            # option_vote_counts 검증
            for option_vote in data["option_vote_counts"]:
                assert "option_id" in option_vote, "option_vote에 option_id가 있어야 합니다"
                assert "option_content" in option_vote, "option_vote에 option_content가 있어야 합니다"
                assert "vote_count" in option_vote, "option_vote에 vote_count가 있어야 합니다"
            
            # first_priority_criteria 검증
            for criterion in data["first_priority_criteria"]:
                assert "criterion_id" in criterion, "criterion에 criterion_id가 있어야 합니다"
                assert "criterion_content" in criterion, "criterion에 criterion_content가 있어야 합니다"
                assert "count" in criterion, "criterion에 count가 있어야 합니다"
            
            # weighted_criteria 검증
            for criterion in data["weighted_criteria"]:
                assert "criterion_id" in criterion, "criterion에 criterion_id가 있어야 합니다"
                assert "criterion_content" in criterion, "criterion에 criterion_content가 있어야 합니다"
                assert "count" in criterion, "criterion에 count가 있어야 합니다"
            
            self.print_result(
                True,
                f"투표 결과 조회 성공: 참가자={data['total_participants_count']}, "
                f"투표자={data['voted_participants_count']}"
            )
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_votes_create_error_not_in_progress(self) -> bool:
        """POST /v1/events/{event_id}/votes - IN_PROGRESS 아님 에러"""
        self.print_test("투표 생성 - IN_PROGRESS 아님 에러")
        
        # 이벤트 생성만 하고 시작하지 않음
        self.setup_complete_event(start_event=False)
        
        if not self.option_ids or not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.option_ids = [opt["id"] for opt in event_detail.get("options", [])]
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.option_ids or not self.criterion_ids:
            self.print_result(False, "옵션 또는 기준이 없습니다")
            return False
        
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": self.criterion_ids
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "IN_PROGRESS 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_create_error_not_accepted(self) -> bool:
        """POST /v1/events/{event_id}/votes - 멤버십 미승인 에러"""
        self.print_test("투표 생성 - 멤버십 미승인 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 이벤트 생성 및 입장만 하고 승인하지 않음
        self.setup_test_event()
        self.join_event()
        self.start_event()
        
        if not self.option_ids or not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.option_ids = [opt["id"] for opt in event_setting.get("options", [])]
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.option_ids or not self.criterion_ids:
            self.print_result(False, "옵션 또는 기준이 없습니다")
            return False
        
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": self.criterion_ids
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="멤버십")
            self.print_result(True, "멤버십 미승인 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_create_error_invalid_option(self) -> bool:
        """POST /v1/events/{event_id}/votes - 잘못된 option_id 에러"""
        self.print_test("투표 생성 - 잘못된 option_id 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        if not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        import uuid
        fake_option_id = str(uuid.uuid4())
        
        payload = {
            "option_id": fake_option_id,
            "criterion_ids": self.criterion_ids
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "잘못된 option_id 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_create_error_invalid_criteria(self) -> bool:
        """POST /v1/events/{event_id}/votes - 잘못된 criterion_ids 에러"""
        self.print_test("투표 생성 - 잘못된 criterion_ids 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        if not self.option_ids:
            event_detail = self.get_event_detail()
            self.option_ids = [opt["id"] for opt in event_detail.get("options", [])]
        
        if not self.option_ids:
            self.print_result(False, "옵션이 없습니다")
            return False
        
        import uuid
        fake_criterion_id = str(uuid.uuid4())
        
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": [fake_criterion_id]
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            # 잘못된 criterion_id는 400 ValidationError를 반환
            self.assert_error_response(response, 400, expected_message_contains=["criterion", "Invalid"])
            self.print_result(True, "잘못된 criterion_ids 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_create_error_missing_criteria(self) -> bool:
        """POST /v1/events/{event_id}/votes - 모든 기준 포함 안 함 에러"""
        self.print_test("투표 생성 - 모든 기준 포함 안 함 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 완전히 설정된 이벤트 준비
        self.setup_complete_event(start_event=True)
        
        if not self.option_ids or not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.option_ids = [opt["id"] for opt in event_detail.get("options", [])]
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.option_ids or not self.criterion_ids:
            self.print_result(False, "옵션 또는 기준이 없습니다")
            return False
        
        if len(self.criterion_ids) < 2:
            self.print_result(False, "기준이 2개 이상 필요합니다")
            return False
        
        # 일부 기준만 포함
        payload = {
            "option_id": self.option_ids[0],
            "criterion_ids": self.criterion_ids[:1]  # 첫 번째만 포함
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/votes",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="기준")
            self.print_result(True, "모든 기준 포함 안 함 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_result_error_not_finished(self) -> bool:
        """GET /v1/events/{event_id}/votes/result - FINISHED 아님 에러"""
        self.print_test("투표 결과 조회 - FINISHED 아님 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 이벤트를 IN_PROGRESS 상태로만 설정
        self.setup_complete_event(start_event=True)
        
        # 이벤트 상태 확인
        current_status = self.get_event_status()
        if current_status != "IN_PROGRESS":
            self.print_result(False, f"이벤트가 IN_PROGRESS 상태가 아닙니다. 현재 상태: {current_status}")
            return False
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/votes/result",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="FINISHED")
            self.print_result(True, "FINISHED 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_votes_result_error_not_accepted(self) -> bool:
        """GET /v1/events/{event_id}/votes/result - 멤버십 미승인 에러"""
        self.print_test("투표 결과 조회 - 멤버십 미승인 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 새 이벤트 생성 및 입장만 하고 승인하지 않음 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우, 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.event_id = None
            self.entrance_code = None
            self.setup_test_event()
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 ACCEPTED가 아닌지 확인
        if membership_status == "ACCEPTED":
            self.print_result(False, f"멤버십이 이미 ACCEPTED 상태입니다. 자동 승인 설정이 활성화되어 있을 수 있습니다.")
            return False
        
        # IN_PROGRESS -> FINISHED 경로 사용
        self.start_event()
        self.finish_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/votes/result",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="멤버십")
            self.print_result(True, "멤버십 미승인 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 투표 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["me"] = safe_run("test_votes_me", self.test_votes_me)
        results["create"] = safe_run("test_votes_create", self.test_votes_create)
        results["result"] = safe_run("test_votes_result", self.test_votes_result)
        
        # 에러 케이스
        results["create_error_not_in_progress"] = safe_run("test_votes_create_error_not_in_progress", self.test_votes_create_error_not_in_progress)
        results["create_error_not_accepted"] = safe_run("test_votes_create_error_not_accepted", self.test_votes_create_error_not_accepted)
        results["create_error_invalid_option"] = safe_run("test_votes_create_error_invalid_option", self.test_votes_create_error_invalid_option)
        results["create_error_invalid_criteria"] = safe_run("test_votes_create_error_invalid_criteria", self.test_votes_create_error_invalid_criteria)
        results["create_error_missing_criteria"] = safe_run("test_votes_create_error_missing_criteria", self.test_votes_create_error_missing_criteria)
        results["result_error_not_finished"] = safe_run("test_votes_result_error_not_finished", self.test_votes_result_error_not_finished)
        results["result_error_not_accepted"] = safe_run("test_votes_result_error_not_accepted", self.test_votes_result_error_not_accepted)
        
        return results
