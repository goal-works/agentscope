from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from agentscope_server.core.ingestion import ingest_trace
from agentscope_server.models import EventType, SpanType, TraceStatus
from agentscope_server.schemas import EventIn, SpanIn, TraceIn


def _event(
    trace_number: int,
    sequence: int,
    timestamp: datetime,
    event_type: EventType,
    name: str,
    *,
    span: str = "root",
    payload: dict | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost: str = "0",
) -> EventIn:
    return EventIn(
        external_id=f"seed-{trace_number}-event-{sequence}",
        span_external_id=f"seed-{trace_number}-{span}",
        type=event_type,
        name=name,
        sequence=sequence,
        timestamp=timestamp,
        payload=payload or {},
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=Decimal(cost),
    )


def _seed_payload(trace_number: int, scenario: str) -> TraceIn:
    started_at = datetime(2026, 8, 20, 14, trace_number * 7, tzinfo=UTC)
    duration_seconds = 94 if scenario == "expensive" else 18 + trace_number * 3
    ended_at = started_at + timedelta(seconds=duration_seconds)
    status = TraceStatus.ERROR if scenario in {"malformed", "failed"} else TraceStatus.SUCCESS
    root_id = f"seed-{trace_number}-root"
    tool_id = f"seed-{trace_number}-tool"
    spans = [
        SpanIn(
            external_id=root_id,
            name="research-agent",
            type=SpanType.AGENT,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            input={"question": "Summarize the synthetic incident report."},
            output={"status": status.value},
        ),
        SpanIn(
            external_id=tool_id,
            parent_external_id=root_id,
            name="search_documents",
            type=SpanType.TOOL,
            status=TraceStatus.ERROR if scenario == "malformed" else TraceStatus.SUCCESS,
            started_at=started_at + timedelta(seconds=3),
            ended_at=started_at + timedelta(seconds=11),
            input={"collection": "synthetic-incidents"},
            output={"matches": 3},
        ),
    ]
    model_cost = "0.115" if scenario == "expensive" else "0.0085"
    first_context = 4_000 if scenario == "expensive" else 620
    events = [
        _event(
            trace_number,
            0,
            started_at + timedelta(seconds=1),
            EventType.MODEL_REQUEST,
            "plan-request",
            payload={"model": "synthetic-reasoner-v1"},
            input_tokens=first_context,
            cost=model_cost,
        ),
        _event(
            trace_number,
            1,
            started_at + timedelta(seconds=2),
            EventType.MODEL_RESPONSE,
            "plan-response",
            payload={"finish_reason": "tool_call"},
            output_tokens=180,
        ),
    ]

    arguments: object = {"query": "payment retry incident"}
    if scenario == "malformed":
        arguments = "{query: payment retry incident"
    call_count = 3 if scenario == "loop" else 1
    sequence = 2
    for call_index in range(call_count):
        events.append(
            _event(
                trace_number,
                sequence,
                started_at + timedelta(seconds=3 + call_index * 2),
                EventType.TOOL_CALL,
                "search_documents",
                span="tool",
                payload={"arguments": arguments},
            )
        )
        sequence += 1
        events.append(
            _event(
                trace_number,
                sequence,
                started_at + timedelta(seconds=4 + call_index * 2),
                EventType.TOOL_RESULT,
                "search_documents",
                span="tool",
                payload={"matches": 3, "attempt": call_index + 1},
            )
        )
        sequence += 1

    if scenario in {"recovery", "malformed", "failed"}:
        events.append(
            _event(
                trace_number,
                sequence,
                started_at + timedelta(seconds=12),
                EventType.ERROR,
                "tool-validation-error" if scenario == "malformed" else "upstream-timeout",
                span="tool",
                payload={"recoverable": scenario == "recovery"},
            )
        )
        sequence += 1

    if scenario == "expensive":
        for input_tokens in (6_500, 9_200):
            events.append(
                _event(
                    trace_number,
                    sequence,
                    started_at + timedelta(seconds=30 + sequence),
                    EventType.MODEL_REQUEST,
                    "analysis-request",
                    payload={"model": "synthetic-reasoner-v1"},
                    input_tokens=input_tokens,
                )
            )
            sequence += 1

    if status == TraceStatus.SUCCESS:
        events.append(
            _event(
                trace_number,
                sequence,
                ended_at - timedelta(seconds=1),
                EventType.FINAL_OUTPUT,
                "final-answer",
                payload={"result": "The retry storm followed a stale worker deployment."},
                output_tokens=240,
            )
        )

    names = {
        "success": "Incident research — successful",
        "recovery": "Incident research — recovered tool error",
        "loop": "Incident research — repeated search loop",
        "expensive": "Incident research — long context",
        "malformed": "Incident research — malformed tool call",
        "failed": "Incident research — failed final result",
    }
    return TraceIn(
        external_id=f"seed-trace-{trace_number}",
        project_slug="incident-research-demo",
        project_name="Incident Research Demo",
        agent_key="research-agent-v1",
        agent_name="Research Agent V1",
        name=names[scenario],
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        input={"question": "Summarize the synthetic incident report."},
        final_result=(
            {"summary": "The retry storm followed a stale worker deployment."}
            if status == TraceStatus.SUCCESS
            else None
        ),
        error_message="The agent did not produce a usable final result."
        if status == TraceStatus.ERROR
        else None,
        metadata={"dataset": "synthetic", "scenario": scenario},
        spans=spans,
        events=events,
    )


def seed_demo_data(session: Session) -> None:
    for index, scenario in enumerate(
        ["success", "recovery", "loop", "expensive", "malformed", "failed"],
        start=1,
    ):
        ingest_trace(session, _seed_payload(index, scenario))
