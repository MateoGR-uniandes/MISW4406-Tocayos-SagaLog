from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from saga_tracker.config.db import db
from sqlalchemy.orm import Mapped, mapped_column

class SagaInstance(db.Model):
    __tablename__ = "saga_instance"
    saga_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    business_key: Mapped[str | None] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="InProgress")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_event_id: Mapped[str | None] = mapped_column(String(64))
    retries_total: Mapped[int] = mapped_column(Integer, default=0)

class SagaStep(db.Model):
    __tablename__ = "saga_step"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    saga_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    #causation_id: Mapped[str | None] = mapped_column(String(64))
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    service: Mapped[str] = mapped_column(String(64), nullable=False)
    step: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    #error_code: Mapped[str | None] = mapped_column(String(64))
    #error_msg: Mapped[str | None] = mapped_column(String(512))
    ts_event: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ts_ingested: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
