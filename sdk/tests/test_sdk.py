from agentscope import AgentScope


def test_sdk_builds_hierarchical_trace_and_uploads_once():
    uploads: list[dict] = []
    scope = AgentScope(
        project_slug="sdk-demo",
        project_name="SDK Demo",
        transport=lambda payload: uploads.append(payload) or {"id": "stored-trace"},
    )

    with scope.trace(
        "research-agent",
        name="Research question",
        input={"question": "What happened?"},
    ) as trace:
        with trace.span("agent-loop", type="agent"):
            trace.event(
                "model_request",
                "reasoning-request",
                input_tokens=120,
                estimated_cost="0.001",
            )
            with trace.span("web_search", type="tool", input={"query": "incident"}) as span:
                trace.event(
                    "tool_call",
                    "web_search",
                    payload={"arguments": {"query": "incident"}},
                )
                span.set_output({"results": 2})
        trace.set_result({"answer": "A synthetic incident."})

    assert len(uploads) == 1
    payload = uploads[0]
    assert payload["status"] == "success"
    assert payload["final_result"] == {"answer": "A synthetic incident."}
    parent = next(span for span in payload["spans"] if span["name"] == "agent-loop")
    child = next(span for span in payload["spans"] if span["name"] == "web_search")
    assert child["parent_external_id"] == parent["external_id"]
    assert [event["sequence"] for event in payload["events"]] == [0, 1, 2]
    assert trace.response == {"id": "stored-trace"}


def test_sdk_records_errors_and_does_not_swallow_application_exception():
    uploads: list[dict] = []
    scope = AgentScope(transport=lambda payload: uploads.append(payload) or {})

    try:
        with scope.trace("failing-agent") as trace, trace.span("broken_tool", type="tool"):
            raise ValueError("synthetic failure")
    except ValueError as error:
        assert str(error) == "synthetic failure"
    else:
        raise AssertionError("the application exception should be re-raised")

    assert uploads[0]["status"] == "error"
    assert uploads[0]["error_message"] == "synthetic failure"
    assert [event["type"] for event in uploads[0]["events"]] == ["error", "error"]
