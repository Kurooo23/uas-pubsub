import httpx, os, time, uuid

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_batch_mixed_single_and_array():
    e1 = {"topic":"mix","event_id":str(uuid.uuid4()),"timestamp":"2025-02-02T00:00:00Z","source":"t","payload":{"a":1}}
    r1 = httpx.post(f"{BASE}/publish", json=e1)
    assert r1.status_code == 200
    e2 = {"topic":"mix","event_id":str(uuid.uuid4()),"timestamp":"2025-02-02T00:00:00Z","source":"t","payload":{"a":2}}
    e3 = {"topic":"mix","event_id":str(uuid.uuid4()),"timestamp":"2025-02-02T00:00:00Z","source":"t","payload":{"a":3}}
    r2 = httpx.post(f"{BASE}/publish", json=[e2,e3])
    assert r2.status_code == 200
    time.sleep(1.0)
    rows = httpx.get(f"{BASE}/events", params={"topic": "mix"}).json()
    ids = {e1["event_id"], e2["event_id"], e3["event_id"]}
    assert ids.issubset({r["event_id"] for r in rows})
