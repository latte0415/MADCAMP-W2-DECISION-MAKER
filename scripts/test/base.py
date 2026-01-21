"""
공통 베이스 클래스 및 헬퍼 함수

모든 테스트 클래스는 BaseAPITester를 상속받아 사용합니다.
"""

import json
import random
import string
import uuid
from typing import Dict, Any, Optional, List, Union
import requests


class BaseAPITester:
    """모든 API 테스트의 베이스 클래스"""
    
    # 클래스 변수: 인증 정보 출력 여부 (처음에만 출력)
    _auth_info_printed = False
    
    # 클래스 변수: 성공한 테스트 출력 억제 여부 (전체 실행 시 True)
    _suppress_success_output = False
    
    def __init__(self, base_url: str, admin_token: Optional[str] = None, user_token: Optional[str] = None,
                 admin_email: Optional[str] = None, admin_password: Optional[str] = None,
                 user_email: Optional[str] = None, user_password: Optional[str] = None,
                 print_auth_info: bool = True):
        self.base_url = base_url.rstrip('/')
        
        # 토큰이 제공되면 사용, 없으면 ID/PW로 로그인
        # 빈 문자열도 None으로 처리
        admin_token_clean = admin_token.strip() if admin_token and admin_token.strip() else None
        user_token_clean = user_token.strip() if user_token and user_token.strip() else None
        
        # 디버깅: 인증 정보 확인 (처음에만 출력)
        if print_auth_info and not BaseAPITester._auth_info_printed:
            print(f"\n[인증 정보 확인]")
            print(f"  Admin Token: {'설정됨 (' + str(len(admin_token_clean)) + '자)' if admin_token_clean else '없음'}")
            if admin_token_clean:
                print(f"  Admin Token Preview: {admin_token_clean[:30]}...")
            print(f"  Admin Email: {admin_email or '없음'}")
            print(f"  User Token: {'설정됨 (' + str(len(user_token_clean)) + '자)' if user_token_clean else '없음'}")
            if user_token_clean:
                print(f"  User Token Preview: {user_token_clean[:30]}...")
            print(f"  User Email: {user_email or '없음'}")
        
        if admin_token_clean:
            admin_token_final = admin_token_clean
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] Admin 토큰 사용 (길이: {len(admin_token_final)})")
        elif admin_email and admin_password:
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] Admin 로그인 시도: {admin_email}")
            admin_token_final = self._login(admin_email, admin_password)
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] Admin 로그인 성공 (토큰 길이: {len(admin_token_final)})")
        else:
            raise ValueError("admin_token 또는 (admin_email, admin_password)가 필요합니다.")
        
        if user_token_clean:
            user_token_final = user_token_clean
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] User 토큰 사용 (길이: {len(user_token_final)})")
        elif user_email and user_password:
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] User 로그인 시도: {user_email}")
            user_token_final = self._login(user_email, user_password)
            if print_auth_info and not BaseAPITester._auth_info_printed:
                print(f"[인증] User 로그인 성공 (토큰 길이: {len(user_token_final)})")
        else:
            raise ValueError("user_token 또는 (user_email, user_password)가 필요합니다.")
        
        # 토큰 검증 (최소 길이 체크)
        if len(admin_token_final) < 10:
            print(f"[경고] Admin 토큰이 너무 짧습니다: {admin_token_final[:20]}...")
        if len(user_token_final) < 10:
            print(f"[경고] User 토큰이 너무 짧습니다: {user_token_final[:20]}...")
        
        self.admin_headers = {
            "Authorization": f"Bearer {admin_token_final}",
            "Content-Type": "application/json"
        }
        self.user_headers = {
            "Authorization": f"Bearer {user_token_final}",
            "Content-Type": "application/json"
        }
        
        if print_auth_info and not BaseAPITester._auth_info_printed:
            print(f"[인증] 헤더 설정 완료")
            print(f"  Admin Authorization: Bearer {admin_token_final[:30]}...")
            print(f"  User Authorization: Bearer {user_token_final[:30]}...")
            BaseAPITester._auth_info_printed = True
        
        # 이메일/비밀번호 저장 (다른 인스턴스에 전달용)
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.user_email = user_email
        self.user_password = user_password
        
        # 테스트 상태 관리
        self.event_id: Optional[str] = None
        self.entrance_code: Optional[str] = None
        self.event_status: Optional[str] = None  # 이벤트 상태 캐시
        self.option_ids: List[str] = []
        self.criterion_ids: List[str] = []
        self.assumption_ids: List[str] = []
        self.proposal_ids: Dict[str, str] = {}  # category -> proposal_id
        self.membership_id: Optional[str] = None
        self.comment_id: Optional[str] = None
        
        # 테스트 데이터 추적 (cleanup용)
        self.created_event_ids: List[str] = []  # 생성한 이벤트 ID 목록
    
    def print_test(self, test_name: str):
        """테스트 시작 출력"""
        # 성공 출력 억제 모드에서는 출력하지 않음 (실패한 경우에만 나중에 출력)
        if BaseAPITester._suppress_success_output:
            return
        print(f"\n테스트: {test_name}")
    
    def print_result(self, success: bool, message: str = ""):
        """테스트 결과 출력"""
        # 성공 출력 억제 모드이고 성공한 경우 출력하지 않음
        if BaseAPITester._suppress_success_output and success:
            return
        
        status = "✓" if success else "✗"
        print(f"{status} {message}")
    
    def _login(self, email: str, password: str) -> str:
        """
        로그인하여 토큰 획득
        
        Args:
            email: 이메일
            password: 비밀번호
        
        Returns:
            access_token
        
        Raises:
            Exception: 로그인 실패 시
        """
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            raise Exception(f"로그인 실패 ({response.status_code}): {error_text}")
        
        data = response.json()
        access_token = data.get("access_token")
        
        if not access_token:
            raise Exception("로그인 응답에 access_token이 없습니다")
        
        return access_token
    
    def generate_idempotency_key(self) -> str:
        """Idempotency 키 생성"""
        return str(uuid.uuid4())
    
    def generate_entrance_code(self) -> str:
        """랜덤 입장 코드 생성 (6자리 대문자/숫자)"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))
    
    def assert_response(
        self,
        response: requests.Response,
        expected_status: int,
        required_fields: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        응답 검증 헬퍼
        
        Args:
            response: requests 응답 객체
            expected_status: 예상 HTTP 상태 코드
            required_fields: 응답에 포함되어야 하는 필드 목록
            error_message: 커스텀 에러 메시지
        
        Returns:
            응답 JSON 데이터
        
        Raises:
            AssertionError: 검증 실패 시
        """
        if response.status_code != expected_status:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            
            msg = error_message or f"예상 상태 코드 {expected_status}, 실제 {response.status_code}"
            raise AssertionError(f"{msg}\n{error_text[:500]}")  # 로그 간소화: 요청 정보 제거, 응답만 간단히
        
        try:
            data = response.json()
        except:
            if expected_status == 204:  # No Content
                return {}
            raise AssertionError(f"응답이 JSON 형식이 아닙니다: {response.text}")
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise AssertionError(f"필수 필드가 누락되었습니다: {missing_fields}")
        
        return data
    
    def assert_error_response(
        self,
        response: requests.Response,
        expected_status: int,
        expected_error_type: Optional[Union[str, List[str]]] = None,
        expected_message_contains: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        에러 응답 검증 헬퍼
        
        Args:
            response: requests 응답 객체
            expected_status: 예상 HTTP 상태 코드 (400, 401, 403, 404, 409 등)
            expected_error_type: 예상 에러 타입 (예: "ValidationError", "ForbiddenError")
            expected_message_contains: 에러 메시지에 포함되어야 하는 문자열
        
        Returns:
            응답 JSON 데이터
        
        Raises:
            AssertionError: 검증 실패 시
        """
        # 상태 코드 검증
        if response.status_code != expected_status:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json, indent=2, ensure_ascii=False)
            except:
                pass
            
            raise AssertionError(
                f"예상 에러 상태 코드 {expected_status}, 실제 {response.status_code}\n"
                f"{error_text[:500]}"  # 로그 간소화: 요청 정보 제거
            )
        
        # JSON 파싱
        try:
            data = response.json()
        except:
            raise AssertionError(f"응답이 유효한 JSON이 아닙니다: {response.text[:200]}")
        
        # 에러 타입 검증 (detail 필드가 있는 경우)
        if expected_error_type:
            # FastAPI 에러 응답 형식: {"detail": "..."} 또는 {"error": "...", "message": "..."}
            error_detail = data.get("detail") or data.get("error") or data.get("message", "")
            if expected_error_type.lower() not in str(error_detail).lower():
                # error 필드도 확인
                if "error" in data:
                    error_value = str(data.get("error", "")).lower()
                    if expected_error_type.lower() not in error_value:
                        raise AssertionError(
                            f"예상 에러 타입 '{expected_error_type}'이 응답에 없습니다. "
                            f"응답: {json.dumps(data, indent=2, ensure_ascii=False)}"
                        )
        
        # 에러 메시지 포함 여부 검증
        if expected_message_contains:
            error_text = json.dumps(data, ensure_ascii=False)
            error_text_lower = error_text.lower()
            
            # 리스트인 경우 처리
            if isinstance(expected_message_contains, list):
                expected_keywords = [str(kw).lower() for kw in expected_message_contains]
            else:
                expected_keywords = [str(expected_message_contains).lower()]
            
            # 영어/한글 키워드 매핑
            keyword_mapping = {
                "관리자": ["admin", "administrator", "관리자"],
                "멤버십": ["membership", "멤버십"],
                "인원": ["limit", "member", "인원", "참가"],
                "pending": ["pending", "대기"],
                "in_progress": ["in_progress", "진행"],
                "finished": ["finished", "종료"],
                "not_started": ["not_started", "시작"],
                "기준": ["criteria", "기준"],
                "투표": ["vote", "투표"],
                "본인": ["creator", "본인", "own"],
                "입장 코드": ["entrance_code", "entrance code", "duplicate", "입장 코드", "entrance"],
                "상태": ["status", "transition", "상태", "state"]
            }
            
            # 각 키워드에 대해 확인
            found = False
            for expected_lower in expected_keywords:
                # 직접 매칭 확인
                if expected_lower in error_text_lower:
                    found = True
                    break
                
                # 키워드 매핑 확인
                if expected_lower in keyword_mapping:
                    for keyword in keyword_mapping[expected_lower]:
                        if keyword.lower() in error_text_lower:
                            found = True
                            break
                
                if found:
                    break
            
            if not found:
                raise AssertionError(
                    f"에러 메시지에 '{expected_message_contains}'가 포함되어 있지 않습니다.\n"
                    f"응답: {error_text[:300]}"  # 로그 간소화
                )
        
        return data
    
    def get_event_status(self) -> Optional[str]:
        """이벤트 현재 상태 조회"""
        if not self.event_id:
            return None
        
        # 캐시된 상태가 있으면 반환
        if self.event_status:
            return self.event_status
        
        try:
            # overview API 사용 (user도 접근 가능)
            response = requests.get(
                f"{self.base_url}/v1/events/{self.event_id}/overview",
                headers=self.user_headers
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("event", {}).get("event_status")
                self.event_status = status  # 캐시
                return status
        except:
            pass
        return None
    
    def get_event_setting(self) -> Dict[str, Any]:
        """이벤트 설정 조회 (관리자용)"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/setting",
            headers=self.admin_headers
        )
        
        return self.assert_response(response, 200)
    
    def setup_test_event(self, auto_approve: bool = False) -> str:
        """
        테스트용 이벤트 생성 및 설정
        
        Args:
            auto_approve: 멤버십 자동 승인 여부
        
        Returns:
            생성된 이벤트 ID
        """
        if self.event_id:
            return self.event_id
        
        # 입장 코드 생성
        entrance_code = self.generate_entrance_code()
        
        payload = {
            "decision_subject": "API 통합 테스트용 이벤트",
            "entrance_code": entrance_code,
            "max_membership": 10,
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "conclusion_is_auto_approved_by_votes": False,
            "membership_is_auto_approved": auto_approve,
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
        
        # 디버깅: 요청 헤더 확인
        print(f"[디버깅] 이벤트 생성 요청")
        print(f"  URL: {self.base_url}/v1/events")
        print(f"  Authorization: {self.admin_headers.get('Authorization', '없음')[:50]}...")
        
        response = requests.post(
            f"{self.base_url}/v1/events",
            headers=self.admin_headers,
            json=payload
        )
        
        # 디버깅: 응답 확인
        if response.status_code != 201:
            print(f"[디버깅] 응답 상태 코드: {response.status_code}")
            print(f"[디버깅] 응답 본문: {response.text[:200]}")
        
        data = self.assert_response(response, 201, ["id"])
        self.event_id = str(data["id"])
        self.entrance_code = entrance_code
        self.event_status = data.get("event_status", "NOT_STARTED")  # 상태 저장
        
        # 생성한 이벤트 ID 추적
        if self.event_id not in self.created_event_ids:
            self.created_event_ids.append(self.event_id)
        
        # 옵션, 기준 ID 저장 (관리자용 setting API 사용)
        event_setting = self.get_event_setting()
        self.option_ids = [opt["id"] for opt in event_setting.get("options", [])]
        self.criterion_ids = [c["id"] for c in event_setting.get("criteria", [])]
        self.assumption_ids = [a["id"] for a in event_setting.get("assumptions", [])]
        
        # 로그 간소화: 이벤트 생성 완료 메시지 제거
        return self.event_id
    
    def join_event(self) -> None:
        """user가 이벤트에 입장"""
        if not self.entrance_code:
            raise Exception("입장 코드가 없습니다. 먼저 이벤트를 생성하세요.")
        
        response = requests.post(
            f"{self.base_url}/v1/events/entry",
            headers=self.user_headers,
            json={"entrance_code": self.entrance_code}
        )
        
        if response.status_code == 201:
            pass  # 로그 간소화
        elif response.status_code == 409:
            # 이미 멤버십이 있는 경우 - 로그 간소화
            pass
        else:
            self.assert_response(response, 201)
    
    def get_user_membership_status(self) -> Optional[str]:
        """현재 user의 멤버십 상태 조회"""
        if not self.event_id:
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/events/{self.event_id}/overview",
                headers=self.user_headers
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("membership_status")
        except:
            pass
        return None
    
    def approve_user_membership(self) -> None:
        """user의 멤버십 승인 (이미 ACCEPTED면 스킵)"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        # 현재 멤버십 상태 확인
        current_status = self.get_user_membership_status()
        if current_status == "ACCEPTED":
            return  # 로그 간소화
        
        # 멤버십 목록 조회
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}/memberships",
            headers=self.admin_headers
        )
        
        data = self.assert_response(response, 200)
        memberships = data if isinstance(data, list) else []
        
        # PENDING 상태이고 admin이 아닌 멤버십 찾기
        pending_membership = None
        for m in memberships:
            if m.get('status') == 'PENDING' and not m.get('is_admin'):
                pending_membership = m
                break
        
        if not pending_membership:
            return  # 로그 간소화
        
        membership_id = pending_membership['membership_id']
        approve_headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/memberships/{membership_id}/approve",
            headers=approve_headers
        )
        
        # 409 에러는 멤버십 한계 도달이므로 스킵 (이미 다른 테스트에서 사용 중일 수 있음)
        if response.status_code == 409:
            # 멤버십 상태 재확인
            current_status = self.get_user_membership_status()
            if current_status == "ACCEPTED":
                return  # 로그 간소화
            else:
                # 한계 도달했지만 ACCEPTED가 아닌 경우는 에러로 처리하지 않음 (테스트 간 상태 공유 문제)
                return
        
        self.assert_response(response, 200)
        self.membership_id = membership_id
    
    def start_event(self) -> None:
        """이벤트 상태를 IN_PROGRESS로 변경 (이미 IN_PROGRESS면 스킵)"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        # 현재 상태 확인
        current_status = self.get_event_status()
        if current_status == "IN_PROGRESS":
            return  # 로그 간소화
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/status",
            headers=headers,
            json={"status": "IN_PROGRESS"}
        )
        
        data = self.assert_response(response, 200)
        self.event_status = data.get("status", "IN_PROGRESS")  # 상태 업데이트
    
    def pause_event(self) -> None:
        """이벤트 상태를 PAUSED로 변경 (이미 PAUSED면 스킵)"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        # 현재 상태 확인
        current_status = self.get_event_status()
        if current_status == "PAUSED":
            return  # 로그 간소화
        
        # IN_PROGRESS 상태에서만 PAUSED로 변경 가능
        if current_status != "IN_PROGRESS":
            raise Exception(f"이벤트를 일시정지할 수 없습니다. 현재 상태: {current_status}, 필요 상태: IN_PROGRESS")
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/status",
            headers=headers,
            json={"status": "PAUSED"}
        )
        
        data = self.assert_response(response, 200)
        self.event_status = data.get("status", "PAUSED")  # 상태 업데이트
    
    def finish_event(self) -> None:
        """이벤트 상태를 FINISHED로 변경 (올바른 전이 경로: IN_PROGRESS -> FINISHED)"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        # 현재 상태 확인
        current_status = self.get_event_status()
        if current_status == "FINISHED":
            return  # 로그 간소화
        
        # IN_PROGRESS 또는 PAUSED 상태에서만 FINISHED로 변경 가능
        if current_status not in ["IN_PROGRESS", "PAUSED"]:
            # NOT_STARTED인 경우 먼저 시작
            if current_status == "NOT_STARTED":
                self.start_event()
            else:
                raise Exception(f"FINISHED로 변경할 수 없는 상태입니다: {current_status}")
        
        headers = {
            **self.admin_headers,
            "Idempotency-Key": self.generate_idempotency_key()
        }
        
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/status",
            headers=headers,
            json={"status": "FINISHED"}
        )
        
        data = self.assert_response(response, 200)
        self.event_status = data.get("status", "FINISHED")  # 상태 업데이트
        print("[이벤트 종료 완료] 상태: FINISHED")
    
    def get_event_detail(self) -> Dict[str, Any]:
        """이벤트 상세 조회"""
        if not self.event_id:
            raise Exception("이벤트 ID가 없습니다.")
        
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}",
            headers=self.user_headers
        )
        
        return self.assert_response(response, 200)
    
    def setup_complete_event(self, start_event: bool = True) -> str:
        """
        완전히 설정된 이벤트 생성 (생성 → 입장 → 승인 → [시작])
        각 단계는 이미 완료된 경우 스킵됩니다.
        
        Args:
            start_event: 이벤트를 IN_PROGRESS 상태로 시작할지 여부 (기본값: True)
        
        Returns:
            이벤트 ID
        """
        # 이벤트 생성
        self.setup_test_event()
        
        # 멤버십 상태 확인 후 입장
        membership_status = self.get_user_membership_status()
        if membership_status is None:
            self.join_event()
            membership_status = "PENDING"  # 입장 후 PENDING 상태
        
        # 멤버십 승인 (PENDING인 경우만)
        if membership_status == "PENDING":
            self.approve_user_membership()
            # 승인 후 상태 재확인
            membership_status = self.get_user_membership_status()
        
        # 멤버십이 승인되지 않았으면 에러
        if membership_status != "ACCEPTED":
            raise Exception(f"멤버십이 승인되지 않았습니다. 현재 상태: {membership_status}")
        
        # 이벤트 시작 (start_event가 True이고 NOT_STARTED인 경우만)
        if start_event:
            current_status = self.get_event_status()
            if current_status == "NOT_STARTED":
                self.start_event()
        
        return self.event_id
    
    def cleanup(self) -> None:
        """
        테스트에서 생성한 데이터 정리 (이벤트 삭제)
        개발용 API를 사용하여 생성한 모든 이벤트를 삭제합니다.
        """
        if not self.created_event_ids:
            return
        
        print(f"\n[데이터 정리 시작] 생성한 이벤트 {len(self.created_event_ids)}개 삭제 중...")
        
        deleted_count = 0
        failed_count = 0
        
        for event_id in self.created_event_ids:
            try:
                response = requests.delete(
                    f"{self.base_url}/dev/events/{event_id}",
                    headers=self.admin_headers
                )
                
                if response.status_code == 204:
                    deleted_count += 1
                elif response.status_code == 404:
                    # 이미 삭제된 경우
                    deleted_count += 1
                else:
                    failed_count += 1
                    print(f"  [경고] 이벤트 삭제 실패: {event_id} (상태 코드: {response.status_code})")
            except Exception as e:
                failed_count += 1
                print(f"  [경고] 이벤트 삭제 중 오류: {event_id} - {str(e)}")
        
        print(f"[데이터 정리 완료] 삭제 성공: {deleted_count}개, 실패: {failed_count}개")
        
        # 추적 목록 초기화
        self.created_event_ids = []
        self.event_id = None
        self.entrance_code = None
        self.event_status = None
        self.option_ids = []
        self.criterion_ids = []
        self.assumption_ids = []
        self.proposal_ids = {}
        self.membership_id = None
        self.comment_id = None
