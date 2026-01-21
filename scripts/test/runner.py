"""
메인 테스트 러너

사용법:
    # 커맨드라인 인자 사용
    python -m scripts.test.runner <base_url> <admin_token> <user_token>
    
    # 환경 변수 사용
    export TEST_BASE_URL=http://localhost:8000
    export TEST_ADMIN_TOKEN=<admin_token>
    export TEST_USER_TOKEN=<user_token>
    python -m scripts.test.runner
    
    # .env 파일 사용 (프로젝트 루트에 .env 파일 생성)
    # TEST_BASE_URL=http://localhost:8000
    # TEST_ADMIN_TOKEN=<admin_token>
    # TEST_USER_TOKEN=<user_token>
    python -m scripts.test.runner
    
    # 특정 모듈만 실행
    python -m scripts.test.runner --module test_auth
    
    # 여러 모듈 실행
    python -m scripts.test.runner --module test_auth test_vote
    
    # 특정 테스트 함수만 실행
    python -m scripts.test.runner --module test_auth --test test_auth_login
"""

import sys
import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from scripts.test.base import BaseAPITester


# 테스트 모듈 매핑
TEST_MODULES = {
    "test_auth": "scripts.test.test_auth",
    "test_event_creation": "scripts.test.test_event_creation",
    "test_event_home": "scripts.test.test_event_home",
    "test_event_detail": "scripts.test.test_event_detail",
    "test_proposal_status": "scripts.test.test_proposal_status",
    "test_comment": "scripts.test.test_comment",
    "test_vote": "scripts.test.test_vote",
    "test_event_setting": "scripts.test.test_event_setting",
    "test_membership": "scripts.test.test_membership",
}


def discover_test_modules() -> List[str]:
    """테스트 모듈 자동 발견"""
    test_dir = Path(__file__).parent
    modules = []
    
    for file in test_dir.glob("test_*.py"):
        module_name = file.stem
        if module_name in TEST_MODULES:
            modules.append(module_name)
    
    return sorted(modules)


def load_test_class(module_name: str) -> type:
    """테스트 모듈에서 테스트 클래스 로드"""
    module_path = TEST_MODULES.get(module_name)
    if not module_path:
        raise ValueError(f"알 수 없는 테스트 모듈: {module_name}")
    
    module = importlib.import_module(module_path)
    
    # BaseAPITester를 상속받은 클래스 찾기
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (issubclass(obj, BaseAPITester) and 
            obj != BaseAPITester and 
            obj.__module__ == module_path):
            return obj
    
    raise ValueError(f"테스트 클래스를 찾을 수 없습니다: {module_name}")


def get_test_methods(test_class: type) -> List[str]:
    """테스트 클래스에서 test_로 시작하는 메서드 목록 반환"""
    methods = []
    for name, method in inspect.getmembers(test_class, inspect.isfunction):
        if name.startswith("test_") and name != "run_all_tests":
            methods.append(name)
    return sorted(methods)


def run_test_module(
    module_name: str,
    tester: BaseAPITester,
    test_method: Optional[str] = None
) -> Tuple[Dict[str, bool], int, int]:
    """
    테스트 모듈 실행
    
    Returns:
        (results_dict, passed_count, total_count)
    """
    print(f"\n[{module_name}]")
    
    test_class = load_test_class(module_name)
    
    # ID/PW 방식으로 토큰 생성 (토큰 직접 전달 대신)
    # 각 테스트 모듈에서 자체적으로 로그인하여 토큰을 얻도록 함
    # 인증 정보는 BaseAPITester 클래스 변수로 처음에만 출력됨
    test_instance = test_class(
        tester.base_url,
        admin_token=None,  # 토큰은 전달하지 않음
        user_token=None,   # 토큰은 전달하지 않음
        admin_email=tester.admin_email,
        admin_password=tester.admin_password,
        user_email=tester.user_email,
        user_password=tester.user_password,
        print_auth_info=False  # 각 모듈에서는 인증 정보 출력하지 않음
    )
    
    # 상태 공유
    test_instance.event_id = tester.event_id
    test_instance.entrance_code = tester.entrance_code
    test_instance.event_status = tester.event_status
    test_instance.option_ids = tester.option_ids
    test_instance.criterion_ids = tester.criterion_ids
    test_instance.assumption_ids = tester.assumption_ids
    test_instance.proposal_ids = tester.proposal_ids
    test_instance.membership_id = tester.membership_id
    test_instance.comment_id = tester.comment_id
    test_instance.created_event_ids = tester.created_event_ids.copy() if tester.created_event_ids else []
    
    results = {}
    
    if test_method:
        # 특정 테스트만 실행
        if hasattr(test_instance, test_method):
            try:
                result = getattr(test_instance, test_method)()
                results[test_method] = result
            except Exception as e:
                print(f"✗ {test_method}: {type(e).__name__} - {str(e)[:200]}")  # 로그 간소화
                results[test_method] = False
        else:
            print(f"테스트 메서드를 찾을 수 없습니다: {test_method}")
            results[test_method] = False
    else:
        # 모든 테스트 실행
        if hasattr(test_instance, "run_all_tests"):
            try:
                results = test_instance.run_all_tests()
                # 결과가 딕셔너리가 아니거나 비어있으면 에러 처리
                if not isinstance(results, dict):
                    print(f"[경고] run_all_tests()가 딕셔너리를 반환하지 않았습니다: {type(results)}")
                    results = {}
                # 빈 딕셔너리인 경우 테스트 메서드를 찾아서 False로 설정
                if not results:
                    print(f"[경고] run_all_tests()가 빈 딕셔너리를 반환했습니다. 테스트 메서드를 찾아 False로 설정합니다.")
                    test_methods = [name for name in dir(test_instance) if name.startswith("test_") and callable(getattr(test_instance, name))]
                    for method_name in test_methods:
                        results[method_name] = False
            except Exception as e:
                print(f"✗ 모듈 {module_name} 실행 오류: {type(e).__name__} - {str(e)[:200]}")  # 로그 간소화
                # 예외 발생 시 모든 테스트를 False로 처리하기 위해 빈 딕셔너리 반환
                # (실제 테스트 메서드들을 찾아서 False로 설정)
                results = {}
                # test_로 시작하는 메서드 찾기
                test_methods = [name for name in dir(test_instance) if name.startswith("test_") and callable(getattr(test_instance, name))]
                for method_name in test_methods:
                    results[method_name] = False
        else:
            # run_all_tests가 없으면 test_로 시작하는 메서드 자동 실행
            test_methods = get_test_methods(test_class)
            for method_name in test_methods:
                try:
                    result = getattr(test_instance, method_name)()
                    results[method_name] = result
                except Exception as e:
                    print(f"테스트 실행 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                    results[method_name] = False
    
    # 상태 업데이트
    tester.event_id = test_instance.event_id
    tester.entrance_code = test_instance.entrance_code
    tester.event_status = test_instance.event_status
    tester.option_ids = test_instance.option_ids
    tester.criterion_ids = test_instance.criterion_ids
    tester.assumption_ids = test_instance.assumption_ids
    tester.proposal_ids = test_instance.proposal_ids
    tester.membership_id = test_instance.membership_id
    tester.comment_id = test_instance.comment_id
    
    # 생성한 이벤트 ID 추적 (cleanup용)
    if hasattr(test_instance, 'created_event_ids'):
        for event_id in test_instance.created_event_ids:
            if event_id not in tester.created_event_ids:
                tester.created_event_ids.append(event_id)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    # 모듈별 결과 출력 (실패한 것만 상세 출력)
    # 성공한 테스트는 마지막 요약에서만 표시
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n실패한 테스트 ({len(failed_tests)}개):")
        for test_name in failed_tests:
            print(f"  ✗ {test_name}")
    
    return results, passed, total


def parse_args():
    """
    커맨드라인 인자 및 환경 변수 파싱
    
    우선순위:
    1. 커맨드라인 인자
    2. 환경 변수 (export로 설정한 경우)
    3. .env 파일
    
    토큰 또는 ID/PW 중 하나만 제공하면 됩니다.
    """
    # .env 파일 로드 (프로젝트 루트에서)
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"[환경 변수] .env 파일 발견: {env_file}")
        load_dotenv(env_file, override=True)  # override=True로 기존 환경 변수 덮어쓰기
    else:
        print(f"[환경 변수] .env 파일 없음: {env_file}")
    
    # 환경 변수에서 읽기 (빈 문자열도 None으로 처리)
    def get_env_clean(key: str) -> Optional[str]:
        """환경 변수를 읽고 빈 문자열을 None으로 변환"""
        value = os.getenv(key)
        return value.strip() if value and value.strip() else None
    
    base_url = get_env_clean("TEST_BASE_URL") or get_env_clean("BASE_URL")
    
    # 토큰 방식
    admin_token = get_env_clean("TEST_ADMIN_TOKEN") or get_env_clean("ADMIN_TOKEN")
    user_token = get_env_clean("TEST_USER_TOKEN") or get_env_clean("USER_TOKEN")
    
    # ID/PW 방식
    admin_email = get_env_clean("TEST_ADMIN_EMAIL") or get_env_clean("ADMIN_EMAIL")
    admin_password = get_env_clean("TEST_ADMIN_PASSWORD") or get_env_clean("ADMIN_PASSWORD")
    user_email = get_env_clean("TEST_USER_EMAIL") or get_env_clean("USER_EMAIL")
    user_password = get_env_clean("TEST_USER_PASSWORD") or get_env_clean("USER_PASSWORD")
    
    # 디버깅: 환경 변수 읽기 결과 출력
    print(f"\n[환경 변수 확인]")
    print(f"  TEST_BASE_URL: {base_url or '없음'}")
    print(f"  TEST_ADMIN_TOKEN: {'설정됨 (' + str(len(admin_token)) + '자)' if admin_token else '없음'}")
    print(f"  TEST_USER_TOKEN: {'설정됨 (' + str(len(user_token)) + '자)' if user_token else '없음'}")
    print(f"  TEST_ADMIN_EMAIL: {admin_email or '없음'}")
    print(f"  TEST_ADMIN_PASSWORD: {'설정됨' if admin_password else '없음'}")
    print(f"  TEST_USER_EMAIL: {user_email or '없음'}")
    print(f"  TEST_USER_PASSWORD: {'설정됨' if user_password else '없음'}")
    
    modules = []
    test_method = None
    
    # 커맨드라인 인자 파싱
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--module":
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                modules.append(sys.argv[i])
                i += 1
        elif sys.argv[i] == "--test":
            i += 1
            if i < len(sys.argv):
                test_method = sys.argv[i]
                i += 1
        elif not sys.argv[i].startswith("--"):
            # 위치 인자 (base_url, admin_token/user_email, user_token/user_email)
            if base_url is None:
                base_url = sys.argv[i]
            elif admin_token is None and admin_email is None:
                # 토큰인지 이메일인지 판단 (이메일 형식 체크)
                if "@" in sys.argv[i]:
                    admin_email = sys.argv[i]
                else:
                    admin_token = sys.argv[i]
            elif user_token is None and user_email is None:
                if "@" in sys.argv[i]:
                    user_email = sys.argv[i]
                else:
                    user_token = sys.argv[i]
            i += 1
        else:
            i += 1
    
    # 필수 인자 확인
    if not base_url:
        print("오류: base_url이 필요합니다.")
        print("\n사용법:")
        print("  1. 토큰 방식 (커맨드라인):")
        print("     python -m scripts.test.runner <base_url> <admin_token> <user_token>")
        print("  2. ID/PW 방식 (커맨드라인):")
        print("     python -m scripts.test.runner <base_url> <admin_email> <user_email>")
        print("     (비밀번호는 환경 변수로 제공)")
        print("  3. 환경 변수 (토큰 방식):")
        print("     export TEST_BASE_URL=http://localhost:8000")
        print("     export TEST_ADMIN_TOKEN=<admin_token>")
        print("     export TEST_USER_TOKEN=<user_token>")
        print("     python -m scripts.test.runner")
        print("  4. 환경 변수 (ID/PW 방식):")
        print("     export TEST_BASE_URL=http://localhost:8000")
        print("     export TEST_ADMIN_EMAIL=admin@test.com")
        print("     export TEST_ADMIN_PASSWORD=password")
        print("     export TEST_USER_EMAIL=user@test.com")
        print("     export TEST_USER_PASSWORD=password")
        print("     python -m scripts.test.runner")
        print("  5. .env 파일:")
        print("     TEST_BASE_URL=http://localhost:8000")
        print("     TEST_ADMIN_EMAIL=admin@test.com")
        print("     TEST_ADMIN_PASSWORD=password")
        print("     TEST_USER_EMAIL=user@test.com")
        print("     TEST_USER_PASSWORD=password")
        print("     python -m scripts.test.runner")
        sys.exit(1)
    
    # Admin 인증 정보 확인 (이미 get_env_clean에서 처리됨)
    
    if not admin_token and not (admin_email and admin_password):
        print("오류: admin 인증 정보가 필요합니다.")
        print("TEST_ADMIN_TOKEN 또는 (TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)를 제공하세요.")
        print(f"\n현재 설정:")
        print(f"  TEST_ADMIN_TOKEN: {'설정됨 (길이: ' + str(len(admin_token)) + ')' if admin_token else '없음'}")
        print(f"  TEST_ADMIN_EMAIL: {admin_email or '없음'}")
        print(f"  TEST_ADMIN_PASSWORD: {'설정됨' if admin_password else '없음'}")
        sys.exit(1)
    
    # User 인증 정보 확인
    if not user_token and not (user_email and user_password):
        print("오류: user 인증 정보가 필요합니다.")
        print("TEST_USER_TOKEN 또는 (TEST_USER_EMAIL, TEST_USER_PASSWORD)를 제공하세요.")
        print(f"\n현재 설정:")
        print(f"  TEST_USER_TOKEN: {'설정됨 (길이: ' + str(len(user_token)) + ')' if user_token else '없음'}")
        print(f"  TEST_USER_EMAIL: {user_email or '없음'}")
        print(f"  TEST_USER_PASSWORD: {'설정됨' if user_password else '없음'}")
        sys.exit(1)
    
    return base_url, admin_token, user_token, admin_email, admin_password, user_email, user_password, modules, test_method


def main():
    """메인 함수"""
    base_url, admin_token, user_token, admin_email, admin_password, user_email, user_password, modules, test_method = parse_args()
    
    # 베이스 테스터 초기화
    tester = BaseAPITester(
        base_url,
        admin_token=admin_token,
        user_token=user_token,
        admin_email=admin_email,
        admin_password=admin_password,
        user_email=user_email,
        user_password=user_password
    )
    
    # 실행할 모듈 결정
    if modules:
        test_modules = modules
    else:
        test_modules = discover_test_modules()
    
    print("\n" + "="*60)
    print("API 통합 테스트 시작")
    print("="*60)
    print(f"Base URL: {base_url}")
    print(f"테스트 모듈: {', '.join(test_modules)}")
    if test_method:
        print(f"특정 테스트: {test_method}")
    print("="*60)
    
    # 전체 실행 시 성공한 테스트 출력 억제 (개별 테스트 실행 시에는 상세 출력)
    if not test_method and len(test_modules) > 1:
        BaseAPITester._suppress_success_output = True
    
    # 전체 결과 집계
    all_results = {}
    module_results = {}
    
    # 각 모듈 실행
    for module_name in test_modules:
        try:
            results, passed, total = run_test_module(module_name, tester, test_method)
            all_results.update(results)
            module_results[module_name] = (passed, total)
        except Exception as e:
            print(f"\n모듈 {module_name} 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            module_results[module_name] = (0, 0)
    
    # 최종 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    # 모듈별 결과
    print("\n모듈별 결과:")
    for module_name, (passed, total) in module_results.items():
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"  {module_name}: {passed}/{total} 통과 ({percentage:.1f}%)")
    
    # 전체 결과
    total_passed = sum(1 for v in all_results.values() if v)
    total_tests = len(all_results)
    total_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n전체 결과: {total_passed}/{total_tests} 통과 ({total_percentage:.1f}%)")
    
    # 성공한 테스트 목록
    passed_tests = [name for name, result in all_results.items() if result]
    if passed_tests:
        print(f"\n성공한 테스트 ({len(passed_tests)}개):")
        for test_name in passed_tests:
            print(f"  ✓ {test_name}")
    
    # 실패한 테스트 목록
    failed_tests = [name for name, result in all_results.items() if not result]
    if failed_tests:
        print(f"\n실패한 테스트 ({len(failed_tests)}개):")
        for test_name in failed_tests:
            print(f"  ✗ {test_name}")
    
    print("="*60)
    
    # 테스트 데이터 정리
    print("\n" + "="*60)
    print("테스트 데이터 정리")
    print("="*60)
    tester.cleanup()
    print("="*60)
    
    # 종료 코드
    sys.exit(0 if total_passed == total_tests else 1)


if __name__ == "__main__":
    main()
