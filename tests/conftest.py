import os
os.environ.setdefault("AGG_BASE", "http://localhost:8080")

import pytest
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

AGG_BASE = os.environ["AGG_BASE"]

@retry(stop=stop_after_attempt(60), wait=wait_fixed(0.5))
def wait_ready(base: str):
    r = httpx.get(f"{base}/readyz", timeout=5.0)
    r.raise_for_status()

@pytest.fixture(scope="session", autouse=True)
def ensure_ready():
    wait_ready(AGG_BASE)
    yield

@pytest.fixture(scope="session")
def agg_base():
    return AGG_BASE

@pytest.fixture
def client():
    return httpx.Client(base_url=AGG_BASE, timeout=30.0)
