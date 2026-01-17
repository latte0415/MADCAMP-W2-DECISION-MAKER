#!/usr/bin/env bash
set -euo pipefail
set -euo pipefail

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"

DB_CONT="${DB_CONT:-db}"

ADMIN_EMAIL="${ADMIN_EMAIL:-admin@test.local}"
USER1_EMAIL="${USER1_EMAIL:-user1@test.local}"
USER2_EMAIL="${USER2_EMAIL:-user2@test.local}"

docker compose exec "${DB_CONT}" sh -lc "
psql -v ON_ERROR_STOP=1 -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" <<SQL
-- UUID 생성 함수 사용을 위해 pgcrypto 활성화
CREATE EXTENSION IF NOT EXISTS pgcrypto;

WITH admin AS (
  INSERT INTO users (id, email, password_hash, is_active)
  VALUES (gen_random_uuid(), '${ADMIN_EMAIL}', NULL, true)
  ON CONFLICT (email) DO UPDATE SET is_active = true
  RETURNING id
),
user1 AS (
  INSERT INTO users (id, email, password_hash, is_active)
  VALUES (gen_random_uuid(), '${USER1_EMAIL}', NULL, true)
  ON CONFLICT (email) DO UPDATE SET is_active = true
  RETURNING id
),
user2 AS (
  INSERT INTO users (id, email, password_hash, is_active)
  VALUES (gen_random_uuid(), '${USER2_EMAIL}', NULL, true)
  ON CONFLICT (email) DO UPDATE SET is_active = true
  RETURNING id
),
id_admin AS (
  INSERT INTO user_identities (id, user_id, provider, provider_user_id, email)
  SELECT gen_random_uuid(), id, 'local', '${ADMIN_EMAIL}', '${ADMIN_EMAIL}' FROM admin
  ON CONFLICT (provider, provider_user_id) DO NOTHING
),
id_user1 AS (
  INSERT INTO user_identities (id, user_id, provider, provider_user_id, email)
  SELECT gen_random_uuid(), id, 'local', '${USER1_EMAIL}', '${USER1_EMAIL}' FROM user1
  ON CONFLICT (provider, provider_user_id) DO NOTHING
),
id_user2 AS (
  INSERT INTO user_identities (id, user_id, provider, provider_user_id, email)
  SELECT gen_random_uuid(), id, 'local', '${USER2_EMAIL}', '${USER2_EMAIL}' FROM user2
  ON CONFLICT (provider, provider_user_id) DO NOTHING
)
SELECT
  (SELECT id FROM admin) AS admin_id,
  (SELECT id FROM user1) AS user1_id,
  (SELECT id FROM user2) AS user2_id;
SQL
" | awk '
  $1 ~ /^[0-9a-fA-F-]{36}$/ && $2 ~ /^[0-9a-fA-F-]{36}$/ && $3 ~ /^[0-9a-fA-F-]{36}$/ {
    print "admin_id=" $1
    print "user1_id=" $2
    print "user2_id=" $3
  }
'