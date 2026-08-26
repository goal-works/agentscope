import Link from "next/link";

import { Metrics } from "@/components/metrics";
import { TraceTable } from "@/components/trace-table";
import { getOverview, getTraces } from "@/lib/api";

export default async function OverviewPage() {
  const [overview, traces] = await Promise.all([getOverview(), getTraces()]);
  const maxUses = overview.common_tools[0]?.uses ?? 1;

  return (
    <main className="main">
      <div className="page-head">
        <div>
          <p className="eyebrow">Execution overview</p>
          <h1>Observe every decision.</h1>
          <p className="lede">
            Inspect how the agent reasoned, which tools it called, what failed,
            and what each execution cost.
          </p>
        </div>
        <Link className="button primary" href="/traces">Explore traces</Link>
      </div>

      <Metrics overview={overview} />

      <div className="grid-2">
        <section className="panel">
          <div className="panel-head">
            <h2>Recent traces</h2>
            <Link href="/traces">View all</Link>
          </div>
          <TraceTable traces={traces.slice(0, 5)} />
        </section>

        <section className="panel">
          <div className="panel-head"><h2>Common tools</h2></div>
          <div className="panel-body">
            <ol className="tool-list">
              {overview.common_tools.map((tool) => (
                <li className="tool-row" key={tool.name}>
                  <span>{tool.name}</span>
                  <span className="subtle">{tool.uses} calls</span>
                  <div className="tool-bar" aria-hidden="true">
                    <span style={{ width: `${(tool.uses / maxUses) * 100}%` }} />
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>
      </div>
    </main>
  );
}
