# 실패 시 즉시 중단
$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# .env 로드
# ------------------------------------------------------------
if (Test-Path ".env") {
    Get-Content ".env" |
        Where-Object { $_ -and -not $_.StartsWith("#") } |
        ForEach-Object {
            $parts = $_ -split "=", 2
            if ($parts.Count -eq 2) {
                $name  = $parts[0].Trim()
                $value = $parts[1].Trim()

                # PowerShell 5.1: dynamic env var name needs Env:\ drive
                Set-Item -Path ("Env:\{0}" -f $name) -Value $value
            }
        }
}

# ------------------------------------------------------------
# 필수 환경변수 체크
# ------------------------------------------------------------
$requiredVars = @(
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "APP_RUNTIME_PASSWORD"
)

foreach ($var in $requiredVars) {
    $val = Get-Item -Path ("Env:\{0}" -f $var) -ErrorAction SilentlyContinue |
           Select-Object -ExpandProperty Value -ErrorAction SilentlyContinue

    if ([string]::IsNullOrWhiteSpace($val)) {
        throw "$var is required"
    }
}

# ------------------------------------------------------------
# 변수 설정
# ------------------------------------------------------------
$OWNER_ROLE   = $env:POSTGRES_USER
$DB_CONT      = if ([string]::IsNullOrWhiteSpace($env:DB_CONT)) { "db" } else { [string]$env:DB_CONT }
$RUNTIME_ROLE = if ([string]::IsNullOrWhiteSpace($env:RUNTIME_ROLE)) { "app_runtime" } else { [string]$env:RUNTIME_ROLE }
$SCHEMA_NAME  = if ([string]::IsNullOrWhiteSpace($env:SCHEMA_NAME)) { "public" } else { [string]$env:SCHEMA_NAME }

# SQL 문자열용 비밀번호 escape ( ' → '' )
$APP_RUNTIME_PASSWORD_SQL = $env:APP_RUNTIME_PASSWORD -replace "'", "''"

Write-Host "[db_bootstrap] owner=$OWNER_ROLE runtime=$RUNTIME_ROLE db=$($env:POSTGRES_DB)"

# ------------------------------------------------------------
# SQL 생성 (PowerShell 확장 방지 + 변수 삽입)
# ------------------------------------------------------------
$sql = @'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{0}') THEN
    CREATE ROLE {0} LOGIN PASSWORD '{1}';
  ELSE
    ALTER ROLE {0} WITH PASSWORD '{1}';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE {2} TO {0};
GRANT USAGE ON SCHEMA {3} TO {0};

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA {3}
TO {0};

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA {3}
TO {0};

ALTER DEFAULT PRIVILEGES IN SCHEMA {3}
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {0};

ALTER DEFAULT PRIVILEGES IN SCHEMA {3}
  GRANT USAGE, SELECT ON SEQUENCES TO {0};
'@ -f $RUNTIME_ROLE, $APP_RUNTIME_PASSWORD_SQL, $env:POSTGRES_DB, $SCHEMA_NAME

# ------------------------------------------------------------
# docker compose exec → psql 실행 (STDIN으로 SQL 전달)
# ------------------------------------------------------------
$psqlArgs = @(
  "compose", "exec", "-T", $DB_CONT,
  "psql",
  "-v", "ON_ERROR_STOP=1",
  "-U", $OWNER_ROLE,
  "-d", $env:POSTGRES_DB
)

$sql | docker @psqlArgs

Write-Host "[db_bootstrap] done"
