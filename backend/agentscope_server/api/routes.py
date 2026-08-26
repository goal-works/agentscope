from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from agentscope_server.core.ingestion import ingest_trace
from agentscope_server.database import get_db
from agentscope_server.models import Agent, Event, EventType, Trace, TraceStatus
from agentscope_server.schemas import TraceDetailOut, TraceIn, TraceSummaryOut
from agentscope_server.serializers import trace_detail, trace_summary

router = APIRouter(prefix="/api")
DbSession = Annotated[Session, Depends(get_db)]


def _trace_options():
    return (
        selectinload(Trace.project),
        selectinload(Trace.agent),
        selectinload(Trace.spans),
        selectinload(Trace.events),
        selectinload(Trace.diagnostics),
    )


def _load_trace(session: Session, trace_id: str) -> Trace:
    trace = session.scalar(select(Trace).options(*_trace_options()).where(Trace.id == trace_id))
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/overview")
async def overview(session: DbSession) -> dict:
    traces = list(session.scalars(select(Trace).options(selectinload(Trace.events))))
    executions = len(traces)
    success_count = sum(trace.status == TraceStatus.SUCCESS for trace in traces)
    error_count = sum(trace.status == TraceStatus.ERROR for trace in traces)
    tool_names = session.execute(
        select(Event.name, func.count(Event.id).label("uses"))
        .where(Event.type == EventType.TOOL_CALL)
        .group_by(Event.name)
        .order_by(func.count(Event.id).desc(), Event.name)
        .limit(5)
    ).all()

    return {
        "executions": executions,
        "success_rate": round(success_count / executions, 4) if executions else 0,
        "error_rate": round(error_count / executions, 4) if executions else 0,
        "average_latency_ms": round(sum(trace.duration_ms for trace in traces) / executions)
        if executions
        else 0,
        "average_cost": round(sum(float(trace.estimated_cost) for trace in traces) / executions, 6)
        if executions
        else 0,
        "total_tokens": sum(trace.total_tokens for trace in traces),
        "common_tools": [{"name": name, "uses": uses} for name, uses in tool_names],
    }


@router.post(
    "/v1/traces",
    response_model=TraceDetailOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_trace(payload: TraceIn, response: Response, session: DbSession) -> dict:
    trace, created = ingest_trace(session, payload)
    if not created:
        response.status_code = status.HTTP_200_OK
    loaded = _load_trace(session, trace.id)
    return trace_detail(loaded)


@router.get("/traces", response_model=list[TraceSummaryOut])
async def list_traces(
    session: DbSession,
    agent: str | None = None,
    trace_status: Annotated[TraceStatus | None, Query(alias="status")] = None,
    min_duration_ms: Annotated[int | None, Query(ge=0)] = None,
    max_cost: Annotated[float | None, Query(ge=0)] = None,
    has_error: bool | None = None,
    tool: str | None = None,
) -> list[dict]:
    statement = select(Trace).options(*_trace_options()).order_by(Trace.started_at.desc())
    if agent:
        statement = statement.join(Trace.agent).where(Agent.key == agent)
    if trace_status:
        statement = statement.where(Trace.status == trace_status)
    if min_duration_ms is not None:
        statement = statement.where(Trace.duration_ms >= min_duration_ms)
    if max_cost is not None:
        statement = statement.where(Trace.estimated_cost <= max_cost)
    if has_error is True:
        statement = statement.where(Trace.status == TraceStatus.ERROR)
    if has_error is False:
        statement = statement.where(Trace.status != TraceStatus.ERROR)
    if tool:
        statement = statement.where(
            Trace.events.any(
                and_(Event.type == EventType.TOOL_CALL, Event.name == tool)
            )
        )
    traces = list(session.scalars(statement).unique())
    return [trace_summary(trace) for trace in traces]


@router.get("/traces/compare")
async def compare_traces(
    trace_ids: Annotated[list[str], Query(min_length=2, max_length=2)],
    session: DbSession,
) -> dict:
    traces = [_load_trace(session, trace_id) for trace_id in trace_ids]
    return {
        "traces": [trace_detail(trace) for trace in traces],
        "delta": {
            "duration_ms": traces[1].duration_ms - traces[0].duration_ms,
            "total_tokens": traces[1].total_tokens - traces[0].total_tokens,
            "estimated_cost": float(traces[1].estimated_cost - traces[0].estimated_cost),
            "tool_calls": sum(event.type == EventType.TOOL_CALL for event in traces[1].events)
            - sum(event.type == EventType.TOOL_CALL for event in traces[0].events),
            "errors": sum(event.type == EventType.ERROR for event in traces[1].events)
            - sum(event.type == EventType.ERROR for event in traces[0].events),
        },
    }


@router.get("/traces/{trace_id}", response_model=TraceDetailOut)
async def get_trace(trace_id: str, session: DbSession) -> dict:
    return trace_detail(_load_trace(session, trace_id))
