from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON
from sqlalchemy import TIMESTAMP, text, String

class Base(DeclarativeBase):
    pass

class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    topic: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))
    source: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

class EventRaw(Base):
    __tablename__ = "events_raw"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic: Mapped[str]
    event_id: Mapped[str]
    ts: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))
    source: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
