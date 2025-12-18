import httpx, os

def test_health(agg_base=os.getenv("AGG_BASE","http://aggregator:8080")):
    r = httpx.get(f"{agg_base}/healthz", timeout=5.0)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
