import httpx, os

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_readyz():
    r = httpx.get(f"{BASE}/readyz", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
