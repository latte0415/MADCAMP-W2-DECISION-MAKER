import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

load_dotenv()

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델 메타데이터 연결 (중요)
from app.db import Base  # noqa: E402
# 모든 모델을 import하여 테이블과 ENUM 타입이 등록되도록 함
from app.models import (  # noqa: F401,E402
    auth,
    event,
    content,
    proposal,
    vote,
    comment,
    idempotency,
    outbox,
)

target_metadata = Base.metadata


def get_url() -> str:
    """
    Priority:
    1) DATABASE_URL (explicit override; useful for one-off exec)
    2) DATABASE_URL_OWNER (for migrations / DDL)
    3) DATABASE_URL_RUNTIME (fallback)
    """
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_URL_OWNER")
        or os.getenv("DATABASE_URL_RUNTIME")
        or ""
    ).strip()

    if not url:
        raise RuntimeError(
            "Database URL is not set. Set DATABASE_URL (preferred override) "
            "or DATABASE_URL_OWNER / DATABASE_URL_RUNTIME."
        )

    # 필요하면 아래 변환을 켜도 됨 (일단은 그대로 두는 걸 추천)
    # url = url.replace("postgresql+psycopg://", "postgresql://")

    return url

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config.set_main_option("sqlalchemy.url", get_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
