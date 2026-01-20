"""
API 통합 테스트 모듈

사용법:
    # 전체 테스트 실행
    python -m scripts.test.runner <base_url> <admin_token> <user_token>
    
    # 특정 모듈만 실행
    python -m scripts.test.runner <base_url> <admin_token> <user_token> --module test_auth
    
    # 특정 테스트 함수만 실행
    python -m scripts.test.runner <base_url> <admin_token> <user_token> --module test_auth --test test_auth_login
"""

from scripts.test.base import BaseAPITester

__all__ = ['BaseAPITester']
