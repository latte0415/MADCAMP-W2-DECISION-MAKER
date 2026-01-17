from fastapi import APIRouter

from . import event, assumption, criterion, option, membership

router = APIRouter()

# 각 모듈의 라우터를 통합
router.include_router(event.router, tags=["dev-events"])
router.include_router(assumption.router, tags=["dev-assumptions"])
router.include_router(criterion.router, tags=["dev-criteria"])
router.include_router(option.router, tags=["dev-options"])
router.include_router(membership.router, tags=["dev-memberships"])
