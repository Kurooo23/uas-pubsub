from __future__ import annotations
import asyncio, json
from typing import Any, Optional
from fastapi import FastAPI, Body, HTTPException, Query
from pydantic import ValidationError
from datetime import datetime, timezone
import redis.asyncio as redis
from sqlalchemy import text
from .settings import REDIS_URL, REDIS_STREAM, WORKERS, CONSUMER_PREFIX, SERVICE_PORT
from .schemas import Event, PublishResponse, Stats
from .db import init_db, session_scope, bump_counter, get_counters
from .broker import Worker

app = FastAPI(title="UAS Pub-Sub Aggregator", version="1.0.0")
r = redis.from_url(REDIS_URL, decode_responses=True)
workers: list[Worker] = []
_started_at = datetime.now(tz=timezone.utc)

@app.on_event("startup")
async def _startup():
    await init_db()
    for i in range(WORKERS):
        w = Worker(app, name=f"{CONSUMER_PREFIX}-{i}")
        workers.append(w)
        asyncio.create_task(w.start())

@app.on_event("shutdown")
async def _shutdown():
    for w in workers:
        await w.stop()
    await r.close()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    try:
        pong = await r.ping()
        if not pong:
            raise RuntimeError("redis not ok")
    except Exception:
        raise HTTPException(status_code=503, detail="broker not ready")
    async with session_scope() as s:
        await s.execute(text("SELECT 1"))
    return {"status": "ready"}

def _normalize_payload(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        raw_events = body
    elif isinstance(body, dict):
        raw_events = body.get("events") if "events" in body else [body]
    else:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    events: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_events):
        try:
            e = Event.model_validate(item)
        except ValidationError as ve:
            raise HTTPException(status_code=422, detail={"index": idx, "error": json.loads(ve.json())})
        events.append(json.loads(e.model_dump_json()))
    return events

@app.post("/publish", response_model=PublishResponse)
async def publish(body: Any = Body(...)):
    events = _normalize_payload(body)
    pipe = r.pipeline()
    for e in events:
        pipe.xadd(REDIS_STREAM, {"json": json.dumps(e)}, maxlen=1000000, approximate=True)
    added = sum(1 for _ in await pipe.execute())
    async with session_scope() as s:
        await bump_counter(s, "received", added)
        await s.commit()
    return PublishResponse(accepted=len(events), enqueued=added)

@app.get("/events")
async def get_events(topic: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    async with session_scope() as s:
        if topic:
            res = await s.execute(text("""
                SELECT topic, event_id, ts, source, payload, processed_at
                FROM processed_events
                WHERE topic = :topic
                ORDER BY ts ASC
                LIMIT :limit OFFSET :offset
            """), {"topic": topic, "limit": limit, "offset": offset})
        else:
            res = await s.execute(text("""
                SELECT topic, event_id, ts, source, payload, processed_at
                FROM processed_events
                ORDER BY ts ASC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})
        rows = [dict(r._mapping) for r in res.fetchall()]
    return rows

@app.get("/stats", response_model=Stats)
async def stats():
    async with session_scope() as s:
        counters = await get_counters(s)
        res = await s.execute(text("""
            SELECT topic, COUNT(*)::bigint AS c
            FROM processed_events
            GROUP BY topic
        """))
        topics = {row[0]: int(row[1]) for row in res.fetchall()}
    uptime_seconds = (datetime.now(tz=timezone.utc) - _started_at).total_seconds()
    return Stats(
        received=counters.get("received", 0),
        unique_processed=counters.get("unique_processed", 0),
        duplicate_dropped=counters.get("duplicate_dropped", 0),
        topics=topics,
        uptime_seconds=uptime_seconds,
    )
