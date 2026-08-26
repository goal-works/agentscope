import type { Metadata } from "next";

export const metadata: Metadata = { title: "Python SDK" };

const sample = `from agentscope import AgentScope

scope = AgentScope(
    project_slug="incident-research",
    project_name="Incident Research",
)

with scope.trace("research-agent", input={"question": question}) as trace:
    with trace.span("web_search", type="tool", input={"query": question}) as span:
        trace.event(
            "tool_call",
            "web_search",
            payload={"arguments": {"query": question}},
        )
        result = search(question)
        span.set_output(result)

    trace.set_result({"answer": summarize(result)})`;

export default function DocumentationPage() {
  return (
    <main className="main">
      <div className="page-head"><div><p className="eyebrow">Python SDK</p><h1>Instrument the boundary that matters.</h1><p className="lede">A dependency-free context-manager API captures trace identity, nested spans, ordered events, failures, usage, and final output.</p></div></div>
      <div className="detail-grid">
        <section className="panel"><div className="panel-head"><h2>Context-manager example</h2></div><pre className="code-sample">{sample}</pre></section>
        <aside className="stack">
          <section className="panel"><div className="panel-head"><h2>Captured evidence</h2></div><div className="panel-body"><ul className="tool-list"><li>Trace status and timing</li><li>Parent / child span identity</li><li>Ordered model and tool events</li><li>Token and estimated cost metrics</li><li>Unhandled exception evidence</li></ul></div></section>
          <section className="panel"><div className="panel-head"><h2>Delivery behavior</h2></div><div className="panel-body"><p className="lede" style={{ fontSize: 14, margin: 0 }}>The SDK sends one validated JSON document to the ingestion endpoint when the trace context closes. Reusing an external trace ID is idempotent.</p></div></section>
        </aside>
      </div>
    </main>
  );
}
