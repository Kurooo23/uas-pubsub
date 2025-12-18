import httpx, os

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_publish_invalid_schema():
    bad = {"topic": "", "event_id": ""}
    r = httpx.post(f"{BASE}/publish", json=bad, timeout=10)
    assert r.status_code == 422
