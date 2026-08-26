import json
from collections import Counter

from sqlalchemy.orm import Session

from agentscope_server.models import (
    Diagnostic,
    DiagnosticSeverity,
    Event,
    EventType,
    Trace,
)


def _tool_signature(event: Event) -> str:
    arguments = event.payload.get("arguments", event.payload.get("input", {}))
    return f"{event.name}:{json.dumps(arguments, sort_keys=True, default=str)}"


def detect_diagnostics(session: Session, trace: Trace) -> list[Diagnostic]:
    """Run deterministic, explainable checks over a persisted trace."""
    diagnostics: list[Diagnostic] = []
    events = sorted(trace.events, key=lambda event: (event.sequence, event.timestamp))
    tool_calls = [event for event in events if event.type == EventType.TOOL_CALL]
    signatures = Counter(_tool_signature(event) for event in tool_calls)

    repeated = [(signature, count) for signature, count in signatures.items() if count >= 3]
    if repeated:
        signature, count = max(repeated, key=lambda item: item[1])
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="repeated_tool_call",
                severity=DiagnosticSeverity.WARNING,
                title="Repeated identical tool call",
                explanation=(
                    "The same tool and arguments were observed at least three times. "
                    "This may indicate a retry loop without state change."
                ),
                evidence={"signature": signature, "occurrences": count},
            )
        )

    error_events = [event for event in events if event.type == EventType.ERROR]
    if error_events:
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="tool_error",
                severity=DiagnosticSeverity.WARNING,
                title="Execution error recorded",
                explanation="One or more error events were emitted during the trace.",
                evidence={
                    "count": len(error_events),
                    "events": [event.name for event in error_events[:5]],
                },
            )
        )

    malformed = [
        event
        for event in tool_calls
        if "arguments" in event.payload and not isinstance(event.payload["arguments"], dict)
    ]
    if malformed:
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="malformed_arguments",
                severity=DiagnosticSeverity.CRITICAL,
                title="Malformed tool arguments",
                explanation="A tool call supplied arguments in a non-object format.",
                evidence={"events": [event.name for event in malformed]},
            )
        )

    context_sizes = [
        event.input_tokens for event in events if event.type == EventType.MODEL_REQUEST
    ]
    has_context_growth = (
        len(context_sizes) >= 3
        and context_sizes[-1] >= 8_000
        and context_sizes[-1] > context_sizes[0] * 2
    )
    if has_context_growth:
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="context_growth",
                severity=DiagnosticSeverity.WARNING,
                title="Excessive context growth",
                explanation="Model input tokens more than doubled and exceeded 8,000 tokens.",
                evidence={
                    "first_input_tokens": context_sizes[0],
                    "last_input_tokens": context_sizes[-1],
                },
            )
        )

    if trace.duration_ms >= 60_000:
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="slow_trace",
                severity=DiagnosticSeverity.INFO,
                title="Unusually slow execution",
                explanation="The trace duration exceeded the V1 sixty-second threshold.",
                evidence={"duration_ms": trace.duration_ms, "threshold_ms": 60_000},
            )
        )

    if float(trace.estimated_cost) >= 0.10:
        diagnostics.append(
            Diagnostic(
                trace=trace,
                type="expensive_trace",
                severity=DiagnosticSeverity.INFO,
                title="Unusually expensive execution",
                explanation="Estimated model cost exceeded the V1 ten-cent threshold.",
                evidence={"estimated_cost": float(trace.estimated_cost), "threshold": 0.10},
            )
        )

    session.add_all(diagnostics)
    return diagnostics
