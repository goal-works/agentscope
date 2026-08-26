import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Literal
from urllib.request import Request, urlopen

TraceStatus = Literal["running", "success", "error"]
SpanType = Literal["agent", "model", "tool", "retrieval", "custom"]
EventType = Literal[
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "retrieval",
    "log",
    "error",
    "final_output",
]
Transport = Callable[[dict[str, Any]], dict[str, Any]]


def _now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class AgentScope:
    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8001/api",
        project_slug: str = "default-project",
        project_name: str = "Default Project",
        timeout_seconds: float = 5,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_slug = project_slug
        self.project_name = project_name
        self.timeout_seconds = timeout_seconds
        self._transport = transport or self._upload

    def trace(
        self,
        agent: str,
        *,
        name: str | None = None,
        agent_name: str | None = None,
        input: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "TraceContext":
        return TraceContext(
            client=self,
            agent_key=agent,
            agent_name=agent_name or agent.replace("-", " ").title(),
            name=name or agent,
            input=input or {},
            metadata=metadata or {},
        )

    def _upload(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}/v1/traces",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read())


class TraceContext:
    def __init__(
        self,
        *,
        client: AgentScope,
        agent_key: str,
        agent_name: str,
        name: str,
        input: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        self.client = client
        self.agent_key = agent_key
        self.agent_name = agent_name
        self.name = name
        self.input = input
        self.metadata = metadata
        self.external_id = str(uuid.uuid4())
        self.started_at: datetime | None = None
        self.ended_at: datetime | None = None
        self.status: TraceStatus = "running"
        self.final_result: Any | None = None
        self.error_message: str | None = None
        self.spans: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.response: dict[str, Any] | None = None
        self._active_spans: list[SpanContext] = []

    def __enter__(self) -> "TraceContext":
        self.started_at = _now()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.ended_at = _now()
        self.status = "error" if exc_value else "success"
        if exc_value:
            self.error_message = str(exc_value)
            self.event("error", "unhandled-exception", payload={"message": str(exc_value)})
        self.response = self.client._transport(self.to_payload())
        return False

    def span(
        self,
        name: str,
        *,
        type: SpanType = "custom",
        input: Any | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> "SpanContext":
        return SpanContext(
            trace=self,
            name=name,
            span_type=type,
            input=input,
            attributes=attributes or {},
        )

    def event(
        self,
        type: EventType,
        name: str,
        *,
        payload: dict[str, Any] | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost: Decimal | float | str = Decimal("0"),
    ) -> None:
        active_span = self._active_spans[-1] if self._active_spans else None
        self.events.append(
            {
                "external_id": str(uuid.uuid4()),
                "span_external_id": active_span.external_id if active_span else None,
                "type": type,
                "name": name,
                "sequence": len(self.events),
                "timestamp": _timestamp(_now()),
                "payload": payload or {},
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": str(estimated_cost),
            }
        )

    def set_result(self, result: Any) -> None:
        self.final_result = result
        self.event("final_output", "final-output", payload={"result": result})

    def to_payload(self) -> dict[str, Any]:
        if not self.started_at:
            raise RuntimeError("trace must be entered before serialization")
        return {
            "external_id": self.external_id,
            "project_slug": self.client.project_slug,
            "project_name": self.client.project_name,
            "agent_key": self.agent_key,
            "agent_name": self.agent_name,
            "name": self.name,
            "status": self.status,
            "started_at": _timestamp(self.started_at),
            "ended_at": _timestamp(self.ended_at),
            "input": self.input,
            "final_result": self.final_result,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "spans": self.spans,
            "events": self.events,
        }


class SpanContext:
    def __init__(
        self,
        *,
        trace: TraceContext,
        name: str,
        span_type: SpanType,
        input: Any | None,
        attributes: dict[str, Any],
    ) -> None:
        self.trace = trace
        self.name = name
        self.span_type = span_type
        self.input = input
        self.attributes = attributes
        self.output: Any | None = None
        self.external_id = str(uuid.uuid4())
        self.parent_external_id: str | None = None
        self.started_at: datetime | None = None

    def __enter__(self) -> "SpanContext":
        self.started_at = _now()
        if self.trace._active_spans:
            self.parent_external_id = self.trace._active_spans[-1].external_id
        self.trace._active_spans.append(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        ended_at = _now()
        if exc_value:
            self.trace.event("error", f"{self.name}-error", payload={"message": str(exc_value)})
        self.trace._active_spans.pop()
        self.trace.spans.append(
            {
                "external_id": self.external_id,
                "parent_external_id": self.parent_external_id,
                "name": self.name,
                "type": self.span_type,
                "status": "error" if exc_value else "success",
                "started_at": _timestamp(self.started_at),
                "ended_at": _timestamp(ended_at),
                "input": self.input,
                "output": self.output,
                "attributes": self.attributes,
            }
        )
        return False

    def set_output(self, output: Any) -> None:
        self.output = output
