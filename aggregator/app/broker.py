from __future__ import annotations
import asyncio, json, logging
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .settings import (
    REDIS_URL, REDIS_STREAM, CONSUMER_GROUP,
    MAX_READ_COUNT, CLAIM_IDLE_MS,
)
from .db import session_scope, bump_counter
from .schemas import Event  # <- pakai schema untuk validasi

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")


class Worker:
    def __init__(self, app: FastAPI, name: str):
        self.app = app
        self.name = name
        self.r = redis.from_url(REDIS_URL, decode_responses=True)
        self._stopping = asyncio.Event()

    async def start(self):
        try:
            await self.r.xgroup_create(
                name=REDIS_STREAM,
                groupname=CONSUMER_GROUP,
                id="0-0",
                mkstream=True,
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        asyncio.create_task(self._claim_loop())
        await self._consume_loop()

    async def stop(self):
        self._stopping.set()
        await self.r.close()

    async def _claim_loop(self):
        while not self._stopping.is_set():
            try:
                await self.r.xautoclaim(
                    REDIS_STREAM,
                    CONSUMER_GROUP,
                    self.name,
                    min_idle_time=CLAIM_IDLE_MS,
                    start_id="0-0",
                    count=100,
                )
            except Exception:
                # cukup diam; akan diclaim lagi di iterasi berikutnya
                pass
            await asyncio.sleep(1.0)

    async def _consume_loop(self):
        while not self._stopping.is_set():
            try:
                resp = await self.r.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=self.name,
                    streams={REDIS_STREAM: ">"},
                    count=MAX_READ_COUNT,
                    block=200,
                )
                if not resp:
                    continue

                for stream, messages in resp:
                    for msg_id, fields in messages:
                        try:
                            await self._process_message(fields)
                            await self.r.xack(REDIS_STREAM, CONSUMER_GROUP, msg_id)
                        except Exception:
                            log.exception(
                                "process_message failed; leaving pending for re-delivery"
                            )
            except Exception:
                log.exception("consume_loop error")
                await asyncio.sleep(0.3)

    async def _process_message(self, fields: dict[str, Any]):
        raw = fields.get("json")
        if not raw:
            return

        # VALIDASI + KONVERSI: timestamp → datetime, payload → dict
        event = Event.model_validate_json(raw)

        async with session_scope() as session:
            # insert raw + upsert processed dalam SATU transaksi
            await self._insert_raw(session, event)
            inserted = await self._upsert_processed(session, event)
            if inserted:
                await bump_counter(session, "unique_processed", 1)
            else:
                await bump_counter(session, "duplicate_dropped", 1)
            # session_scope biasanya yang commit; kalau tidak, commit di sini
            await session.commit()

    async def _insert_raw(self, session: AsyncSession, e: Event):
        await session.execute(
            text(
                """
                INSERT INTO events_raw (topic, event_id, ts, source, payload)
                VALUES (:topic, :event_id, :ts, :source, :payload)
                """
            ),
            {
                "topic": e.topic,
                "event_id": e.event_id,
                "ts": e.timestamp,          # datetime → PG timestamptz
                "source": e.source,
                "payload": json.dumps(e.payload),  # string JSON → PG jsonb
            },
        )

    async def _upsert_processed(self, session: AsyncSession, e: Event) -> bool:
        res = await session.execute(
            text(
                """
                INSERT INTO processed_events (topic, event_id, ts, source, payload)
                VALUES (:topic, :event_id, :ts, :source, :payload)
                ON CONFLICT (topic, event_id) DO NOTHING
                RETURNING 1
                """
            ),
            {
                "topic": e.topic,
                "event_id": e.event_id,
                "ts": e.timestamp,
                "source": e.source,
                "payload": json.dumps(e.payload),
            },
        )
        row = res.first()
        return bool(row)
