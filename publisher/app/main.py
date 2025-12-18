from __future__ import annotations
import asyncio, random, uuid
from datetime import datetime, timezone
from typing import Any
import httpx
from .settings import TARGET_URL, EVENTS_TOTAL, DUP_RATE, TOPICS, QPS, BATCH_SIZE, SOURCE

def make_event(event_id: str | None = None) -> dict[str, Any]:
    if event_id is None:
        import uuid as _uuid
        event_id = str(_uuid.uuid4())
    topic = random.choice(TOPICS) if TOPICS else "default"
    return {
        "topic": topic,
        "event_id": event_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "source": SOURCE,
        "payload": {"value": random.randint(1, 1_000_000), "note": "demo"},
    }

async def run():
    print(f"[publisher] target={TARGET_URL} total={EVENTS_TOTAL} dup_rate={DUP_RATE} qps={QPS} batch={BATCH_SIZE}")
    unique_ids: list[str] = []
    sent = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while sent < EVENTS_TOTAL:
            batch = []
            to_send = min(BATCH_SIZE, EVENTS_TOTAL - sent)
            for _ in range(to_send):
                import random as _random
                if unique_ids and _random.random() < DUP_RATE:
                    dup_id = _random.choice(unique_ids)
                    batch.append(make_event(dup_id))
                else:
                    e = make_event()
                    unique_ids.append(e["event_id"])
                    batch.append(e)
            r = await client.post(TARGET_URL, json=batch)
            r.raise_for_status()
            sent += len(batch)
            await asyncio.sleep(max(len(batch) / QPS, 0.001))
    print(f"[publisher] done sent={sent}")

if __name__ == "__main__":
    asyncio.run(run())
