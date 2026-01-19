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
docker compose exec api sh -lc 'DATABASE_URL="$DATABASE_URL_OWNER" alembic revision --autogenerate -m "init schema"'

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
