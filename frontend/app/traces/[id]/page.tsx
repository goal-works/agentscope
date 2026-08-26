import type { Metadata } from "next";
import Link from "next/link";

import { Severity, Status } from "@/components/status";
import { formatCost, formatDate, formatDuration, getTrace } from "@/lib/api";

type PageProps = Readonly<{ params: Promise<{ id: string }> }>;

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const trace = await getTrace(id);
  return { title: trace.name };
}

export default async function TraceDetailPage({ params }: PageProps) {
  const { id } = await params;
  const trace = await getTrace(id);

  return (
    <main className="main">
      <div className="page-head">
        <div>
          <p className="eyebrow">Trace / {trace.external_id}</p>
          <h1>{trace.name}</h1>
          <p className="lede">{formatDate(trace.started_at)} · {trace.agent.name} · <Status value={trace.status} /></p>
        </div>
        <div className="page-actions">
          <Link className="button" href="/traces">Back to explorer</Link>
          <Link className="button primary" href={`/compare?left=${trace.id}`}>Compare</Link>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric"><p className="metric-label">Latency</p><p className="metric-value">{formatDuration(trace.duration_ms)}</p><p className="metric-foot">wall-clock duration</p></div>
        <div className="metric"><p className="metric-label">Tokens</p><p className="metric-value">{trace.total_tokens.toLocaleString()}</p><p className="metric-foot">{trace.input_tokens.toLocaleString()} in · {trace.output_tokens.toLocaleString()} out</p></div>
        <div className="metric"><p className="metric-label">Estimated cost</p><p className="metric-value">{formatCost(trace.estimated_cost)}</p><p className="metric-foot">reported model usage</p></div>
        <div className="metric"><p className="metric-label">Diagnostics</p><p className="metric-value">{trace.diagnostics.length}</p><p className="metric-foot">deterministic findings</p></div>
      </div>

      <div className="detail-grid" style={{ marginTop: 20 }}>
        <section className="panel">
          <div className="panel-head"><h2>Ordered execution timeline</h2><span className="subtle">{trace.events.length} events</span></div>
          <ol className="timeline">
            {trace.events.map((event) => (
              <li className="event" key={event.id}>
                <span className="event-index">{String(event.sequence + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{event.name}</h3>
                  <p className="event-type">{event.type.replaceAll("_", " ")}</p>
                  <details>
                    <summary>Inspect payload</summary>
                    <pre>{JSON.stringify(event.payload, null, 2)}</pre>
                  </details>
                </div>
                <span className="event-meta">{event.input_tokens + event.output_tokens} tok · {formatCost(event.estimated_cost)}</span>
              </li>
            ))}
          </ol>
        </section>

        <aside className="stack">
          <section className="panel">
            <div className="panel-head"><h2>Diagnostics</h2></div>
            <div className="panel-body">
              {trace.diagnostics.length ? (
                <ul className="diagnostic-list">
                  {trace.diagnostics.map((diagnostic) => (
                    <li className="diagnostic" key={diagnostic.id}>
                      <Severity value={diagnostic.severity} />
                      <h3 style={{ marginTop: 8 }}>{diagnostic.title}</h3>
                      <p>{diagnostic.explanation}</p>
                      <details><summary>Evidence</summary><pre>{JSON.stringify(diagnostic.evidence, null, 2)}</pre></details>
                    </li>
                  ))}
                </ul>
              ) : <p className="empty">No deterministic diagnostics fired.</p>}
            </div>
          </section>

          <section className="panel">
            <div className="panel-head"><h2>Span hierarchy</h2></div>
            <div className="panel-body">
              <ol className="tool-list">
                {trace.spans.map((span) => (
                  <li key={span.id} style={{ paddingLeft: span.parent_span_id ? 18 : 0 }}>
                    <Status value={span.status} />
                    <strong style={{ display: "block", marginTop: 6 }}>{span.name}</strong>
                    <span className="subtle">{span.type} · {formatDuration(span.duration_ms)}</span>
                  </li>
                ))}
              </ol>
            </div>
          </section>

          <section className="panel">
            <div className="panel-head"><h2>Final result</h2></div>
            <div className="panel-body"><pre>{JSON.stringify(trace.final_result ?? { error: trace.error_message }, null, 2)}</pre></div>
          </section>
        </aside>
      </div>
    </main>
  );
}
