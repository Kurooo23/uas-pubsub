import os, asyncio, pytest, httpx
from tenacity import retry, stop_after_attempt, wait_fixed

AGG_BASE = os.getenv("AGG_BASE", "http://aggregator:8080")

@pytest.fixture(scope="session")
def agg_base():
    return AGG_BASE

@retry(stop=stop_after_attempt(40), wait=wait_fixed(0.5))
async def wait_ready(base):
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(f"{base}/readyz")
        r.raise_for_status()

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def ensure_ready(agg_base):
    await wait_ready(agg_base)
    yield

@pytest.fixture
def client():
    return httpx.Client(base_url=AGG_BASE, timeout=30.0)
