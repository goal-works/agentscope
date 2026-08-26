import type { Metadata } from "next";

import { Status } from "@/components/status";
import { compareTraces, formatCost, formatDuration, getTraces } from "@/lib/api";

export const metadata: Metadata = { title: "Trace comparison" };
type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function ComparePage({ searchParams }: Readonly<{ searchParams: SearchParams }>) {
  const [params, traces] = await Promise.all([searchParams, getTraces()]);
  const requestedLeft = typeof params.left === "string" ? params.left : undefined;
  const requestedRight = typeof params.right === "string" ? params.right : undefined;
  const left = requestedLeft ?? traces[0]?.id;
  const right = requestedRight ?? traces.find((trace) => trace.id !== left)?.id;
  const comparison = left && right ? await compareTraces(left, right) : null;

  return (
    <main className="main">
      <div className="page-head">
        <div><p className="eyebrow">Trace comparison</p><h1>See where behavior diverged.</h1><p className="lede">Compare outcomes, latency, tokens, tool calls, cost, errors, and ordered evidence.</p></div>
      </div>

      <form className="filters" style={{ gridTemplateColumns: "1fr 1fr auto" }}>
        <div className="field"><label htmlFor="left">Baseline</label><select defaultValue={left} id="left" name="left">{traces.map((trace) => <option key={trace.id} value={trace.id}>{trace.name}</option>)}</select></div>
        <div className="field"><label htmlFor="right">Candidate</label><select defaultValue={right} id="right" name="right">{traces.map((trace) => <option key={trace.id} value={trace.id}>{trace.name}</option>)}</select></div>
        <button className="button primary" type="submit">Compare</button>
      </form>

      {comparison ? (
        <>
          <div className="metric-grid">
            <div className="metric"><p className="metric-label">Latency delta</p><p className="metric-value delta">{formatDuration(comparison.delta.duration_ms)}</p></div>
            <div className="metric"><p className="metric-label">Token delta</p><p className="metric-value delta">{comparison.delta.total_tokens.toLocaleString()}</p></div>
            <div className="metric"><p className="metric-label">Cost delta</p><p className="metric-value delta">{formatCost(comparison.delta.estimated_cost)}</p></div>
            <div className="metric"><p className="metric-label">Error delta</p><p className="metric-value delta">{comparison.delta.errors}</p></div>
          </div>
          <section className="compare-grid" style={{ marginTop: 20 }}>
            {comparison.traces.map((trace, index) => (
              <article className="compare-column" key={trace.id}>
                <p className="eyebrow">{index === 0 ? "Baseline" : "Candidate"}</p>
                <h2>{trace.name}</h2>
                <p style={{ marginTop: 12 }}><Status value={trace.status} /></p>
                <dl className="tool-list" style={{ marginTop: 24 }}>
                  <div className="tool-row"><dt>Latency</dt><dd>{formatDuration(trace.duration_ms)}</dd></div>
                  <div className="tool-row"><dt>Tokens</dt><dd>{trace.total_tokens.toLocaleString()}</dd></div>
                  <div className="tool-row"><dt>Cost</dt><dd>{formatCost(trace.estimated_cost)}</dd></div>
                  <div className="tool-row"><dt>Events</dt><dd>{trace.events.length}</dd></div>
                  <div className="tool-row"><dt>Diagnostics</dt><dd>{trace.diagnostics.length}</dd></div>
                </dl>
                <h3 style={{ marginTop: 28 }}>Final result</h3>
                <pre>{JSON.stringify(trace.final_result ?? { error: trace.error_message }, null, 2)}</pre>
              </article>
            ))}
          </section>
        </>
      ) : <p className="empty">Two traces are required for comparison.</p>}
    </main>
  );
}
