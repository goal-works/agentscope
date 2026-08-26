import type { Metadata } from "next";
import Link from "next/link";

import { Severity, Status } from "@/components/status";
import { getTrace, getTraces } from "@/lib/api";

export const metadata: Metadata = { title: "Diagnostics" };

export default async function DiagnosticsPage() {
  const summaries = await getTraces();
  const traces = await Promise.all(
    summaries.filter((trace) => trace.diagnostic_count > 0).map((trace) => getTrace(trace.id)),
  );
  const findings = traces.flatMap((trace) =>
    trace.diagnostics.map((diagnostic) => ({ trace, diagnostic })),
  );

  return (
    <main className="main">
      <div className="page-head"><div><p className="eyebrow">Deterministic diagnostics</p><h1>Explainable signals, not opaque scores.</h1><p className="lede">Each finding names the threshold or repeated behavior that triggered it and preserves supporting evidence.</p></div></div>
      <section className="panel">
        <div className="panel-head"><h2>{findings.length} findings across {traces.length} traces</h2></div>
        <div className="panel-body">
          <ul className="diagnostic-list">
            {findings.map(({ trace, diagnostic }) => (
              <li className="diagnostic" key={diagnostic.id}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><Severity value={diagnostic.severity} /><Status value={trace.status} /></div>
                <h3 style={{ marginTop: 10 }}>{diagnostic.title}</h3>
                <p>{diagnostic.explanation}</p>
                <Link className="button" href={`/traces/${trace.id}`} style={{ marginTop: 14 }}>Inspect {trace.name}</Link>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
