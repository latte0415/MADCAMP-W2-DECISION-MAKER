from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from os import getenv

from app.routers.dev import router as dev_router
from app.routers.auth import router as auth_router
from app.routers.event import router as event_router
from app.dependencies.error_handlers import register_error_handlers

app = FastAPI()

# 전역 예외 핸들러 등록
register_error_handlers(app)

# CORS 설정
cors_origins = getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    origins = ["*"]
    allow_credentials = False
else:
    origins = [origin.strip() for origin in cors_origins.split(",")]
    # 개발 환경: localhost:5173 자동 추가 (중복 방지)
    dev_origin = "http://localhost:5173"
    if dev_origin not in origins:
        origins.append(dev_origin)
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# app.include_router(dev_router, prefix="/dev", tags=["dev"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(event_router, prefix="/v1", tags=["events"])