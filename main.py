from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from os import getenv

from app.routers.dev import router as dev_router
from app.routers.auth import router as auth_router

app = FastAPI()

# CORS 설정
cors_origins = getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    origins = ["*"]
    allow_credentials = False
else:
    origins = [origin.strip() for origin in cors_origins.split(",")]
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

# Dev 라우터 등록
app.include_router(dev_router, prefix="/dev", tags=["dev"])

app.add_middleware( # 테스트용
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,                   # MUST be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
