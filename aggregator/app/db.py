from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker, AsyncConnection
)
from sqlalchemy import text
from .settings import DATABASE_URL, ISOLATION_LEVEL

# 1) engine tanpa pool_size/max_overflow
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS processed_events (
    topic TEXT NOT NULL,
    event_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (topic, event_id)
);

CREATE TABLE IF NOT EXISTS events_raw (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    event_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kv_counters (
    key TEXT PRIMARY KEY,
    value BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app_state (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version TEXT NOT NULL DEFAULT '1.0.0'
);

INSERT INTO app_state (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO kv_counters(key, value) VALUES
('received', 0),
('unique_processed', 0),
('duplicate_dropped', 0)
ON CONFLICT (key) DO NOTHING;
"""

async def _run_ddl(conn: AsyncConnection, sql: str) -> None:
    # 2) pecah per-statement lalu eksekusi dengan exec_driver_sql
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        await conn.exec_driver_sql(stmt)

@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

async def init_db() -> None:
    # Set default isolation level di luar explicit transaction (best-effort)
    async with engine.connect() as conn:
        try:
            await conn.exec_driver_sql(
                f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {ISOLATION_LEVEL}"
            )
        except Exception:
            pass
        await conn.commit()

    # Jalankan DDL dalam satu transaksi
    async with engine.begin() as conn:
        await _run_ddl(conn, MIGRATION_SQL)

async def bump_counter(session: AsyncSession, key: str, delta: int = 1) -> None:
    await session.execute(
        text("""
            INSERT INTO kv_counters(key, value) VALUES (:k, :d)
            ON CONFLICT (key) DO UPDATE SET value = kv_counters.value + EXCLUDED.value
        """),
        {"k": key, "d": delta},
    )

async def get_counters(session: AsyncSession) -> dict[str, int]:
    rows = (await session.execute(text("SELECT key, value FROM kv_counters"))).all()
    return {k: int(v) for k, v in rows}
