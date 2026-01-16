# Auth 구현 가이드

> **이 문서는 Auth 담당 팀원을 위한 구현 가이드입니다.**  
> DB 스키마와 인프라는 이미 준비되어 있으므로, FastAPI 기반 Auth API 구현에만 집중하면 됩니다.

## 📌 빠른 요약

**현재 상태:**
- ✅ 프로젝트 폴더 구조 완료 (모든 `__init__.py` 포함)
- ✅ DB 스키마 및 모델 정의 완료 (`app/models/auth.py`)
- ✅ 레이어드 아키텍처 구조 준비 완료
- 🆕 각 레이어의 실제 구현 파일 생성 필요

**구현해야 할 파일:**
- `app/utils/security.py` - 보안 유틸리티
- `app/schemas/auth.py` - Pydantic 스키마
- `app/repositories/auth.py` - Repository 레이어
- `app/services/auth.py` - Service 레이어
- `app/routers/auth.py` - API 레이어
- `app/dependencies.py` - 의존성 주입 (내용 구현)
- `app/db.py` - DB 연결 설정 (내용 추가)

---

## 🚀 시작하기

### 1. 프로젝트 받기

인프라 담당자가 GitHub 저장소를 공유하면 다음 명령어로 클론합니다:

```bash
git clone <저장소_URL>
cd backend
```

### 2. 초기 세팅

#### 2.1 Python 가상환경 생성 및 활성화

```bash
# Python 3.10 이상 필요
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

#### 2.2 의존성 설치

```bash
pip install -r requirements.txt
```

#### 2.3 Auth 구현에 필요한 추가 라이브러리 설치

```bash
pip install python-jose[cryptography]>=3.3.0
pip install passlib[bcrypt]>=1.7.4
pip install python-multipart>=0.0.6
```

또는 `requirements.txt`에 직접 추가한 후:

```bash
pip install -r requirements.txt
```

#### 2.4 환경 변수 설정

인프라 담당자로부터 다음 정보를 받아 `.env` 파일을 생성합니다:

```bash
# 프로젝트 루트에 .env 파일 생성
touch .env
```

`.env` 파일 내용 예시:

```env
# DB 연결 (인프라 담당자에게 로컬 개발용 정보 요청)
DATABASE_URL=postgresql+psycopg://app_runtime:password@localhost:5432/dbname

# JWT 설정
SECRET_KEY=your-secret-key-here-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**⚠️ 주의사항**:
- `.env` 파일은 `.gitignore`에 포함되어 있으므로 Git에 커밋되지 않습니다
- 로컬 개발용 DB 연결 정보는 인프라 담당자에게 문의하세요
- `SECRET_KEY`는 반드시 강력한 랜덤 문자열을 사용하세요 (최소 32자 이상 권장)
- 프로덕션 환경의 `SECRET_KEY`는 절대 공유하지 마세요

#### 2.5 서버 실행 확인

```bash
# 개발 서버 실행
uvicorn main:app --reload

# 브라우저에서 확인
# http://localhost:8000/health
# http://localhost:8000/docs (FastAPI 자동 생성 문서)
```

---

## 📁 프로젝트 구조 및 구현 위치

### 현재 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py              # ✅ 패키지 초기화 파일
│   ├── db.py                    # ✅ SQLAlchemy Base 클래스 (이미 존재)
│   ├── dependencies.py           # ✅ FastAPI 의존성 (비어있음, 구현 필요)
│   ├── models/
│   │   ├── __init__.py          # ✅ 모델 export (이미 존재)
│   │   └── auth.py               # ✅ 이미 존재 (User, UserIdentity, RefreshToken)
│   ├── repositories/
│   │   └── __init__.py          # ✅ 패키지 초기화 (이미 존재)
│   ├── routers/
│   │   └── __init__.py          # ✅ 패키지 초기화 (이미 존재)
│   ├── schemas/
│   │   └── __init__.py          # ✅ 패키지 초기화 (이미 존재)
│   ├── services/
│   │   └── __init__.py          # ✅ 패키지 초기화 (이미 존재)
│   └── utils/
│       └── __init__.py          # ✅ 패키지 초기화 (이미 존재)
├── main.py                       # FastAPI 앱 진입점
├── requirements.txt              # Python 의존성
├── migrations/                   # Alembic 마이그레이션 (건드리지 않음)
└── docs/
    └── auth_guide.md            # 이 문서
```

**✅ 완료된 작업:**
- 모든 폴더 구조 생성 완료
- 각 패키지의 `__init__.py` 파일 생성 완료
- `app/models/__init__.py`에 모델 export 코드 추가 완료

**📝 모델 사용 방법:**
`app/models/__init__.py`에서 모델을 export하고 있으므로, 다음과 같이 import할 수 있습니다:

```python
# 방법 1: 직접 import
from app.models.auth import User, UserIdentity, RefreshToken

# 방법 2: __init__.py를 통해 import (권장)
from app.models import User, UserIdentity, RefreshToken
```

### 구현해야 할 파일들 (레이어드 아키텍처)

다음 파일들을 **새로 생성**해야 합니다. **레이어드 아키텍처**를 적용합니다:

```
app/
├── schemas/
│   └── auth.py                  # 🆕 Pydantic 모델 (요청/응답 스키마)
├── routers/
│   └── auth.py                  # 🆕 API 레이어 (HTTP 요청/응답 처리)
├── services/
│   └── auth.py                  # 🆕 Service 레이어 (비즈니스 로직)
├── repositories/
│   └── auth.py                  # 🆕 Repository 레이어 (DB 접근 로직)
├── utils/
│   └── security.py              # 🆕 비밀번호 해싱, JWT 유틸리티
└── dependencies.py              # ✅ 이미 존재 (내용 구현 필요)
```

**참고:**
- 모든 폴더와 `__init__.py` 파일은 이미 생성되어 있습니다
- `app/dependencies.py` 파일도 이미 존재하지만 내용을 구현해야 합니다

**아키텍처 흐름:**
```
API (Router) 
  ↓
Service (비즈니스 로직)
  ↓
Repository (DB 접근)
  ↓
DB (Domain 모델: app/models/auth.py)
```

**각 레이어의 역할:**
- **Router (API)**: HTTP 요청/응답 처리, 입력 검증, Service 호출
- **Service**: 비즈니스 로직 (회원가입, 로그인, 토큰 발급 등)
- **Repository**: DB CRUD 작업 캡슐화 (SQLAlchemy 세션 사용)
- **Domain**: `app/models/auth.py`의 SQLAlchemy 모델 (이미 존재)
- **Schema**: `app/schemas/auth.py`의 Pydantic 모델 (요청/응답 DTO)

### main.py 수정

`main.py`에 Auth 라우터를 등록해야 합니다:

```python
from fastapi import FastAPI
from app.routers import auth  # 추가

app = FastAPI()

# 기존 엔드포인트
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Auth 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])  # 추가
```

### 구현 순서 추천 (레이어드 아키텍처 기준)

**하위 레이어부터 상위 레이어 순서로 구현:**

1. **`app/utils/security.py`** (유틸리티)
   - 비밀번호 해싱 함수 (`hash_password`, `verify_password`)
   - JWT 토큰 생성/검증 함수 (`create_access_token`, `create_refresh_token`, `verify_token`)

2. **`app/schemas/auth.py`** (Schema 레이어)
   - 요청 스키마: `SignupRequest`, `LoginRequest`, `RefreshRequest`
   - 응답 스키마: `TokenResponse`, `UserResponse`

3. **`app/repositories/auth.py`** (Repository 레이어)
   - `UserRepository`: 사용자 CRUD
   - `UserIdentityRepository`: 사용자 인증 정보 CRUD
   - `RefreshTokenRepository`: 리프레시 토큰 CRUD
   - 예시:
     ```python
     class UserRepository:
         def __init__(self, db: Session):
             self.db = db
         
         def create_user(self, email: str, password_hash: str) -> User:
             # DB 작업
         
         def get_user_by_email(self, email: str) -> User | None:
             # DB 조회
     ```

4. **`app/services/auth.py`** (Service 레이어)
   - Repository를 주입받아 사용
   - 비즈니스 로직 구현:
     - `signup()`: 회원가입 (User + UserIdentity 생성)
     - `login()`: 로그인 (인증 후 토큰 발급)
     - `refresh_token()`: 토큰 갱신
     - `logout()`: 로그아웃
   - 예시:
     ```python
     class AuthService:
         def __init__(
             self,
             user_repo: UserRepository,
             identity_repo: UserIdentityRepository,
             token_repo: RefreshTokenRepository
         ):
             self.user_repo = user_repo
             self.identity_repo = identity_repo
             self.token_repo = token_repo
         
         def signup(self, email: str, password: str) -> TokenResponse:
             # 비즈니스 로직
     ```

5. **`app/dependencies.py`** (의존성) - ✅ 파일 이미 존재, 내용 구현 필요
   - `get_db`: DB 세션 제공
   - `get_current_user`: Access token에서 사용자 정보 추출
   - Repository 인스턴스 생성 함수들 (예: `get_user_repository`, `get_auth_service` 등)

6. **`app/routers/auth.py`** (API 레이어)
   - HTTP 엔드포인트 정의
   - Service를 주입받아 호출
   - 예시:
     ```python
     @router.post("/signup")
     async def signup(
         request: SignupRequest,
         service: AuthService = Depends(get_auth_service)
     ):
         return service.signup(request.email, request.password)
     ```

7. **`main.py`** 수정
   - Auth 라우터 등록

### DB 연결 설정

DB 연결은 환경 변수 `DATABASE_URL`을 통해 설정됩니다.  
`app/db.py`에 DB 세션 관리 코드를 추가해야 합니다:

```python
# app/db.py 수정 예시
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from os import getenv

class Base(DeclarativeBase):
    pass

# DB 연결 설정 (환경 변수에서 읽기)
DATABASE_URL = getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI 의존성으로 사용할 DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**레이어드 아키텍처 사용 예시:**

```python
# app/repositories/auth.py
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()  # user.id 생성
        return user
    
    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

# app/services/auth.py
class AuthService:
    def __init__(self, user_repo: UserRepository, ...):
        self.user_repo = user_repo
    
    def signup(self, email: str, password: str) -> TokenResponse:
        # Repository를 통해 DB 접근
        user = self.user_repo.create_user(email, hashed_password)
        # 비즈니스 로직 처리
        ...

# app/routers/auth.py
@router.post("/signup")
async def signup(
    request: SignupRequest,
    service: AuthService = Depends(get_auth_service)  # Service 주입
):
    return service.signup(request.email, request.password)
```

---

## 📋 현재 상태

### ✅ 완료된 작업

- **DB 스키마**: `users`, `user_identities`, `refresh_tokens` 테이블 생성 완료
- **Alembic 마이그레이션**: 체계 정상 작동 중
- **인프라**: AWS Lightsail + Docker 배포 완료
- **기본 API**: `/health` 엔드포인트 동작 확인

### 🎯 팀원이 구현해야 할 작업

- FastAPI 기반 Auth API 구현
- JWT access/refresh 토큰 발급·검증
- 로컬 로그인 구현 (추후 Google OAuth 확장 가능하도록 설계)
- Auth 관련 엔드포인트 구현

---

## 📤 GitHub 저장소 공유 방법 (인프라 담당자용)

팀원에게 프로젝트를 공유하려면:

### 1. GitHub 저장소 생성 및 푸시

```bash
# 저장소 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit: Auth 스키마 및 인프라 설정"

# GitHub에 저장소 생성 후
git remote add origin <저장소_URL>
git branch -M main
git push -u origin main
```

### 2. 팀원 초대

- GitHub 저장소 Settings → Collaborators에서 팀원 추가
- 또는 Organization/Team을 사용하는 경우 해당 팀에 권한 부여

### 3. 팀원에게 전달할 정보

다음 정보를 팀원에게 공유하세요:

- **저장소 URL**: `https://github.com/...`
- **로컬 개발용 DB 연결 정보** (`.env` 파일 내용 또는 별도 문서)
  - `DATABASE_URL`
  - `SECRET_KEY` (JWT 서명용)
  - 기타 필요한 환경 변수

### 4. 브랜치 전략 (선택사항)

팀원이 Auth 구현을 별도 브랜치에서 작업하도록 권장:

```bash
# 팀원이 실행
git checkout -b feature/auth-implementation
# 작업 후
git push origin feature/auth-implementation
```

---

## 🚫 절대 하지 말아야 할 것

다음 작업은 **절대 하지 마세요**. 인프라 담당자가 관리합니다.

- ❌ **DB 스키마 변경** (테이블 추가/수정/삭제)
- ❌ **Alembic 마이그레이션 생성/적용**
- ❌ **`app_owner` 계정 사용** (DDL 권한 계정)
- ❌ **환경 변수 파일(.env) 수정** (DB 연결 정보 등)

---

## 🔧 환경 정보

### API 엔드포인트

```
Base URL: http://15.164.74.228
Health:   GET /health
```

### DB 접근 정책

- **런타임 계정**: `app_runtime` (API에서 사용)
- **DDL 계정**: `app_owner` (인프라 담당자만 사용)
- **테이블 목록**:
  - `users`
  - `user_identities`
  - `refresh_tokens`

---

## 📊 스키마 설계 의도

### 1. `users` 테이블

- 사용자 기본 정보 저장
- `email`, `password_hash`는 nullable (OAuth 사용자 대비)
- `is_active`로 계정 활성화 상태 관리

### 2. `user_identities` 테이블

- **핵심 설계**: 로그인 방식을 확장 가능하게 설계
- `provider`: `'local'`, `'google'`, `'kakao'` 등
- `provider_user_id`: 각 provider의 고유 ID
- 동일 사용자가 여러 provider로 로그인 가능 (예: local + google)

### 3. `refresh_tokens` 테이블

- **보안**: 토큰은 **해시만 저장** (원본 저장 금지)
- `revoked_at`: 토큰 폐기 시점 기록
- 토큰 회전/폐기는 DB 상태로 관리

---

## 🎯 구현해야 할 API 엔드포인트

### 1. 회원가입 (`POST /signup`)

**요청:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**처리 흐름:**
1. 이메일 중복 확인 (`users.email` 또는 `user_identities`에서 `provider='local'` 조회)
2. 비밀번호 해싱 (bcrypt 권장)
3. 트랜잭션 내에서:
   - `users` 테이블에 사용자 생성
   - `user_identities` 테이블에 `provider='local'` row 생성
4. JWT access/refresh 토큰 발급
5. `refresh_tokens` 테이블에 refresh token 해시 저장

**응답:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

### 2. 로그인 (`POST /login`)

**요청:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**처리 흐름:**
1. `user_identities`에서 `provider='local'` + `email`로 사용자 조회
2. 비밀번호 검증
3. JWT access/refresh 토큰 발급
4. `refresh_tokens` 테이블에 refresh token 해시 저장

**응답:** (회원가입과 동일)

### 3. 토큰 갱신 (`POST /refresh`)

**요청:**
```json
{
  "refresh_token": "eyJ..."
}
```

**처리 흐름:**
1. refresh token 검증 (JWT 서명 + 만료 시간)
2. refresh token 해시 생성 후 DB에서 조회
3. `revoked_at IS NULL` 및 `expires_at > NOW()` 확인
4. 기존 refresh token `revoked_at` 업데이트 (토큰 회전)
5. 새로운 access/refresh 토큰 발급
6. 새로운 refresh token 해시 저장

**응답:** (회원가입과 동일)

### 4. 로그아웃 (`POST /logout`)

**요청:**
```json
{
  "refresh_token": "eyJ..."
}
```

**처리 흐름:**
1. refresh token 해시 생성 후 DB에서 조회
2. `revoked_at` 업데이트

**응답:**
```json
{
  "message": "Logged out successfully"
}
```

### 5. 현재 사용자 정보 (`GET /me`)

**요청 헤더:**
```
Authorization: Bearer <access_token>
```

**처리 흐름:**
1. Access token 검증
2. 사용자 정보 조회

**응답:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 💡 구현 규칙 및 가이드라인

### 1. 회원가입 시

```python
# 의사코드
with db_session.begin():
    # 1. users 생성
    user = User(email=email, password_hash=hashed_password)
    db_session.add(user)
    db_session.flush()  # user.id 생성
    
    # 2. user_identities 생성
    identity = UserIdentity(
        user_id=user.id,
        provider='local',
        provider_user_id=email,  # 또는 별도 ID
        email=email
    )
    db_session.add(identity)
```

### 2. 로그인 시

```python
# user_identities 기준으로 사용자 조회
identity = db_session.query(UserIdentity).filter(
    UserIdentity.provider == 'local',
    UserIdentity.email == email
).first()

if not identity:
    raise HTTPException(401, "Invalid credentials")

user = identity.user
# 비밀번호 검증 후 토큰 발급
```

### 3. Refresh Token 재사용 시

```python
# 기존 토큰 폐기 (토큰 회전)
existing_token = db_session.query(RefreshToken).filter(
    RefreshToken.token_hash == old_token_hash,
    RefreshToken.revoked_at.is_(None)
).first()

if existing_token:
    existing_token.revoked_at = datetime.utcnow()

# 새 토큰 저장
new_refresh_token = RefreshToken(
    user_id=user.id,
    token_hash=new_token_hash,
    expires_at=expires_at
)
db_session.add(new_refresh_token)
```

### 4. 보안 주의사항

- **비밀번호**: bcrypt로 해싱 (최소 10 rounds 권장)
- **Refresh Token**: DB에 저장 시 반드시 해시만 저장
- **Access Token**: 짧은 만료 시간 (예: 15분)
- **Refresh Token**: 긴 만료 시간 (예: 7일)
- **에러 메시지**: 구체적인 에러 정보 노출 금지 (보안 취약점)

### 5. JWT 토큰 구조

**Access Token Payload 예시:**
```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "type": "access",
  "exp": 1234567890
}
```

**Refresh Token Payload 예시:**
```json
{
  "sub": "user_uuid",
  "type": "refresh",
  "exp": 1234567890,
  "jti": "token_uuid"  # 토큰 고유 ID (선택)
}
```

---

## 📁 최종 파일 구조 (구현 완료 후)

구현이 완료되면 다음과 같은 구조가 됩니다:

```
app/
├── __init__.py              # ✅ 패키지 초기화
├── db.py                    # ✅ DB 연결 설정 (수정 필요)
├── dependencies.py          # ✅ 의존성 주입 함수들 (구현 필요)
├── models/
│   ├── __init__.py         # ✅ 모델 export
│   └── auth.py             # ✅ User, UserIdentity, RefreshToken
├── repositories/
│   ├── __init__.py         # ✅ 패키지 초기화
│   └── auth.py             # 🆕 Repository 레이어 (생성 필요)
├── routers/
│   ├── __init__.py         # ✅ 패키지 초기화
│   └── auth.py             # 🆕 API 레이어 (생성 필요)
├── schemas/
│   ├── __init__.py         # ✅ 패키지 초기화
│   └── auth.py             # 🆕 Pydantic 모델 (생성 필요)
├── services/
│   ├── __init__.py         # ✅ 패키지 초기화
│   └── auth.py             # 🆕 Service 레이어 (생성 필요)
└── utils/
    ├── __init__.py         # ✅ 패키지 초기화
    └── security.py         # 🆕 보안 유틸리티 (생성 필요)
```

**범례:**
- ✅ = 이미 존재하는 파일/폴더
- 🆕 = 새로 생성해야 하는 파일

---

## 🔍 필요한 라이브러리

다음 라이브러리를 `requirements.txt`에 추가해야 할 수 있습니다:

```txt
python-jose[cryptography]>=3.3.0  # JWT 토큰 처리
passlib[bcrypt]>=1.7.4             # 비밀번호 해싱
python-multipart>=0.0.6            # Form 데이터 처리 (필요시)
```

---

## ✅ 체크리스트

### 파일 생성 체크리스트

- [ ] `app/utils/security.py` 생성 및 구현
- [ ] `app/schemas/auth.py` 생성 및 구현
- [ ] `app/repositories/auth.py` 생성 및 구현
- [ ] `app/services/auth.py` 생성 및 구현
- [ ] `app/dependencies.py` 내용 구현
- [ ] `app/routers/auth.py` 생성 및 구현
- [ ] `app/db.py` DB 연결 설정 추가
- [ ] `main.py`에 Auth 라우터 등록

### 기능 구현 체크리스트

- [ ] 회원가입 시 이메일 중복 체크
- [ ] 비밀번호 해싱 적용
- [ ] 트랜잭션으로 users + user_identities 동시 생성
- [ ] 로그인 시 user_identities 기준 조회
- [ ] Refresh token은 해시만 저장
- [ ] 토큰 갱신 시 기존 토큰 폐기 (토큰 회전)
- [ ] Access token 만료 시 적절한 에러 응답
- [ ] `/me` 엔드포인트에서 현재 사용자 정보 반환
- [ ] 에러 메시지가 보안상 안전한지 확인
- [ ] 레이어드 아키텍처 구조 준수 (Router → Service → Repository)

---

## 🆘 문제 발생 시

- **DB 연결 오류**: 인프라 담당자에게 문의
- **스키마 변경 필요**: 인프라 담당자와 논의 후 결정
- **마이그레이션 필요**: 인프라 담당자에게 요청

---

## 📝 참고사항

### 스키마 설계
- 현재 스키마는 **OAuth 확장을 고려**하여 설계되었습니다
- 추후 Google OAuth 추가 시 `provider='google'`로 `user_identities`에 추가하면 됩니다
- 모든 Auth 관련 로직은 `user_identities`를 기준으로 사용자를 조회하는 것이 핵심입니다

### 레이어드 아키텍처
- **Router**: HTTP 요청/응답만 처리, 비즈니스 로직은 Service에 위임
- **Service**: 비즈니스 로직 중심, Repository를 통해 DB 접근
- **Repository**: DB CRUD 작업만 담당, SQLAlchemy 세션 사용
- **Domain**: `app/models/auth.py`의 SQLAlchemy 모델 (이미 존재)
- **Schema**: Pydantic 모델로 요청/응답 검증

### Import 규칙
- 모델은 `from app.models import User, UserIdentity, RefreshToken`로 import
- 각 레이어는 상위 레이어만 import (예: Service는 Repository만 import)
- 순환 참조를 피하기 위해 의존성 방향을 명확히 유지

---

**질문이 있으면 언제든지 인프라 담당자에게 문의하세요!** 🚀
