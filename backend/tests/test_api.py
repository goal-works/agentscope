from agentscope_server.database import SessionLocal
from agentscope_server.models import Trace


def test_overview_aggregates_seeded_traces(client):
    response = client.get("/api/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["executions"] == 6
    assert data["success_rate"] == 0.6667
    assert data["error_rate"] == 0.3333
    assert data["total_tokens"] > 0
    assert data["common_tools"][0] == {"name": "search_documents", "uses": 8}


def test_trace_explorer_filters_status_tool_duration_and_cost(client):
    assert len(client.get("/api/traces?status=error").json()) == 2
    assert len(client.get("/api/traces?tool=search_documents").json()) == 6
    assert len(client.get("/api/traces?min_duration_ms=60000").json()) == 1
    assert len(client.get("/api/traces?max_cost=0.01").json()) == 5
    assert len(client.get("/api/traces?has_error=true").json()) == 2
    assert len(client.get("/api/traces?agent=research-agent-v1").json()) == 6


def test_trace_detail_orders_events_and_exposes_hierarchy(client):
    traces = client.get("/api/traces").json()
    trace_id = next(trace["id"] for trace in traces if trace["external_id"] == "seed-trace-1")

    response = client.get(f"/api/traces/{trace_id}")

    assert response.status_code == 200
    detail = response.json()
    assert [event["sequence"] for event in detail["events"]] == list(
        range(len(detail["events"]))
    )
    root = next(span for span in detail["spans"] if span["external_id"] == "seed-1-root")
    child = next(span for span in detail["spans"] if span["external_id"] == "seed-1-tool")
    assert child["parent_span_id"] == root["id"]
    assert detail["total_tokens"] == detail["input_tokens"] + detail["output_tokens"]


def test_trace_comparison_returns_metric_deltas(client):
    traces = client.get("/api/traces").json()
    by_external_id = {trace["external_id"]: trace for trace in traces}
    left = by_external_id["seed-trace-1"]
    right = by_external_id["seed-trace-4"]

    response = client.get(
        f"/api/traces/compare?trace_ids={left['id']}&trace_ids={right['id']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert [trace["id"] for trace in data["traces"]] == [left["id"], right["id"]]
    assert data["delta"]["duration_ms"] > 0
    assert data["delta"]["total_tokens"] > 0
    assert data["delta"]["estimated_cost"] > 0


def test_duplicate_ingestion_is_idempotent(client):
    detail = client.get("/api/traces").json()[0]
    original = client.get(f"/api/traces/{detail['id']}").json()
    payload = {
        "external_id": original["external_id"],
        "project_slug": original["project"]["slug"],
        "project_name": original["project"]["name"],
        "agent_key": original["agent"]["key"],
        "agent_name": original["agent"]["name"],
        "name": original["name"],
        "status": original["status"],
        "started_at": original["started_at"],
        "ended_at": original["ended_at"],
    }

    response = client.post("/api/v1/traces", json=payload)

    assert response.status_code == 200
    assert response.json()["id"] == original["id"]
    with SessionLocal() as session:
        assert session.query(Trace).count() == 6


def test_ingestion_rejects_unknown_parent_span(client):
    payload = {
        "external_id": "invalid-parent",
        "project_slug": "sdk-test",
        "project_name": "SDK Test",
        "agent_key": "agent",
        "agent_name": "Agent",
        "name": "Invalid trace",
        "status": "success",
        "started_at": "2026-08-20T14:00:00Z",
        "ended_at": "2026-08-20T14:00:01Z",
        "spans": [
            {
                "external_id": "child",
                "parent_external_id": "missing",
                "name": "child",
                "type": "tool",
                "status": "success",
                "started_at": "2026-08-20T14:00:00Z",
                "ended_at": "2026-08-20T14:00:01Z",
            }
        ],
    }

    response = client.post("/api/v1/traces", json=payload)

    assert response.status_code == 422
    assert "unknown parent span" in response.text


def test_ingestion_rejects_cyclic_span_graph(client):
    span_template = {
        "type": "tool",
        "status": "success",
        "started_at": "2026-08-20T14:00:00Z",
        "ended_at": "2026-08-20T14:00:01Z",
    }
    payload = {
        "external_id": "cyclic-parent",
        "project_slug": "sdk-test",
        "project_name": "SDK Test",
        "agent_key": "agent",
        "agent_name": "Agent",
        "name": "Cyclic trace",
        "status": "success",
        "started_at": "2026-08-20T14:00:00Z",
        "ended_at": "2026-08-20T14:00:01Z",
        "spans": [
            {
                **span_template,
                "external_id": "one",
                "parent_external_id": "two",
                "name": "one",
            },
            {
                **span_template,
                "external_id": "two",
                "parent_external_id": "one",
                "name": "two",
            },
        ],
    }

    response = client.post("/api/v1/traces", json=payload)

    assert response.status_code == 422
    assert "must not contain a cycle" in response.text


def test_unknown_trace_returns_404(client):
    response = client.get("/api/traces/not-a-trace")

    assert response.status_code == 404
