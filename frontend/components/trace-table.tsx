import Link from "next/link";

import { Status } from "@/components/status";
import {
  formatCost,
  formatDate,
  formatDuration,
  type TraceSummary,
} from "@/lib/api";

export function TraceTable({ traces }: Readonly<{ traces: TraceSummary[] }>) {
  if (traces.length === 0) {
    return <p className="empty">No traces match the selected filters.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Trace</th>
            <th scope="col">Status</th>
            <th scope="col">Started</th>
            <th scope="col">Latency</th>
            <th scope="col">Tokens</th>
            <th scope="col">Cost</th>
            <th scope="col">Diagnostics</th>
          </tr>
        </thead>
        <tbody>
          {traces.map((trace) => (
            <tr key={trace.id}>
              <td>
                <Link className="trace-link" href={`/traces/${trace.id}`}>
                  {trace.name}
                </Link>
                <div className="subtle">{trace.external_id}</div>
              </td>
              <td><Status value={trace.status} /></td>
              <td>{formatDate(trace.started_at)}</td>
              <td>{formatDuration(trace.duration_ms)}</td>
              <td>{trace.total_tokens.toLocaleString()}</td>
              <td>{formatCost(trace.estimated_cost)}</td>
              <td>{trace.diagnostic_count || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
