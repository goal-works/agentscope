import type { Metadata } from "next";
import Link from "next/link";

import { TraceTable } from "@/components/trace-table";
import { getTraces } from "@/lib/api";

export const metadata: Metadata = { title: "Trace explorer" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function value(params: Record<string, string | string[] | undefined>, key: string) {
  const current = params[key];
  return Array.isArray(current) ? current[0] ?? "" : current ?? "";
}

export default async function TracesPage({ searchParams }: Readonly<{ searchParams: SearchParams }>) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const key of ["agent", "status", "min_duration_ms", "max_cost", "tool"] as const) {
    const selected = value(params, key);
    if (selected) query.set(key, selected);
  }
  const traces = await getTraces(query.toString());

  return (
    <main className="main">
      <div className="page-head">
        <div>
          <p className="eyebrow">Trace explorer</p>
          <h1>Find the execution that changed.</h1>
          <p className="lede">Filter durable trace evidence by outcome, agent, latency, cost, or tool use.</p>
        </div>
        <Link className="button" href="/compare">Compare traces</Link>
      </div>

      <form className="filters">
        <div className="field">
          <label htmlFor="agent">Agent</label>
          <select defaultValue={value(params, "agent")} id="agent" name="agent">
            <option value="">All agents</option>
            <option value="research-agent-v1">Research Agent V1</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="status">Status</label>
          <select defaultValue={value(params, "status")} id="status" name="status">
            <option value="">All outcomes</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="running">Running</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="tool">Tool</label>
          <select defaultValue={value(params, "tool")} id="tool" name="tool">
            <option value="">All tools</option>
            <option value="search_documents">search_documents</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="min_duration_ms">Min latency ms</label>
          <input defaultValue={value(params, "min_duration_ms")} id="min_duration_ms" min="0" name="min_duration_ms" type="number" />
        </div>
        <div className="field">
          <label htmlFor="max_cost">Max cost USD</label>
          <input defaultValue={value(params, "max_cost")} id="max_cost" min="0" name="max_cost" step="0.001" type="number" />
        </div>
        <button className="button primary" type="submit">Apply</button>
      </form>

      <section className="panel">
        <div className="panel-head">
          <h2>{traces.length} trace{traces.length === 1 ? "" : "s"}</h2>
          <Link href="/traces">Clear filters</Link>
        </div>
        <TraceTable traces={traces} />
      </section>
    </main>
  );
}
