from fastapi import APIRouter

from app.routers.event import home, creation, entry, detail, setting, comment


router = APIRouter()

# 모든 서브 라우터를 메인 라우터에 포함
router.include_router(home.router)
router.include_router(creation.router)
router.include_router(entry.router)
router.include_router(detail.router)
router.include_router(setting.router)
router.include_router(comment.router)
