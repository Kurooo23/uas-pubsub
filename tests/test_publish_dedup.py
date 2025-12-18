import httpx, uuid, os, time

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def make(topic, eid):
    return {
        "topic": topic,
        "event_id": str(eid),
        "timestamp": "2025-01-01T00:00:00Z",
        "source": "test",
        "payload": {"x": 1},
    }

def test_dedup_basic():
    eid = uuid.uuid4()
    batch = [make("t", eid) for _ in range(5)]
    r = httpx.post(f"{BASE}/publish", json=batch, timeout=10)
    assert r.status_code == 200
    time.sleep(1.0)
    stats = httpx.get(f"{BASE}/stats").json()
    assert stats["received"] >= 5
    assert stats["unique_processed"] >= 1
    assert stats["duplicate_dropped"] >= 4
