from agentscope_server.models import Trace


def trace_summary(trace: Trace) -> dict:
    return {
        "id": trace.id,
        "external_id": trace.external_id,
        "name": trace.name,
        "status": trace.status.value,
        "started_at": trace.started_at,
        "ended_at": trace.ended_at,
        "duration_ms": trace.duration_ms,
        "total_tokens": trace.total_tokens,
        "estimated_cost": trace.estimated_cost,
        "error_message": trace.error_message,
        "agent": {"id": trace.agent.id, "key": trace.agent.key, "name": trace.agent.name},
        "project": {
            "id": trace.project.id,
            "name": trace.project.name,
            "slug": trace.project.slug,
        },
        "diagnostic_count": len(trace.diagnostics),
    }


def trace_detail(trace: Trace) -> dict:
    summary = trace_summary(trace)
    summary.update(
        {
            "input_tokens": trace.input_tokens,
            "output_tokens": trace.output_tokens,
            "input": trace.input,
            "final_result": trace.final_result,
            "trace_metadata": trace.trace_metadata,
            "spans": [
                {
                    "id": span.id,
                    "external_id": span.external_id,
                    "parent_span_id": span.parent_span_id,
                    "name": span.name,
                    "type": span.type.value,
                    "status": span.status.value,
                    "started_at": span.started_at,
                    "ended_at": span.ended_at,
                    "duration_ms": span.duration_ms,
                    "input": span.input,
                    "output": span.output,
                    "attributes": span.attributes,
                }
                for span in sorted(trace.spans, key=lambda item: item.started_at)
            ],
            "events": [
                {
                    "id": event.id,
                    "external_id": event.external_id,
                    "span_id": event.span_id,
                    "type": event.type.value,
                    "name": event.name,
                    "sequence": event.sequence,
                    "timestamp": event.timestamp,
                    "payload": event.payload,
                    "input_tokens": event.input_tokens,
                    "output_tokens": event.output_tokens,
                    "estimated_cost": event.estimated_cost,
                }
                for event in sorted(trace.events, key=lambda item: item.sequence)
            ],
            "diagnostics": [
                {
                    "id": diagnostic.id,
                    "type": diagnostic.type,
                    "severity": diagnostic.severity.value,
                    "title": diagnostic.title,
                    "explanation": diagnostic.explanation,
                    "evidence": diagnostic.evidence,
                }
                for diagnostic in trace.diagnostics
            ],
        }
    )
    return summary
