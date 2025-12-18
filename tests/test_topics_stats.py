import httpx, os, uuid, time

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_topics_counts():
    tid = str(uuid.uuid4())
    e = {"topic": tid, "event_id": tid, "timestamp":"2025-05-05T00:00:00Z","source":"t","payload":{"z":1}}
    httpx.post(f"{BASE}/publish", json=e)
    time.sleep(1.0)
    stats = httpx.get(f"{BASE}/stats").json()
    assert "topics" in stats and isinstance(stats["topics"], dict)
    assert stats["topics"].get(tid, 0) >= 1
