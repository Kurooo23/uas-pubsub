import os
TARGET_URL = os.getenv("TARGET_URL", "http://aggregator:8080/publish")
EVENTS_TOTAL = int(os.getenv("EVENTS_TOTAL", "20000"))
DUP_RATE = float(os.getenv("DUP_RATE", "0.3"))
TOPICS = [t.strip() for t in os.getenv("TOPICS", "auth,payments,orders,logs").split(",") if t.strip()]
QPS = int(os.getenv("QPS", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
SOURCE = os.getenv("SOURCE", "publisher-1")
