import httpx, os, time, uuid, threading

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def make(i):
    return {"topic":"cons","event_id":str(uuid.uuid4()),"timestamp":"2025-03-03T00:00:00Z","source":"t","payload":{"i":i}}

def test_stats_atomic_updates():
    def send():
        httpx.post(f"{BASE}/publish", json=[make(i) for i in range(30)], timeout=15)
    threads = [threading.Thread(target=send) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    time.sleep(1.5)
    stats = httpx.get(f"{BASE}/stats").json()
    assert stats["received"] >= 150
    assert stats["unique_processed"] >= 150
