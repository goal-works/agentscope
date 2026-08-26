import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentscope_server.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class TraceStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class SpanType(StrEnum):
    AGENT = "agent"
    MODEL = "model"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    CUSTOM = "custom"


class EventType(StrEnum):
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RETRIEVAL = "retrieval"
    LOG = "log"
    ERROR = "error"
    FINAL_OUTPUT = "final_output"


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    agents: Mapped[list["Agent"]] = relationship(back_populates="project")
    traces: Mapped[list["Trace"]] = relationship(back_populates="project")


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_agent_project_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    key: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Project] = relationship(back_populates="agents")
    traces: Mapped[list["Trace"]] = relationship(back_populates="agent")


class Trace(TimestampMixin, Base):
    __tablename__ = "traces"
    __table_args__ = (UniqueConstraint("project_id", "external_id", name="uq_trace_external"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_id: Mapped[str] = mapped_column(String(160), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    status: Mapped[TraceStatus] = mapped_column(Enum(TraceStatus), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    final_result: Mapped[Any | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    trace_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    project: Mapped[Project] = relationship(back_populates="traces")
    agent: Mapped[Agent] = relationship(back_populates="traces")
    spans: Mapped[list["Span"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )
    diagnostics: Mapped[list["Diagnostic"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )


class Span(Base):
    __tablename__ = "spans"
    __table_args__ = (UniqueConstraint("trace_id", "external_id", name="uq_span_external"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_id: Mapped[str] = mapped_column(String(160))
    trace_id: Mapped[str] = mapped_column(ForeignKey("traces.id"), index=True)
    parent_span_id: Mapped[str | None] = mapped_column(ForeignKey("spans.id"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    type: Mapped[SpanType] = mapped_column(Enum(SpanType), index=True)
    status: Mapped[TraceStatus] = mapped_column(Enum(TraceStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    input: Mapped[Any | None] = mapped_column(JSON)
    output: Mapped[Any | None] = mapped_column(JSON)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    trace: Mapped[Trace] = relationship(back_populates="spans")
    parent: Mapped["Span | None"] = relationship(remote_side="Span.id", back_populates="children")
    children: Mapped[list["Span"]] = relationship(back_populates="parent")
    events: Mapped[list["Event"]] = relationship(back_populates="span")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("trace_id", "sequence", name="uq_event_sequence"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_id: Mapped[str] = mapped_column(String(160))
    trace_id: Mapped[str] = mapped_column(ForeignKey("traces.id"), index=True)
    span_id: Mapped[str | None] = mapped_column(ForeignKey("spans.id"), index=True)
    type: Mapped[EventType] = mapped_column(Enum(EventType), index=True)
    name: Mapped[str] = mapped_column(String(180))
    sequence: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))

    trace: Mapped[Trace] = relationship(back_populates="events")
    span: Mapped[Span | None] = relationship(back_populates="events")


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    trace_id: Mapped[str] = mapped_column(ForeignKey("traces.id"), index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[DiagnosticSeverity] = mapped_column(Enum(DiagnosticSeverity))
    title: Mapped[str] = mapped_column(String(180))
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    trace: Mapped[Trace] = relationship(back_populates="diagnostics")
