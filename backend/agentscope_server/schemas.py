from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agentscope_server.models import EventType, SpanType, TraceStatus


class SpanIn(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    parent_external_id: str | None = Field(default=None, max_length=160)
    name: str = Field(min_length=1, max_length=180)
    type: SpanType
    status: TraceStatus
    started_at: datetime
    ended_at: datetime | None = None
    input: Any | None = None
    output: Any | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.ended_at and self.ended_at < self.started_at:
            raise ValueError("span ended_at must not precede started_at")
        return self


class EventIn(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    span_external_id: str | None = Field(default=None, max_length=160)
    type: EventType
    name: str = Field(min_length=1, max_length=180)
    sequence: int = Field(ge=0)
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost: Decimal = Field(default=Decimal("0"), ge=0)


class TraceIn(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    project_slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")
    project_name: str = Field(min_length=1, max_length=120)
    agent_key: str = Field(min_length=1, max_length=120)
    agent_name: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    status: TraceStatus
    started_at: datetime
    ended_at: datetime | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    final_result: Any | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    spans: list[SpanIn] = Field(default_factory=list, max_length=500)
    events: list[EventIn] = Field(default_factory=list, max_length=2000)

    @model_validator(mode="after")
    def validate_graph(self):
        if self.ended_at and self.ended_at < self.started_at:
            raise ValueError("trace ended_at must not precede started_at")

        span_ids = [span.external_id for span in self.spans]
        if len(span_ids) != len(set(span_ids)):
            raise ValueError("span external_id values must be unique")

        known_spans = set(span_ids)
        parent_by_span = {
            span.external_id: span.parent_external_id for span in self.spans
        }
        for span in self.spans:
            if span.parent_external_id and span.parent_external_id not in known_spans:
                raise ValueError(f"unknown parent span: {span.parent_external_id}")
            if span.parent_external_id == span.external_id:
                raise ValueError("a span cannot be its own parent")

        for span_id in span_ids:
            ancestors: set[str] = set()
            current: str | None = span_id
            while current:
                if current in ancestors:
                    raise ValueError("span parent references must not contain a cycle")
                ancestors.add(current)
                current = parent_by_span[current]

        sequences = [event.sequence for event in self.events]
        if len(sequences) != len(set(sequences)):
            raise ValueError("event sequence values must be unique")
        for event in self.events:
            if event.span_external_id and event.span_external_id not in known_spans:
                raise ValueError(f"unknown event span: {event.span_external_id}")
        return self


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    name: str


class DiagnosticOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    severity: str
    title: str
    explanation: str
    evidence: dict[str, Any]


class SpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    parent_span_id: str | None
    name: str
    type: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int
    input: Any | None
    output: Any | None
    attributes: dict[str, Any]


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    span_id: str | None
    type: str
    name: str
    sequence: int
    timestamp: datetime
    payload: dict[str, Any]
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal


class TraceSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int
    total_tokens: int
    estimated_cost: Decimal
    error_message: str | None
    agent: AgentOut
    project: ProjectOut
    diagnostic_count: int = 0


class TraceDetailOut(TraceSummaryOut):
    input_tokens: int
    output_tokens: int
    input: dict[str, Any]
    final_result: Any | None
    trace_metadata: dict[str, Any]
    spans: list[SpanOut]
    events: list[EventOut]
    diagnostics: list[DiagnosticOut]
