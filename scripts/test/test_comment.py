"""
코멘트 API 테스트

테스트 항목:
- GET /v1/events/{event_id}/criteria/{criterion_id}/comments/count - 코멘트 수 조회
- GET /v1/events/{event_id}/criteria/{criterion_id}/comments - 코멘트 목록 조회
- POST /v1/events/{event_id}/criteria/{criterion_id}/comments - 코멘트 생성
- PATCH /v1/events/{event_id}/comments/{comment_id} - 코멘트 수정
- DELETE /v1/events/{event_id}/comments/{comment_id} - 코멘트 삭제
"""

import requests
from scripts.test.base import BaseAPITester


class CommentAPITester(BaseAPITester):
    """코멘트 API 테스트 클래스"""
    
    def test_comments_count(self) -> bool:
        """GET /v1/events/{event_id}/criteria/{criterion_id}/comments/count - 코멘트 수 조회"""
        self.print_test("코멘트 수 조회")
        
        # 멤버십 승인 후 이벤트 상세 조회 가능 (이벤트 시작은 선택사항)
        self.setup_complete_event(start_event=False)
        
        # 기준 ID가 없으면 이벤트 설정에서 가져오기 (관리자용)
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments/count",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(response, 200, required_fields=["count"])
            
            assert isinstance(data["count"], int), "count는 정수여야 합니다"
            assert data["count"] >= 0, "count는 0 이상이어야 합니다"
            
            self.print_result(True, f"코멘트 수 조회 성공: {data['count']}개")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_list(self) -> bool:
        """GET /v1/events/{event_id}/criteria/{criterion_id}/comments - 코멘트 목록 조회"""
        self.print_test("코멘트 목록 조회")
        
        self.setup_complete_event()
        
        if not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(response, 200)
            
            assert isinstance(data, list), "응답은 리스트여야 합니다"
            
            # 각 코멘트 검증
            for comment in data:
                assert "id" in comment, "코멘트에 id가 있어야 합니다"
                assert "content" in comment, "코멘트에 content가 있어야 합니다"
                assert "created_at" in comment, "코멘트에 created_at이 있어야 합니다"
                assert "created_by" in comment, "코멘트에 created_by가 있어야 합니다"
            
            self.print_result(True, f"코멘트 목록 조회 성공: {len(data)}개")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_create(self) -> bool:
        """POST /v1/events/{event_id}/criteria/{criterion_id}/comments - 코멘트 생성"""
        self.print_test("코멘트 생성")
        
        self.setup_complete_event()
        
        if not self.criterion_ids:
            event_detail = self.get_event_detail()
            self.criterion_ids = [c["id"] for c in event_detail.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        payload = {
            "content": "테스트 코멘트 내용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["id", "content", "created_at", "created_by"]
            )
            
            assert data["content"] == payload["content"], "코멘트 내용이 일치해야 합니다"
            assert data["criterion_id"] == self.criterion_ids[0], "기준 ID가 일치해야 합니다"
            
            self.comment_id = str(data["id"])
            
            self.print_result(True, f"코멘트 생성 성공: {self.comment_id}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_update(self) -> bool:
        """PATCH /v1/events/{event_id}/comments/{comment_id} - 코멘트 수정"""
        self.print_test("코멘트 수정")
        
        # 코멘트가 없으면 생성
        if not self.comment_id:
            self.test_comments_create()
        
        if not self.comment_id:
            self.print_result(False, "코멘트 ID가 없습니다")
            return False
        
        payload = {
            "content": "수정된 코멘트 내용"
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/comments/{self.comment_id}",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "content", "updated_at"]
            )
            
            assert data["content"] == payload["content"], "코멘트 내용이 수정되어야 합니다"
            assert data["updated_at"] is not None, "updated_at이 있어야 합니다"
            
            self.print_result(True, f"코멘트 수정 성공: {self.comment_id}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_delete(self) -> bool:
        """DELETE /v1/events/{event_id}/comments/{comment_id} - 코멘트 삭제"""
        self.print_test("코멘트 삭제")
        
        # 코멘트가 없으면 생성
        if not self.comment_id:
            self.test_comments_create()
        
        if not self.comment_id:
            self.print_result(False, "코멘트 ID가 없습니다")
            return False
        
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/comments/{self.comment_id}",
            headers=self.user_headers
        )
        
        try:
            # 204 No Content 응답
            if response.status_code == 204:
                self.print_result(True, f"코멘트 삭제 성공: {self.comment_id}")
                self.comment_id = None  # 삭제되었으므로 초기화
                return True
            else:
                self.assert_response(response, 204)
                return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    # 에러 케이스 테스트
    def test_comments_create_error_not_accepted(self) -> bool:
        """POST /v1/events/{event_id}/criteria/{criterion_id}/comments - 멤버십 미승인 에러"""
        self.print_test("코멘트 생성 - 멤버십 미승인 에러")
        
        # 이벤트 ID 초기화하여 새 이벤트 생성 보장
        self.event_id = None
        self.entrance_code = None
        self.criterion_ids = None
        
        # 새 이벤트 생성 (독립적인 테스트를 위해)
        self.setup_test_event()
        # 입장만 하고 승인하지 않음
        self.join_event()
        
        # 멤버십 상태 확인
        membership_status = self.get_user_membership_status()
        if membership_status == "ACCEPTED":
            # 이미 승인된 경우 (자동 승인 등), 이벤트를 새로 생성하여 PENDING 상태로 만들기
            self.event_id = None
            self.entrance_code = None
            self.criterion_ids = None
            self.setup_test_event()
            self.join_event()
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 ACCEPTED가 아닌지 확인
        if membership_status == "ACCEPTED":
            self.print_result(False, f"멤버십이 이미 ACCEPTED 상태입니다. 자동 승인 설정이 활성화되어 있을 수 있습니다.")
            return False
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        payload = {
            "content": "테스트 코멘트 내용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="멤버십")
            self.print_result(True, "멤버십 미승인 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_update_error_not_owner(self) -> bool:
        """PATCH /v1/events/{event_id}/comments/{comment_id} - 본인 코멘트 아님 에러"""
        self.print_test("코멘트 수정 - 본인 코멘트 아님 에러")
        
        # admin으로 코멘트 생성
        self.setup_complete_event(start_event=False)
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        # admin으로 코멘트 생성
        payload = {
            "content": "관리자 코멘트"
        }
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments",
            headers=self.admin_headers,
            json=payload
        )
        data = self.assert_response(response, 201)
        comment_id = data["id"]
        
        # user로 수정 시도
        payload2 = {
            "content": "수정된 코멘트"
        }
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/comments/{comment_id}",
            headers=self.user_headers,
            json=payload2
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="본인")
            self.print_result(True, "본인 코멘트 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_delete_error_not_owner(self) -> bool:
        """DELETE /v1/events/{event_id}/comments/{comment_id} - 본인 코멘트 아님 에러"""
        self.print_test("코멘트 삭제 - 본인 코멘트 아님 에러")
        
        # admin으로 코멘트 생성
        self.setup_complete_event(start_event=False)
        
        if not self.criterion_ids:
            event_setting = self.get_event_setting()
            self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        
        if not self.criterion_ids:
            self.print_result(False, "기준이 없습니다")
            return False
        
        # admin으로 코멘트 생성
        payload = {
            "content": "관리자 코멘트"
        }
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{self.criterion_ids[0]}/comments",
            headers=self.admin_headers,
            json=payload
        )
        data = self.assert_response(response, 201)
        comment_id = data["id"]
        
        # user로 삭제 시도
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/comments/{comment_id}",
            headers=self.user_headers
        )
        
        try:
            self.assert_error_response(response, 403, expected_message_contains="본인")
            self.print_result(True, "본인 코멘트 아님 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_comments_update_error_nonexistent(self) -> bool:
        """PATCH /v1/events/{event_id}/comments/{comment_id} - 코멘트 없음 에러"""
        self.print_test("코멘트 수정 - 코멘트 없음 에러")
        
        # 이벤트 생성
        self.setup_complete_event(start_event=False)
        
        import uuid
        fake_comment_id = str(uuid.uuid4())
        
        payload = {
            "content": "수정된 코멘트"
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/comments/{fake_comment_id}",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "코멘트 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 코멘트 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["count"] = safe_run("test_comments_count", self.test_comments_count)
        results["list"] = safe_run("test_comments_list", self.test_comments_list)
        results["create"] = safe_run("test_comments_create", self.test_comments_create)
        results["update"] = safe_run("test_comments_update", self.test_comments_update)
        results["delete"] = safe_run("test_comments_delete", self.test_comments_delete)
        
        # 에러 케이스
        results["create_error_not_accepted"] = safe_run("test_comments_create_error_not_accepted", self.test_comments_create_error_not_accepted)
        results["update_error_not_owner"] = safe_run("test_comments_update_error_not_owner", self.test_comments_update_error_not_owner)
        results["delete_error_not_owner"] = safe_run("test_comments_delete_error_not_owner", self.test_comments_delete_error_not_owner)
        results["update_error_nonexistent"] = safe_run("test_comments_update_error_nonexistent", self.test_comments_update_error_nonexistent)
        
        return results
