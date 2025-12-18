import os
import json
import httpx

BASE = os.getenv("AGG_BASE", "http://localhost:8080")

def test_show_stats_json():
    r = httpx.get(f"{BASE}/stats", timeout=10)
    r.raise_for_status()
    stats = r.json()

    # cetak JSON rapih
    print(json.dumps(stats, indent=2, sort_keys=True, ensure_ascii=False))

    # minimal assert biar tetap test yang valid
    assert "received" in stats
    assert "unique_processed" in stats
    assert "duplicate_dropped" in stats
