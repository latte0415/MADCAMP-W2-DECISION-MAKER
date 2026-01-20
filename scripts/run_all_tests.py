#!/usr/bin/env python3
"""
편의용 전체 테스트 실행 스크립트

사용법:
    # 커맨드라인 인자 사용
    python scripts/run_all_tests.py <base_url> <admin_token> <user_token>
    
    # 환경 변수 사용
    export TEST_BASE_URL=http://localhost:8000
    export TEST_ADMIN_TOKEN=<admin_token>
    export TEST_USER_TOKEN=<user_token>
    python scripts/run_all_tests.py
    
    # .env 파일 사용 (프로젝트 루트에 .env 파일 생성)
    # TEST_BASE_URL=http://localhost:8000
    # TEST_ADMIN_TOKEN=<admin_token>
    # TEST_USER_TOKEN=<user_token>
    python scripts/run_all_tests.py
"""

import sys
from scripts.test.runner import main

if __name__ == "__main__":
    main()
