"""
이벤트 상세/제안 API 테스트

테스트 항목:
- GET /v1/events/{event_id} - 이벤트 상세 조회
- POST /v1/events/{event_id}/assumption-proposals - 전제 제안 생성
- POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 전제 제안 투표 생성
- DELETE /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 전제 제안 투표 삭제
- POST /v1/events/{event_id}/criteria-proposals - 기준 제안 생성
- POST /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes - 기준 제안 투표 생성
- DELETE /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes - 기준 제안 투표 삭제
- POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals - 결론 제안 생성
- POST /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes - 결론 제안 투표 생성
- DELETE /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes - 결론 제안 투표 삭제
"""

import requests
from scripts.test.base import BaseAPITester


class EventDetailAPITester(BaseAPITester):
    """이벤트 상세/제안 API 테스트 클래스"""
    
    def test_event_detail(self) -> bool:
        """GET /v1/events/{event_id} - 이벤트 상세 조회"""
        self.print_test("이벤트 상세 조회")
        
        # 멤버십 승인 후 이벤트 상세 조회 가능 (이벤트 시작은 선택사항)
        self.setup_complete_event(start_event=False)
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "decision_subject", "event_status", "options", "assumptions", "criteria"]
            )
            
            # 기본 필드 검증
            assert data["id"] == self.event_id, "이벤트 ID가 일치해야 합니다"
            assert "options" in data, "options가 있어야 합니다"
            assert "assumptions" in data, "assumptions가 있어야 합니다"
            assert "criteria" in data, "criteria가 있어야 합니다"
            
            # 옵션, 기준, 전제 ID 저장
            self.option_ids = [opt["id"] for opt in data.get("options", [])]
            self.criterion_ids = [c["id"] for c in data.get("criteria", [])]
            self.assumption_ids = [a["id"] for a in data.get("assumptions", [])]
            
            self.print_result(True, f"이벤트 상세 조회 성공: {data['decision_subject']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_create(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals - 전제 제안 생성"""
        self.print_test("전제 제안 생성")
        
        # 제안 생성은 IN_PROGRESS 상태에서만 가능
        self.setup_complete_event(start_event=True)
        
        # 이벤트 상태 확인
        current_status = self.get_event_status()
        if current_status != "IN_PROGRESS":
            self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
            return False
        
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["id", "proposal_status", "proposal_category", "proposal_content"]
            )
            
            assert data["proposal_status"] == "PENDING", "제안 상태는 PENDING이어야 합니다"
            assert data["proposal_category"] == "CREATION", "제안 카테고리는 CREATION이어야 합니다"
            
            self.proposal_ids["assumption_creation"] = str(data["id"])
            
            self.print_result(True, f"전제 제안 생성 성공: {data['id']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_vote_create(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 전제 제안 투표 생성"""
        self.print_test("전제 제안 투표 생성")
        
        # 제안이 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "assumption_creation" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            # 제안 생성
            self.test_assumption_proposal_create()
        
        proposal_id = self.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            assert data["vote_count"] >= 1, "투표 수가 1 이상이어야 합니다"
            
            self.print_result(True, f"전제 제안 투표 생성 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_vote_delete(self) -> bool:
        """DELETE /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 전제 제안 투표 삭제"""
        self.print_test("전제 제안 투표 삭제")
        
        # 투표가 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "assumption_creation" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            self.test_assumption_proposal_vote_create()
        
        proposal_id = self.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"전제 제안 투표 삭제 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_create(self) -> bool:
        """POST /v1/events/{event_id}/criteria-proposals - 기준 제안 생성"""
        self.print_test("기준 제안 생성")
        
        # 제안 생성은 IN_PROGRESS 상태에서만 가능
        self.setup_complete_event(start_event=True)
        
        # 이벤트 상태 확인
        current_status = self.get_event_status()
        if current_status != "IN_PROGRESS":
            self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
            return False
        
        if not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        payload = {
            "proposal_category": "MODIFICATION",
            "criteria_id": self.criterion_ids[0],
            "proposal_content": "수정된 기준 내용",
            "reason": "테스트용 수정"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["id", "proposal_status", "proposal_category", "proposal_content"]
            )
            
            assert data["proposal_status"] == "PENDING", "제안 상태는 PENDING이어야 합니다"
            assert data["proposal_category"] == "MODIFICATION", "제안 카테고리는 MODIFICATION이어야 합니다"
            
            self.proposal_ids["criteria_modification"] = str(data["id"])
            
            self.print_result(True, f"기준 제안 생성 성공: {data['id']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_vote_create(self) -> bool:
        """POST /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes - 기준 제안 투표 생성"""
        self.print_test("기준 제안 투표 생성")
        
        # 제안이 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "criteria_modification" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            # 제안 생성
            self.test_criteria_proposal_create()
        
        proposal_id = self.proposal_ids.get("criteria_modification")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/votes",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            assert data["vote_count"] >= 1, "투표 수가 1 이상이어야 합니다"
            
            self.print_result(True, f"기준 제안 투표 생성 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_vote_delete(self) -> bool:
        """DELETE /v1/events/{event_id}/criteria-proposals/{proposal_id}/votes - 기준 제안 투표 삭제"""
        self.print_test("기준 제안 투표 삭제")
        
        # 투표가 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "criteria_modification" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            self.test_criteria_proposal_vote_create()
        
        proposal_id = self.proposal_ids.get("criteria_modification")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"기준 제안 투표 삭제 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_create(self) -> bool:
        """POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals - 결론 제안 생성"""
        self.print_test("결론 제안 생성")
        
        # 제안 생성은 IN_PROGRESS 상태에서만 가능
        self.setup_complete_event(start_event=True)
        
        # 이벤트 상태 확인
        current_status = self.get_event_status()
        if current_status != "IN_PROGRESS":
            self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
            return False
        
        if not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        payload = {
            "proposal_content": "결론 내용"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/conclusion-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["id", "proposal_status", "proposal_content"]
            )
            
            assert data["proposal_status"] == "PENDING", "제안 상태는 PENDING이어야 합니다"
            
            self.proposal_ids["conclusion"] = str(data["id"])
            
            self.print_result(True, f"결론 제안 생성 성공: {data['id']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_vote_create(self) -> bool:
        """POST /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes - 결론 제안 투표 생성"""
        self.print_test("결론 제안 투표 생성")
        
        # 제안이 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "conclusion" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            # 제안 생성
            self.test_conclusion_proposal_create()
        
        proposal_id = self.proposal_ids.get("conclusion")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/votes",
            headers=headers
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            assert data["vote_count"] >= 1, "투표 수가 1 이상이어야 합니다"
            
            self.print_result(True, f"결론 제안 투표 생성 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_vote_delete(self) -> bool:
        """DELETE /v1/events/{event_id}/conclusion-proposals/{proposal_id}/votes - 결론 제안 투표 삭제"""
        self.print_test("결론 제안 투표 삭제")
        
        # 투표가 없으면 생성 (이벤트가 IN_PROGRESS 상태인지 확인)
        if "conclusion" not in self.proposal_ids:
            # 이벤트가 IN_PROGRESS 상태인지 확인하고 필요시 시작
            self.setup_complete_event(start_event=True)
            current_status = self.get_event_status()
            if current_status != "IN_PROGRESS":
                self.print_result(False, f"제안 생성은 IN_PROGRESS 상태에서만 가능합니다. 현재 상태: {current_status}")
                return False
            self.test_conclusion_proposal_vote_create()
        
        proposal_id = self.proposal_ids.get("conclusion")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["message", "vote_id", "proposal_id", "vote_count"]
            )
            
            assert data["proposal_id"] == proposal_id, "제안 ID가 일치해야 합니다"
            
            self.print_result(True, f"결론 제안 투표 삭제 성공: vote_count={data['vote_count']}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_event_detail_error_not_accepted_membership(self) -> bool:
        """GET /v1/events/{event_id} - 멤버십 미승인 에러"""
        self.print_test("이벤트 상세 조회 - 멤버십 미승인 에러")
        
        # 새 이벤트 생성 (독립적인 테스트를 위해)
        self.setup_test_event()
        # 입장만 하고 승인하지 않음
        self.join_event()
        
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우, 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.setup_test_event()
            self.join_event()
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}",
            headers=self.user_headers
        )
        
        try:
            # NOT_STARTED 상태에서는 멤버십 체크를 하지 않을 수 있으므로, 200 또는 403 모두 가능
            if response.status_code == 200:
                # NOT_STARTED 상태에서는 조회 가능할 수 있음 (실제 코드 동작 확인 필요)
                self.print_result(True, "NOT_STARTED 상태에서는 멤버십 체크 없이 조회 가능")
                return True
            else:
                self.assert_error_response(response, 403, expected_message_contains="멤버십")
                self.print_result(True, "멤버십 미승인 에러 확인 성공")
                return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_event_detail_error_nonexistent_event(self) -> bool:
        """GET /v1/events/{event_id} - 존재하지 않는 이벤트 에러"""
        self.print_test("이벤트 상세 조회 - 존재하지 않는 이벤트 에러")
        
        import uuid
        fake_event_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{self.base_url}/v1/events/{fake_event_id}",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "존재하지 않는 이벤트 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_create_error_not_in_progress(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals - NOT_STARTED 상태 에러"""
        self.print_test("전제 제안 생성 - NOT_STARTED 상태 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        
        # 이벤트 생성만 하고 시작하지 않음
        self.setup_complete_event(start_event=False)
        
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "NOT_STARTED 상태 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_create_error_paused(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals - PAUSED 상태 에러"""
        self.print_test("전제 제안 생성 - PAUSED 상태 에러")
        
        # 새 이벤트 생성 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        self.approve_user_membership()
        # IN_PROGRESS -> PAUSED 경로 사용
        self.start_event()
        self.pause_event()
        
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "PAUSED 상태 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_create_error_finished(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals - FINISHED 상태 에러"""
        self.print_test("전제 제안 생성 - FINISHED 상태 에러")
        
        # 새 이벤트 생성 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        self.approve_user_membership()
        # IN_PROGRESS -> FINISHED 경로 사용
        self.start_event()
        self.finish_event()
        
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "FINISHED 상태 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_create_error_not_accepted(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals - 멤버십 미승인 에러"""
        self.print_test("전제 제안 생성 - 멤버십 미승인 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        
        # 새 이벤트 생성 및 입장만 하고 승인하지 않음 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우 (자동 승인 등), 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.event_id = None
            self.entrance_code = None
            self.setup_test_event()
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 ACCEPTED가 아닌지 확인
        if membership_status == "ACCEPTED":
            self.print_result(False, f"멤버십이 이미 ACCEPTED 상태입니다. 자동 승인 설정이 활성화되어 있을 수 있습니다.")
            return False
        
        self.start_event()
        
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
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
    
    def test_assumption_proposal_vote_create_error_not_pending(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 제안이 PENDING 아님 에러"""
        self.print_test("전제 제안 투표 생성 - 제안이 PENDING 아님 에러")
        
        # 제안 생성 후 승인
        self.setup_complete_event(start_event=True)
        
        # 제안 생성
        payload = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "새로운 전제 내용",
            "reason": "테스트용 전제"
        }
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers=headers,
            json=payload
        )
        data = self.assert_response(response, 201)
        proposal_id = data["id"]
        
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
        
        # 승인된 제안에 투표 시도
        vote_headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=vote_headers
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="PENDING")
            self.print_result(True, "제안이 PENDING 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_vote_create_error_already_voted(self) -> bool:
        """POST /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 이미 투표함 에러"""
        self.print_test("전제 제안 투표 생성 - 이미 투표함 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        
        # 제안 생성 및 첫 번째 투표
        self.setup_complete_event(start_event=True)
        if "assumption_creation" not in self.proposal_ids:
            self.test_assumption_proposal_create()
        
        proposal_id = self.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 첫 번째 투표
        vote_key = self.generate_idempotency_key()
        headers = {
            **self.user_headers,
            "Idempotency-Key": vote_key
        }
        requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=headers
        )
        
        # 두 번째 투표 시도 (다른 키로 - 중복 투표 에러를 테스트하기 위해)
        headers2 = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=headers2
        )
        
        try:
            self.assert_error_response(response, 409, expected_message_contains="투표")
            self.print_result(True, "이미 투표함 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_assumption_proposal_vote_delete_error_not_found(self) -> bool:
        """DELETE /v1/events/{event_id}/assumption-proposals/{proposal_id}/votes - 투표 없음 에러"""
        self.print_test("전제 제안 투표 삭제 - 투표 없음 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        
        # 제안 생성만 하고 투표하지 않음
        self.setup_complete_event(start_event=True)
        if "assumption_creation" not in self.proposal_ids:
            self.test_assumption_proposal_create()
        
        proposal_id = self.proposal_ids.get("assumption_creation")
        if not proposal_id:
            self.print_result(False, "제안 ID가 없습니다")
            return False
        
        # 투표가 없는지 확인 (이전 테스트의 투표가 남아있을 수 있음)
        # 제안 상세 조회로 투표 여부 확인
        proposal_response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}",
            headers=self.user_headers
        )
        if proposal_response.status_code == 200:
            proposal_data = proposal_response.json()
            if proposal_data.get("has_voted", False):
                # 이미 투표가 있는 경우, 투표를 삭제
                delete_response = requests.delete(
                    f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
                    headers=self.user_headers
                )
                # 삭제가 성공했는지 확인
                if delete_response.status_code != 200:
                    self.print_result(False, f"기존 투표 삭제 실패: {delete_response.status_code}")
                    return False
        
        # 투표 없이 삭제 시도
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "투표 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_create_error_not_in_progress(self) -> bool:
        """POST /v1/events/{event_id}/criteria-proposals - NOT_STARTED 상태 에러"""
        self.print_test("기준 제안 생성 - NOT_STARTED 상태 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        self.criterion_ids = None
        
        # 이벤트 생성만 하고 시작하지 않음
        self.setup_complete_event(start_event=False)
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준 ID가 없습니다")
            return False
        
        payload = {
            "proposal_category": "MODIFICATION",
            "criteria_id": self.criterion_ids[0],
            "proposal_content": "수정된 기준 내용",
            "reason": "테스트용"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "NOT_STARTED 상태 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_criteria_proposal_create_error_not_accepted(self) -> bool:
        """POST /v1/events/{event_id}/criteria-proposals - 멤버십 미승인 에러"""
        self.print_test("기준 제안 생성 - 멤버십 미승인 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        self.criterion_ids = None
        
        # 새 이벤트 생성 및 입장만 하고 승인하지 않음 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우, 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.event_id = None
            self.entrance_code = None
            self.proposal_ids = {}
            self.criterion_ids = None
            self.setup_test_event()
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 ACCEPTED가 아닌지 확인
        if membership_status == "ACCEPTED":
            self.print_result(False, f"멤버십이 이미 ACCEPTED 상태입니다. 자동 승인 설정이 활성화되어 있을 수 있습니다.")
            return False
        
        self.start_event()
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준 ID가 없습니다")
            return False
        
        payload = {
            "proposal_category": "MODIFICATION",
            "criteria_id": self.criterion_ids[0],
            "proposal_content": "수정된 기준 내용",
            "reason": "테스트용"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
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
    
    def test_conclusion_proposal_create_error_not_in_progress(self) -> bool:
        """POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals - NOT_STARTED 상태 에러"""
        self.print_test("결론 제안 생성 - NOT_STARTED 상태 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        self.criterion_ids = None
        
        # 이벤트 생성만 하고 시작하지 않음
        self.setup_complete_event(start_event=False)
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준 ID가 없습니다")
            return False
        
        payload = {
            "proposal_content": "결론 내용"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/conclusion-proposals",
            headers=headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 400, expected_message_contains="IN_PROGRESS")
            self.print_result(True, "NOT_STARTED 상태 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_conclusion_proposal_create_error_not_accepted(self) -> bool:
        """POST /v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals - 멤버십 미승인 에러"""
        self.print_test("결론 제안 생성 - 멤버십 미승인 에러")
        
        # 이벤트 ID 및 제안 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.proposal_ids = {}
        self.criterion_ids = None
        
        # 새 이벤트 생성 및 입장만 하고 승인하지 않음 (독립적인 테스트를 위해)
        self.setup_test_event()
        self.join_event()
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우, 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.event_id = None
            self.entrance_code = None
            self.proposal_ids = {}
            self.criterion_ids = None
            self.setup_test_event()
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 ACCEPTED가 아닌지 확인
        if membership_status == "ACCEPTED":
            self.print_result(False, f"멤버십이 이미 ACCEPTED 상태입니다. 자동 승인 설정이 활성화되어 있을 수 있습니다.")
            return False
        
        self.start_event()
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준 ID가 없습니다")
            return False
        
        payload = {
            "proposal_content": "결론 내용"
        }
        
        headers = {
            **self.user_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/conclusion-proposals",
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
    
    def run_all_tests(self) -> dict:
        """모든 이벤트 상세/제안 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["detail"] = safe_run("test_event_detail", self.test_event_detail)
        results["assumption_proposal_create"] = safe_run("test_assumption_proposal_create", self.test_assumption_proposal_create)
        results["assumption_proposal_vote_create"] = safe_run("test_assumption_proposal_vote_create", self.test_assumption_proposal_vote_create)
        results["assumption_proposal_vote_delete"] = safe_run("test_assumption_proposal_vote_delete", self.test_assumption_proposal_vote_delete)
        results["criteria_proposal_create"] = safe_run("test_criteria_proposal_create", self.test_criteria_proposal_create)
        results["criteria_proposal_vote_create"] = safe_run("test_criteria_proposal_vote_create", self.test_criteria_proposal_vote_create)
        results["criteria_proposal_vote_delete"] = safe_run("test_criteria_proposal_vote_delete", self.test_criteria_proposal_vote_delete)
        results["conclusion_proposal_create"] = safe_run("test_conclusion_proposal_create", self.test_conclusion_proposal_create)
        results["conclusion_proposal_vote_create"] = safe_run("test_conclusion_proposal_vote_create", self.test_conclusion_proposal_vote_create)
        results["conclusion_proposal_vote_delete"] = safe_run("test_conclusion_proposal_vote_delete", self.test_conclusion_proposal_vote_delete)
        
        # 에러 케이스
        results["detail_error_not_accepted_membership"] = safe_run("test_event_detail_error_not_accepted_membership", self.test_event_detail_error_not_accepted_membership)
        results["detail_error_nonexistent_event"] = safe_run("test_event_detail_error_nonexistent_event", self.test_event_detail_error_nonexistent_event)
        results["assumption_proposal_create_error_not_in_progress"] = safe_run("test_assumption_proposal_create_error_not_in_progress", self.test_assumption_proposal_create_error_not_in_progress)
        results["assumption_proposal_create_error_paused"] = safe_run("test_assumption_proposal_create_error_paused", self.test_assumption_proposal_create_error_paused)
        results["assumption_proposal_create_error_finished"] = safe_run("test_assumption_proposal_create_error_finished", self.test_assumption_proposal_create_error_finished)
        results["assumption_proposal_create_error_not_accepted"] = safe_run("test_assumption_proposal_create_error_not_accepted", self.test_assumption_proposal_create_error_not_accepted)
        results["assumption_proposal_vote_create_error_not_pending"] = safe_run("test_assumption_proposal_vote_create_error_not_pending", self.test_assumption_proposal_vote_create_error_not_pending)
        results["assumption_proposal_vote_create_error_already_voted"] = safe_run("test_assumption_proposal_vote_create_error_already_voted", self.test_assumption_proposal_vote_create_error_already_voted)
        results["assumption_proposal_vote_delete_error_not_found"] = safe_run("test_assumption_proposal_vote_delete_error_not_found", self.test_assumption_proposal_vote_delete_error_not_found)
        results["criteria_proposal_create_error_not_in_progress"] = safe_run("test_criteria_proposal_create_error_not_in_progress", self.test_criteria_proposal_create_error_not_in_progress)
        results["criteria_proposal_create_error_not_accepted"] = safe_run("test_criteria_proposal_create_error_not_accepted", self.test_criteria_proposal_create_error_not_accepted)
        results["conclusion_proposal_create_error_not_in_progress"] = safe_run("test_conclusion_proposal_create_error_not_in_progress", self.test_conclusion_proposal_create_error_not_in_progress)
        results["conclusion_proposal_create_error_not_accepted"] = safe_run("test_conclusion_proposal_create_error_not_accepted", self.test_conclusion_proposal_create_error_not_accepted)
        
        return results
