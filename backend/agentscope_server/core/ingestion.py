from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentscope_server.core.diagnostics import detect_diagnostics
from agentscope_server.models import Agent, Event, Project, Span, Trace
from agentscope_server.schemas import TraceIn


def _duration_ms(started_at: datetime, ended_at: datetime | None) -> int:
    if not ended_at:
        return 0
    return max(0, round((ended_at - started_at).total_seconds() * 1000))


def _get_or_create_project(session: Session, payload: TraceIn) -> Project:
    project = session.scalar(select(Project).where(Project.slug == payload.project_slug))
    if project:
        return project
    project = Project(name=payload.project_name, slug=payload.project_slug)
    session.add(project)
    session.flush()
    return project


def _get_or_create_agent(session: Session, project: Project, payload: TraceIn) -> Agent:
    agent = session.scalar(
        select(Agent).where(Agent.project_id == project.id, Agent.key == payload.agent_key)
    )
    if agent:
        return agent
    agent = Agent(
        project=project,
        key=payload.agent_key,
        name=payload.agent_name,
    )
    session.add(agent)
    session.flush()
    return agent


def ingest_trace(session: Session, payload: TraceIn) -> tuple[Trace, bool]:
    """Persist one complete trace graph and return (trace, created)."""
    project = _get_or_create_project(session, payload)
    existing = session.scalar(
        select(Trace).where(
            Trace.project_id == project.id,
            Trace.external_id == payload.external_id,
        )
    )
    if existing:
        return existing, False

    agent = _get_or_create_agent(session, project, payload)
    trace = Trace(
        external_id=payload.external_id,
        project=project,
        agent=agent,
        name=payload.name,
        status=payload.status,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        duration_ms=_duration_ms(payload.started_at, payload.ended_at),
        input=payload.input,
        final_result=payload.final_result,
        error_message=payload.error_message,
        trace_metadata=payload.metadata,
    )
    session.add(trace)
    session.flush()

    span_by_external_id: dict[str, Span] = {}
    span_payload_by_external_id = {span.external_id: span for span in payload.spans}
    for span_payload in payload.spans:
        span = Span(
            external_id=span_payload.external_id,
            trace=trace,
            name=span_payload.name,
            type=span_payload.type,
            status=span_payload.status,
            started_at=span_payload.started_at,
            ended_at=span_payload.ended_at,
            duration_ms=_duration_ms(span_payload.started_at, span_payload.ended_at),
            input=span_payload.input,
            output=span_payload.output,
            attributes=span_payload.attributes,
        )
        session.add(span)
        span_by_external_id[span_payload.external_id] = span
    session.flush()

    for external_id, span in span_by_external_id.items():
        parent_external_id = span_payload_by_external_id[external_id].parent_external_id
        if parent_external_id:
            span.parent = span_by_external_id[parent_external_id]

    for event_payload in sorted(payload.events, key=lambda event: event.sequence):
        session.add(
            Event(
                external_id=event_payload.external_id,
                trace=trace,
                span=(
                    span_by_external_id[event_payload.span_external_id]
                    if event_payload.span_external_id
                    else None
                ),
                type=event_payload.type,
                name=event_payload.name,
                sequence=event_payload.sequence,
                timestamp=event_payload.timestamp,
                payload=event_payload.payload,
                input_tokens=event_payload.input_tokens,
                output_tokens=event_payload.output_tokens,
                estimated_cost=event_payload.estimated_cost,
            )
        )

    session.flush()
    trace.input_tokens = sum(event.input_tokens for event in trace.events)
    trace.output_tokens = sum(event.output_tokens for event in trace.events)
    trace.total_tokens = trace.input_tokens + trace.output_tokens
    trace.estimated_cost = sum(
        (event.estimated_cost for event in trace.events),
        start=Decimal("0"),
    )
    detect_diagnostics(session, trace)
    session.commit()
    session.refresh(trace)
    return trace, True
