import httpx, os, uuid

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_response_contains_counts():
    evs = [{"topic":"cnt","event_id":str(uuid.uuid4()),"timestamp":"2025-06-06T00:00:00Z","source":"t","payload":{"k":1}} for _ in range(3)]
    r = httpx.post(f"{BASE}/publish", json=evs, timeout=10)
    assert r.status_code == 200
    js = r.json()
    assert js["accepted"] == 3
    assert js["enqueued"] == 3
