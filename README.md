# Decision Backend API

의사결정 이벤트 관리 시스템의 백엔드 API 서버입니다. FastAPI를 기반으로 구축되었으며, 이벤트 생성, 참가, 제안, 투표, 코멘트 등의 기능을 제공합니다.

## 📋 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [시작하기](#시작하기)
- [프로젝트 구조](#프로젝트-구조)
- [환경 변수](#환경-변수)
- [데이터베이스](#데이터베이스)
- [API 문서](#api-문서)
- [개발 가이드](#개발-가이드)
- [배포](#배포)
- [테스트](#테스트)

---

## 🚀 주요 기능

### 인증 및 사용자 관리
- 이메일/비밀번호 기반 회원가입 및 로그인
- Google OAuth 인증
- JWT 기반 인증 (Access Token + Refresh Token)
- 비밀번호 재설정 기능
- 사용자 프로필 관리

### 이벤트 관리
- 이벤트 생성 및 설정
- 입장 코드를 통한 이벤트 참가
- 이벤트 오버뷰 및 상세 정보 조회
- 참가한 이벤트 목록 조회

### 제안 및 투표 시스템
- **전제(Assumption) 제안**: 이벤트의 전제 조건 제안
- **기준(Criterion) 제안**: 평가 기준 제안
- **결론(Conclusion) 제안**: 최종 결론 제안
- 제안에 대한 투표 생성/삭제
- 제안 상태 관리 (대기/승인/거부)
- 투표 결과 조회

### 코멘트 시스템
- 기준별 코멘트 작성
- 코멘트 수정 및 삭제
- 코멘트 목록 조회

### 실시간 동기화
- Server-Sent Events (SSE)를 통한 실시간 업데이트
- Outbox 패턴을 통한 안정적인 이벤트 전달

### 멤버십 관리
- 이벤트 멤버 관리
- 관리자 권한 관리
- 멤버 초대 및 제거

---

## 🛠 기술 스택

### 핵심 프레임워크
- **FastAPI** 0.128.0 - 고성능 웹 프레임워크
- **Uvicorn** - ASGI 서버
- **Python** 3.11+

### 데이터베이스
- **PostgreSQL** 16 - 관계형 데이터베이스
- **SQLAlchemy** 2.0.45 - ORM
- **Alembic** 1.18.1 - 데이터베이스 마이그레이션

### 인증 및 보안
- **python-jose** - JWT 토큰 처리
- **passlib[bcrypt]** - 비밀번호 해싱
- **google-auth** - Google OAuth 인증
- **sendgrid** - 이메일 발송 (비밀번호 재설정)

### 검증 및 스키마
- **Pydantic** 2.12.5 - 데이터 검증 및 직렬화

### 인프라
- **Docker** & **Docker Compose** - 컨테이너화 및 오케스트레이션
- **Caddy** - 리버스 프록시 및 HTTPS

---

## 🏁 시작하기

### 사전 요구사항

- Python 3.11 이상
- PostgreSQL 16 이상
- Docker 및 Docker Compose (선택사항)

### 로컬 개발 환경 설정

#### 1. 저장소 클론

```bash
git clone <repository-url>
cd backend
```

#### 2. 가상 환경 생성 및 활성화

```bash
# 가상 환경 생성
python -m venv venv

# 활성화 (macOS/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

#### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

#### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DATABASE_URL_RUNTIME=postgresql://user:password@db:5432/dbname

# JWT 인증
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 설정
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 환경 설정
ENVIRONMENT=development

# Google OAuth (선택사항)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# SendGrid (비밀번호 재설정용, 선택사항)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@example.com

# PostgreSQL (Docker 사용 시)
POSTGRES_DB=decision_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

#### 5. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head
```

#### 6. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn main:app --reload

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc

### Docker를 사용한 실행

#### 1. 환경 변수 설정

`.env` 파일을 생성하고 위의 환경 변수들을 설정하세요.

#### 2. Docker Compose로 실행

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 서비스 중지
docker-compose down
```

#### 3. 로컬 개발용 Docker Compose

```bash
# 로컬 개발용 (볼륨 마운트)
docker-compose -f docker-compose.local.yml up -d
```

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── routers/              # HTTP 라우터 (API 엔드포인트)
│   │   ├── auth.py          # 인증 관련 라우터
│   │   ├── event/           # 이벤트 관련 라우터
│   │   │   ├── home.py      # 홈 화면
│   │   │   ├── creation.py  # 이벤트 생성
│   │   │   ├── entry.py     # 이벤트 입장
│   │   │   ├── detail.py    # 이벤트 상세
│   │   │   ├── setting.py   # 이벤트 설정
│   │   │   ├── comment.py   # 코멘트
│   │   │   ├── vote.py      # 투표
│   │   │   └── stream.py    # 실시간 스트림 (SSE)
│   │   └── dev/             # 개발용 라우터
│   │
│   ├── services/            # 비즈니스 로직 레이어
│   │   ├── auth.py          # 인증 서비스
│   │   ├── event/           # 이벤트 관련 서비스
│   │   │   ├── base.py      # 공통 서비스 (EventBaseService)
│   │   │   ├── home_service.py
│   │   │   ├── creation_service.py
│   │   │   ├── detail_service.py
│   │   │   └── ...
│   │   ├── idempotency_service.py  # 멱등성 관리
│   │   └── notification_service.py # 알림 서비스
│   │
│   ├── repositories/        # 데이터 접근 레이어
│   │   ├── auth.py          # 인증 관련 리포지토리
│   │   ├── event_repository.py
│   │   ├── content/         # 콘텐츠 관련 리포지토리
│   │   ├── proposal/        # 제안 관련 리포지토리
│   │   └── vote_repository.py
│   │
│   ├── models/              # SQLAlchemy ORM 모델
│   │   ├── auth.py          # 사용자, 인증 모델
│   │   ├── event.py         # 이벤트, 멤버십 모델
│   │   ├── content.py       # 전제, 기준 모델
│   │   ├── proposal.py      # 제안 모델
│   │   ├── vote.py          # 투표 모델
│   │   ├── comment.py       # 코멘트 모델
│   │   ├── idempotency.py   # 멱등성 모델
│   │   └── outbox.py        # Outbox 패턴 모델
│   │
│   ├── schemas/             # Pydantic 스키마 (요청/응답)
│   │   ├── auth.py
│   │   └── event/
│   │
│   ├── dependencies/        # 의존성 주입
│   │   ├── auth.py          # 인증 의존성
│   │   ├── repositories.py  # 리포지토리 의존성
│   │   ├── services.py      # 서비스 의존성
│   │   ├── error_handlers.py # 에러 핸들러
│   │   └── idempotency.py   # 멱등성 처리
│   │
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── db.py                # 데이터베이스 연결 설정
│   └── utils/               # 유틸리티 함수
│       ├── security.py      # 보안 관련 유틸
│       ├── google_auth.py   # Google 인증 유틸
│       ├── mailer.py        # 이메일 발송 유틸
│       └── transaction.py   # 트랜잭션 유틸
│
├── migrations/              # Alembic 마이그레이션 파일
│   └── versions/
│
├── scripts/                # 유틸리티 스크립트
│   ├── test/               # 테스트 스크립트
│   └── db_bootstrap.sh     # 데이터베이스 초기화
│
├── docs/                   # 문서
│   ├── api_spec/           # API 스펙 문서
│   ├── db/                 # 데이터베이스 스키마 문서
│   └── ...
│
├── main.py                 # FastAPI 애플리케이션 진입점
├── requirements.txt        # Python 의존성
├── Dockerfile              # Docker 이미지 빌드 파일
├── docker-compose.yml      # Docker Compose 설정
├── alembic.ini             # Alembic 설정
└── Caddyfile               # Caddy 리버스 프록시 설정
```

### 아키텍처 패턴

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)**를 따릅니다:

```
Router Layer (HTTP 요청/응답)
    ↓
Service Layer (비즈니스 로직)
    ↓
Repository Layer (데이터 접근)
    ↓
Model Layer (ORM 모델)
    ↓
Database (PostgreSQL)
```

각 레이어는 명확한 책임을 가지며, 의존성 주입을 통해 느슨하게 결합되어 있습니다.

---

## 🔐 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DATABASE_URL` | 로컬 개발용 데이터베이스 URL | `postgresql://user:pass@localhost:5432/dbname` |
| `DATABASE_URL_RUNTIME` | Docker 환경용 데이터베이스 URL | `postgresql://user:pass@db:5432/dbname` |
| `SECRET_KEY` | JWT 토큰 서명용 시크릿 키 | `your-secret-key-here` |
| `ALGORITHM` | JWT 알고리즘 | `HS256` |

### 선택적 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 만료 시간 (분) | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 만료 시간 (일) | `7` |
| `CORS_ORIGINS` | CORS 허용 오리진 (쉼표로 구분) | `*` |
| `ENVIRONMENT` | 실행 환경 (`development`, `production`) | `development` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | - |
| `SENDGRID_API_KEY` | SendGrid API 키 (비밀번호 재설정용) | - |
| `SENDGRID_FROM_EMAIL` | 발신자 이메일 주소 | - |

---

## 🗄 데이터베이스

### 마이그레이션 관리

Alembic을 사용하여 데이터베이스 스키마를 관리합니다.

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history
```

### 주요 테이블

- **users**: 사용자 정보
- **events**: 이벤트 정보
- **memberships**: 이벤트 멤버십 정보
- **assumptions**: 전제 조건
- **criteria**: 평가 기준
- **options**: 선택지
- **proposals**: 제안 (전제/기준/결론)
- **votes**: 투표 정보
- **comments**: 코멘트
- **idempotency_keys**: 멱등성 키 관리
- **outbox**: Outbox 패턴을 위한 이벤트 저장소

자세한 스키마 정보는 `docs/db/db_schema.md`를 참조하세요.

---

## 📚 API 문서

### 자동 생성 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 API 엔드포인트

#### 인증 API (`/auth`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 |
| POST | `/auth/google` | Google 로그인 |
| POST | `/auth/refresh` | 토큰 갱신 |
| POST | `/auth/logout` | 로그아웃 |
| GET | `/auth/me` | 현재 사용자 정보 |
| PATCH | `/auth/me/name` | 사용자 이름 업데이트 |
| POST | `/auth/password-reset/request` | 비밀번호 재설정 요청 |
| POST | `/auth/password-reset/confirm` | 비밀번호 재설정 확인 |

#### 이벤트 API (`/v1`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/v1/events/participated` | 참가한 이벤트 목록 |
| POST | `/v1/events` | 이벤트 생성 |
| POST | `/v1/events/entry` | 이벤트 입장 |
| GET | `/v1/events/{event_id}/overview` | 이벤트 오버뷰 |
| GET | `/v1/events/{event_id}` | 이벤트 상세 |
| GET | `/v1/events/{event_id}/stream` | 실시간 업데이트 스트림 (SSE) |
| POST | `/v1/events/{event_id}/assumption-proposals` | 전제 제안 생성 |
| POST | `/v1/events/{event_id}/criteria-proposals` | 기준 제안 생성 |
| POST | `/v1/events/{event_id}/criteria/{criterion_id}/conclusion-proposals` | 결론 제안 생성 |
| POST | `/v1/events/{event_id}/votes` | 투표 생성/업데이트 |
| GET | `/v1/events/{event_id}/votes/result` | 투표 결과 조회 |

자세한 API 스펙은 `docs/api_spec/api_spec.md`를 참조하세요.

### 인증 방식

대부분의 API는 JWT Bearer Token 인증이 필요합니다:

```bash
# 요청 헤더에 토큰 포함
Authorization: Bearer <access_token>
```

Refresh Token은 HTTP-only 쿠키로 전달됩니다.

---

## 👨‍💻 개발 가이드

### 코딩 컨벤션

- **Python 스타일**: PEP 8 준수
- **타입 힌팅**: 가능한 모든 함수에 타입 힌팅 사용
- **문서화**: 주요 함수와 클래스에 docstring 작성

### 새로운 기능 추가하기

1. **모델 정의** (`app/models/`)
   - SQLAlchemy 모델 생성
   - 필요시 마이그레이션 생성

2. **스키마 정의** (`app/schemas/`)
   - Pydantic 스키마 생성 (요청/응답)

3. **리포지토리 구현** (`app/repositories/`)
   - 데이터 접근 로직 구현

4. **서비스 구현** (`app/services/`)
   - 비즈니스 로직 구현

5. **라우터 구현** (`app/routers/`)
   - API 엔드포인트 정의

6. **의존성 등록** (`app/dependencies/`)
   - 필요한 의존성 함수 등록

### 에러 처리

커스텀 예외는 `app/exceptions.py`에 정의되어 있으며, `app/dependencies/error_handlers.py`에서 전역적으로 처리됩니다.

### 트랜잭션 관리

서비스 레이어에서 데이터베이스 트랜잭션을 관리합니다:

```python
# 트랜잭션 시작
self.db.begin()

try:
    # 작업 수행
    self.db.commit()
except Exception:
    self.db.rollback()
    raise
```

### 멱등성 처리

중복 요청 방지를 위해 멱등성 키를 사용합니다. 클라이언트는 `Idempotency-Key` 헤더를 포함하여 요청을 보낼 수 있습니다.

---

## 🚢 배포

### Docker를 사용한 배포

1. **환경 변수 설정**
   - `.env` 파일에 프로덕션 환경 변수 설정

2. **Docker 이미지 빌드**
   ```bash
   docker build -t decision-backend .
   ```

3. **Docker Compose로 실행**
   ```bash
   docker-compose up -d
   ```

### Caddy 리버스 프록시

프로젝트에는 Caddy를 사용한 리버스 프록시 설정이 포함되어 있습니다. `Caddyfile`을 수정하여 도메인 및 HTTPS 설정을 구성할 수 있습니다.

---

## 🧪 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
python scripts/run_all_tests.py

# 특정 테스트 실행
python scripts/test/test_auth.py
```

### 테스트 시나리오

테스트 시나리오는 `docs/test-scenario.md`에 문서화되어 있습니다.

---

## 📖 추가 문서

- [개발자 가이드](docs/developer_guide.md) - 개발 워크플로우 및 가이드
- [아키텍처 문서](docs/architecturing.md) - 시스템 아키텍처 및 설계 원칙
- [API 스펙](docs/api_spec/api_spec.md) - 상세 API 명세서
- [데이터베이스 스키마](docs/db/db_schema.md) - 데이터베이스 스키마 문서
- [프론트엔드 실시간 가이드](docs/frontend_realtime_guide.md) - SSE 연동 가이드

---

## 🤝 기여하기

1. 이슈를 생성하거나 기존 이슈를 확인하세요
2. 새로운 브랜치를 생성하세요 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성하세요

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

