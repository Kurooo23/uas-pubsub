from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime

class Event(BaseModel):
    topic: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=1)
    timestamp: datetime
    source: str = Field(..., min_length=1)
    payload: dict[str, Any]

class PublishResponse(BaseModel):
    accepted: int
    enqueued: int

class Stats(BaseModel):
    received: int
    unique_processed: int
    duplicate_dropped: int
    topics: dict[str, int]
    uptime_seconds: float
