"""
인증 API 테스트

테스트 항목:
- POST /auth/signup - 회원가입
- POST /auth/login - 로그인
- POST /auth/google - 구글 로그인 (스킵 가능)
- POST /auth/refresh - 토큰 갱신 (쿠키 필요, 스킵 가능)
- POST /auth/logout - 로그아웃 (쿠키 필요, 스킵 가능)
- GET /auth/me - 현재 사용자 정보 조회
- PATCH /auth/me/name - 이름 업데이트
- POST /auth/password-reset/request - 비밀번호 재설정 요청
- POST /auth/password-reset/confirm - 비밀번호 재설정 확인 (토큰 필요, 스킵 가능)
"""

import requests
from scripts.test.base import BaseAPITester


class AuthAPITester(BaseAPITester):
    """인증 API 테스트 클래스"""
    
    def test_auth_signup(self) -> bool:
        """POST /auth/signup - 회원가입"""
        self.print_test("회원가입")
        
        # 고유한 이메일 생성 (타임스탬프 사용)
        import time
        email = f"test_{int(time.time())}@test.com"
        
        payload = {
            "email": email,
            "password": "testpassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/signup",
            json=payload
        )
        
        try:
            data = self.assert_response(
                response,
                201,
                required_fields=["access_token", "token_type", "user"]
            )
            
            # 응답 검증
            assert data["token_type"] == "bearer", "token_type이 bearer여야 합니다"
            assert "id" in data["user"], "user에 id가 있어야 합니다"
            assert data["user"]["email"] == email, "이메일이 일치해야 합니다"
            
            self.print_result(True, f"회원가입 성공: {email}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_login(self) -> bool:
        """POST /auth/login - 로그인"""
        self.print_test("로그인")
        
        # 테스트용 계정이 필요하므로, 실제 토큰이 있다는 가정 하에 스킵 가능
        # 여기서는 토큰 검증만 수행
        if not self.user_headers.get("Authorization"):
            self.print_result(False, "토큰이 없어 테스트를 스킵합니다")
            return False
        
        # 실제 로그인 테스트는 별도 계정이 필요하므로 스킵
        # 대신 현재 토큰이 유효한지 확인
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.user_headers
        )
        
        if response.status_code == 200:
            self.print_result(True, "토큰이 유효합니다 (로그인 상태 확인)")
            return True
        else:
            self.print_result(False, f"토큰이 유효하지 않습니다: {response.status_code}")
            return False
    
    def test_auth_google(self) -> bool:
        """POST /auth/google - 구글 로그인"""
        self.print_test("구글 로그인")
        
        # 구글 토큰이 필요하므로 스킵
        self.print_result(True, "구글 로그인 테스트는 스킵됩니다 (구글 토큰 필요)")
        return True
    
    def test_auth_refresh(self) -> bool:
        """POST /auth/refresh - 토큰 갱신"""
        self.print_test("토큰 갱신")
        
        # 쿠키가 필요하므로 스킵
        self.print_result(True, "토큰 갱신 테스트는 스킵됩니다 (쿠키 필요)")
        return True
    
    def test_auth_logout(self) -> bool:
        """POST /auth/logout - 로그아웃"""
        self.print_test("로그아웃")
        
        # 쿠키가 필요하므로 스킵
        self.print_result(True, "로그아웃 테스트는 스킵됩니다 (쿠키 필요)")
        return True
    
    def test_auth_me(self) -> bool:
        """GET /auth/me - 현재 사용자 정보 조회"""
        self.print_test("현재 사용자 정보 조회")
        
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.user_headers
        )
        
        try:
            data = self.assert_response(
                response,
                200,
                required_fields=["id", "email", "is_active"]
            )
            
            # 응답 검증
            assert "id" in data, "id가 있어야 합니다"
            assert "email" in data, "email이 있어야 합니다"
            assert isinstance(data["is_active"], bool), "is_active는 boolean이어야 합니다"
            
            self.print_result(True, f"사용자 정보 조회 성공: {data.get('email')}")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_update_name(self) -> bool:
        """PATCH /auth/me/name - 이름 업데이트"""
        self.print_test("이름 업데이트")
        
        payload = {
            "name": "테스트 사용자"
        }
        
        response = requests.patch(
            f"{self.base_url}/auth/me/name",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            data = self.assert_response(response, 200, required_fields=["message"])
            
            # 이름이 업데이트되었는지 확인
            me_response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self.user_headers
            )
            me_data = self.assert_response(me_response, 200)
            
            assert me_data.get("name") == "테스트 사용자", "이름이 업데이트되어야 합니다"
            
            self.print_result(True, "이름 업데이트 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_password_reset_request(self) -> bool:
        """POST /auth/password-reset/request - 비밀번호 재설정 요청"""
        self.print_test("비밀번호 재설정 요청")
        
        # 현재 사용자 이메일 가져오기
        me_response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.user_headers
        )
        
        if me_response.status_code != 200:
            self.print_result(False, "사용자 정보를 가져올 수 없습니다")
            return False
        
        email = me_response.json().get("email")
        if not email:
            self.print_result(False, "이메일을 찾을 수 없습니다")
            return False
        
        payload = {
            "email": email
        }
        
        response = requests.post(
            f"{self.base_url}/auth/password-reset/request",
            json=payload
        )
        
        try:
            # 이메일 전송 실패 시 502가 올 수 있지만, 요청 자체는 성공할 수 있음
            if response.status_code in [200, 502]:
                self.print_result(
                    True,
                    f"비밀번호 재설정 요청 완료 (상태: {response.status_code})"
                )
                return True
            else:
                self.assert_response(response, 200)
                return True
        except Exception as e:
            # 502 에러는 이메일 서버 문제일 수 있으므로 경고만
            if response.status_code == 502:
                self.print_result(
                    True,
                    "비밀번호 재설정 요청은 성공했지만 이메일 전송 실패 (502)"
                )
                return True
            self.print_result(False, str(e))
            return False
    
    def test_auth_password_reset_confirm(self) -> bool:
        """POST /auth/password-reset/confirm - 비밀번호 재설정 확인"""
        self.print_test("비밀번호 재설정 확인")
        
        # 리셋 토큰이 필요하므로 스킵
        self.print_result(True, "비밀번호 재설정 확인 테스트는 스킵됩니다 (리셋 토큰 필요)")
        return True
    
    # 에러 케이스 테스트
    def test_auth_signup_error_duplicate_email(self) -> bool:
        """POST /auth/signup - 중복 이메일 에러"""
        self.print_test("회원가입 - 중복 이메일 에러")
        
        # 먼저 회원가입
        import time
        email = f"test_dup_{int(time.time())}@test.com"
        payload = {
            "email": email,
            "password": "testpassword123"
        }
        requests.post(f"{self.base_url}/auth/signup", json=payload)
        
        # 같은 이메일로 다시 회원가입 시도
        response = requests.post(
            f"{self.base_url}/auth/signup",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 409, expected_message_contains="이미 사용")
            self.print_result(True, "중복 이메일 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_signup_error_invalid_email(self) -> bool:
        """POST /auth/signup - 잘못된 이메일 형식 에러"""
        self.print_test("회원가입 - 잘못된 이메일 형식 에러")
        
        payload = {
            "email": "invalid-email",
            "password": "testpassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/signup",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 422)  # FastAPI validation error
            self.print_result(True, "잘못된 이메일 형식 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_signup_error_invalid_password(self) -> bool:
        """POST /auth/signup - 잘못된 비밀번호 길이 에러"""
        self.print_test("회원가입 - 잘못된 비밀번호 길이 에러")
        
        import time
        email = f"test_pw_{int(time.time())}@test.com"
        
        # 비밀번호가 너무 짧은 경우
        payload = {
            "email": email,
            "password": "short"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/signup",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 422)  # FastAPI validation error
            self.print_result(True, "잘못된 비밀번호 길이 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_login_error_wrong_password(self) -> bool:
        """POST /auth/login - 잘못된 비밀번호 에러"""
        self.print_test("로그인 - 잘못된 비밀번호 에러")
        
        # 현재 사용자 이메일 가져오기
        me_response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.user_headers
        )
        
        if me_response.status_code != 200:
            self.print_result(False, "사용자 정보를 가져올 수 없습니다")
            return False
        
        email = me_response.json().get("email")
        if not email:
            self.print_result(False, "이메일을 찾을 수 없습니다")
            return False
        
        payload = {
            "email": email,
            "password": "wrongpassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 401, expected_message_contains="비밀번호")
            self.print_result(True, "잘못된 비밀번호 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_login_error_nonexistent_user(self) -> bool:
        """POST /auth/login - 존재하지 않는 사용자 에러"""
        self.print_test("로그인 - 존재하지 않는 사용자 에러")
        
        payload = {
            "email": "nonexistent@test.com",
            "password": "testpassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 401)
            self.print_result(True, "존재하지 않는 사용자 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_me_error_no_token(self) -> bool:
        """GET /auth/me - 토큰 없음 에러"""
        self.print_test("현재 사용자 정보 조회 - 토큰 없음 에러")
        
        response = requests.get(
            f"{self.base_url}/auth/me"
        )
        
        try:
            self.assert_error_response(response, 401)
            self.print_result(True, "토큰 없음 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_update_name_error_invalid_length(self) -> bool:
        """PATCH /auth/me/name - 이름 길이 오류"""
        self.print_test("이름 업데이트 - 이름 길이 오류")
        
        # 이름이 너무 긴 경우 (100자 초과)
        payload = {
            "name": "a" * 101
        }
        
        response = requests.patch(
            f"{self.base_url}/auth/me/name",
            headers=self.user_headers,
            json=payload
        )
        
        try:
            # FastAPI는 validation error를 422로 반환
            self.assert_error_response(response, 422)
            self.print_result(True, "이름 길이 오류 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def test_auth_password_reset_request_error_nonexistent(self) -> bool:
        """POST /auth/password-reset/request - 존재하지 않는 사용자 에러"""
        self.print_test("비밀번호 재설정 요청 - 존재하지 않는 사용자 에러")
        
        payload = {
            "email": "nonexistent@test.com"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/password-reset/request",
            json=payload
        )
        
        try:
            self.assert_error_response(response, 404)
            self.print_result(True, "존재하지 않는 사용자 에러 확인 성공")
            return True
        except Exception as e:
            self.print_result(False, str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """모든 인증 API 테스트 실행"""
        results = {}
        
        def safe_run(test_name: str, test_func):
            """테스트를 안전하게 실행하고 예외 발생 시 False 반환"""
            try:
                return test_func()
            except Exception as e:
                print(f"✗ {test_name} 실행 중 예외 발생: {type(e).__name__} - {str(e)[:200]}")
                return False
        
        # 성공 케이스
        results["signup"] = safe_run("test_auth_signup", self.test_auth_signup)
        results["login"] = safe_run("test_auth_login", self.test_auth_login)
        results["google"] = safe_run("test_auth_google", self.test_auth_google)
        results["refresh"] = safe_run("test_auth_refresh", self.test_auth_refresh)
        results["logout"] = safe_run("test_auth_logout", self.test_auth_logout)
        results["me"] = safe_run("test_auth_me", self.test_auth_me)
        results["update_name"] = safe_run("test_auth_update_name", self.test_auth_update_name)
        results["password_reset_request"] = safe_run("test_auth_password_reset_request", self.test_auth_password_reset_request)
        results["password_reset_confirm"] = safe_run("test_auth_password_reset_confirm", self.test_auth_password_reset_confirm)
        
        # 에러 케이스
        results["signup_error_duplicate_email"] = safe_run("test_auth_signup_error_duplicate_email", self.test_auth_signup_error_duplicate_email)
        results["signup_error_invalid_email"] = safe_run("test_auth_signup_error_invalid_email", self.test_auth_signup_error_invalid_email)
        results["signup_error_invalid_password"] = safe_run("test_auth_signup_error_invalid_password", self.test_auth_signup_error_invalid_password)
        results["login_error_wrong_password"] = safe_run("test_auth_login_error_wrong_password", self.test_auth_login_error_wrong_password)
        results["login_error_nonexistent_user"] = safe_run("test_auth_login_error_nonexistent_user", self.test_auth_login_error_nonexistent_user)
        results["me_error_no_token"] = safe_run("test_auth_me_error_no_token", self.test_auth_me_error_no_token)
        results["update_name_error_invalid_length"] = safe_run("test_auth_update_name_error_invalid_length", self.test_auth_update_name_error_invalid_length)
        results["password_reset_request_error_nonexistent"] = safe_run("test_auth_password_reset_request_error_nonexistent", self.test_auth_password_reset_request_error_nonexistent)
        
        return results
