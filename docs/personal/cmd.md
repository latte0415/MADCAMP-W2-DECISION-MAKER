서버 접속용
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-2.pem ubuntu@15.164.74.228


cd /srv/decision_app
초기화 (DB 하드 리셋 포함)
docker compose down -v
컨테이너 재 생성
docker compose up -d --build

API만 재배포하기
docker compose up -d --build api

마이그레이션
docker compose exec api sh -lc 'DATABASE_URL="$DATABASE_URL_OWNER" alembic revision --autogenerate -m "add sse to outbox table"'

docker compose exec api sh -lc 'DATABASE_URL="$DATABASE_URL_OWNER" alembic upgrade head'


로컬 빌드 + 실행
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build

컨테이너 상태 확인
docker compose ps

최근 로그
docker compose logs -n 200 api

실시간 로그
docker compose logs -f api


스크립트 실행
chmod +x scripts/db_bootstrap.sh
./scripts/db_bootstrap.sh

스크립트 실행
chmod +x scripts/seed_users.sh
./scripts/seed_users.sh

docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"select id, email from users order by created_at desc limit 5;\""

아예 초기화
docker compose down -v
docker compose up -d --build
./scripts/db_bootstrap.sh
docker compose exec api sh -lc 'DATABASE_URL="$DATABASE_URL_OWNER" alembic upgrade head'


# events 삭제 (events가 users를 참조하므로 먼저 삭제)
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"DELETE FROM events;\""

# users 삭제
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"DELETE FROM users;\""

# 현재 users 확인
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"SELECT id, email, created_at FROM users ORDER BY created_at DESC;\""

# 특정 이메일의 user 삭제 (관련 events도 함께 삭제됨)
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"DELETE FROM events WHERE admin_id IN (SELECT id FROM users WHERE email = 'example@email.com'); DELETE FROM users WHERE email = 'example@email.com';\""

# 특정 entrance_code의 event 삭제
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"DELETE FROM events WHERE entrance_code = 'ABC123';\""

# 현재 events 확인
docker compose exec db sh -lc "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"SELECT id, decision_subject, entrance_code, admin_id, created_at FROM events ORDER BY created_at DESC;\""