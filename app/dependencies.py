from typing import Annotated
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from uuid import UUID

from app.schemas.auth import CurrentUser
from app.db import get_db

# JWT 인증용 (나중에 팀원이 실제 구현 완성)
security = HTTPBearer()


# TODO: 팀원이 auth 구현 완료 후 실제 구현으로 교체
async def get_current_user(
    # 임시: 개발 중에는 X-User-Id 헤더 사용, 나중에 JWT 토큰으로 변경
    x_user_id: Annotated[str | None, Header()] = None,
    # 실제 구현 시 사용:
    # credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None,
    db = Depends(get_db)
) -> CurrentUser:
    """
    현재 인증된 사용자 정보를 반환하는 dependency
    
    임시 구현: 개발 중에는 X-User-Id 헤더로 테스트
    실제 구현: JWT 토큰에서 사용자 정보 추출 (팀원이 완성 예정)
    """
    # TODO: 팀원이 auth 구현 완료 후 아래 주석 처리하고 실제 구현 활성화
    # 실제 구현:
    # token = credentials.credentials
    # auth_service = AuthService(db)
    # user = await auth_service.verify_token_and_get_user(token)
    # if not user or not user.is_active:
    #     raise HTTPException(status_code=401, detail="Invalid or inactive user")
    # return CurrentUser.model_validate(user)
    
    # 임시 구현: 개발용 (X-User-Id 헤더 또는 기본 테스트 사용자)
    if x_user_id:
        try:
            user_id = UUID(x_user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
    else:
        # 기본 테스트 사용자 ID (개발용)
        user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # TODO: 실제 DB에서 사용자 조회 필요 (현재는 Mock 객체 반환)
    # repo = UserRepository(db)
    # user = repo.get_by_id(user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return CurrentUser.model_validate(user)
    
    # 임시: Mock 객체 반환 (DB 연결 없이 개발 가능)
    return CurrentUser(
        id=user_id,
        email="test@example.com",
        is_active=True
    )