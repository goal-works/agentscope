def _detail_for_external_id(client, external_id: str) -> dict:
    trace = next(
        trace for trace in client.get("/api/traces").json() if trace["external_id"] == external_id
    )
    return client.get(f"/api/traces/{trace['id']}").json()


def test_repeated_tool_call_detector_reports_evidence(client):
    detail = _detail_for_external_id(client, "seed-trace-3")
    diagnostic = next(
        item for item in detail["diagnostics"] if item["type"] == "repeated_tool_call"
    )

    assert diagnostic["severity"] == "warning"
    assert diagnostic["evidence"]["occurrences"] == 3


def test_malformed_tool_arguments_are_critical(client):
    detail = _detail_for_external_id(client, "seed-trace-5")
    diagnostic = next(
        item for item in detail["diagnostics"] if item["type"] == "malformed_arguments"
    )

    assert diagnostic["severity"] == "critical"


def test_expensive_slow_context_trace_gets_three_explainable_diagnostics(client):
    detail = _detail_for_external_id(client, "seed-trace-4")
    diagnostic_types = {item["type"] for item in detail["diagnostics"]}

    assert {"context_growth", "slow_trace", "expensive_trace"} <= diagnostic_types


def test_tool_error_is_preserved_even_when_trace_recovers(client):
    detail = _detail_for_external_id(client, "seed-trace-2")

    assert detail["status"] == "success"
    assert "tool_error" in {item["type"] for item in detail["diagnostics"]}
