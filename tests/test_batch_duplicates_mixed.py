import httpx, os, time, uuid

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_batch_duplicates_mixed():
    eid = str(uuid.uuid4())
    base_event = {"topic":"mixdup","event_id": eid, "timestamp":"2025-01-01T00:00:00Z","source":"t","payload":{"n":1}}
    batch = [base_event] * 20
    r = httpx.post(f"{BASE}/publish", json=batch)
    assert r.status_code == 200

    # polling ringan sampai 6 detik total
    count = 0
    for _ in range(20):
        rows = httpx.get(f"{BASE}/events", params={"topic":"mixdup"}).json()
        count = sum(1 for e in rows if e["event_id"] == eid)
        if count == 1:
            break
        time.sleep(0.3)
    assert count == 1
