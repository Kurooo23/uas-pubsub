import httpx, uuid, time, os

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def make(topic, eid):
    return {
        "topic": topic,
        "event_id": str(eid),
        "timestamp": "2025-01-01T00:00:00Z",
        "source": "test",
        "payload": {"y": 2},
    }

def test_query_events_by_topic():
    eid = uuid.uuid4()
    httpx.post(f"{BASE}/publish", json=make("topic-A", eid))
    time.sleep(1.0)
    rows = httpx.get(f"{BASE}/events", params={"topic": "topic-A", "limit": 60}).json()
    assert any(r["event_id"] == str(eid) for r in rows)
