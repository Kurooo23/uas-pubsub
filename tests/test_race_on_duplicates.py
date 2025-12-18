import httpx, os, time, uuid, threading

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def body(eid):
    return {
        "topic":"race",
        "event_id":str(eid),
        "timestamp":"2025-04-04T00:00:00Z",
        "source":"t",
        "payload":{"ok":True},
    }

def test_parallel_duplicate_race():
    eid = uuid.uuid4()
    def send():
        httpx.post(f"{BASE}/publish", json=[body(eid) for _ in range(50)], timeout=10)
    threads = [threading.Thread(target=send) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    time.sleep(2.0)
    events = httpx.get(f"{BASE}/events", params={"topic":"race"}).json()
    count = sum(1 for e in events if e["event_id"] == str(eid))
    assert count == 1
