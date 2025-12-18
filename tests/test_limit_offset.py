import httpx, os

BASE = os.getenv("AGG_BASE","http://aggregator:8080")

def test_limit_offset_params():
    r = httpx.get(f"{BASE}/events", params={"limit": 5, "offset": 0}, timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
