import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@storage:5432/uasdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://broker:6379/0")
REDIS_STREAM = os.getenv("REDIS_STREAM", "events_stream")
WORKERS = int(os.getenv("WORKERS", "4"))
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8080"))
CONSUMER_GROUP = "agg"
CONSUMER_PREFIX = os.getenv("CONSUMER_PREFIX", "w")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
CLAIM_IDLE_MS = int(os.getenv("CLAIM_IDLE_MS", "60000"))
MAX_READ_COUNT = int(os.getenv("MAX_READ_COUNT", "100"))
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@storage:5432/uasdb")
REDIS_URL = os.getenv("REDIS_URL", "redis://broker:6379/0")
REDIS_STREAM = os.getenv("REDIS_STREAM", "events_stream")
WORKERS = int(os.getenv("WORKERS", "4"))
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8080"))
CONSUMER_GROUP = "agg"
CONSUMER_PREFIX = os.getenv("CONSUMER_PREFIX", "w")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
CLAIM_IDLE_MS = int(os.getenv("CLAIM_IDLE_MS", "60000"))
MAX_READ_COUNT = int(os.getenv("MAX_READ_COUNT", "100"))
ISOLATION_LEVEL = os.getenv("ISOLATION_LEVEL", "READ COMMITTED")