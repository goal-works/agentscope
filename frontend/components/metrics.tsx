import { formatCost, formatDuration, type Overview } from "@/lib/api";

export function Metrics({ overview }: Readonly<{ overview: Overview }>) {
  const values = [
    ["Executions", overview.executions.toLocaleString(), "persisted synthetic traces"],
    ["Success rate", `${(overview.success_rate * 100).toFixed(1)}%`, `${(overview.error_rate * 100).toFixed(1)}% error rate`],
    ["Average latency", formatDuration(overview.average_latency_ms), "wall-clock execution"],
    ["Average cost", formatCost(overview.average_cost), `${overview.total_tokens.toLocaleString()} total tokens`],
  ] as const;

  return (
    <div className="metric-grid">
      {values.map(([label, value, foot]) => (
        <div className="metric" key={label}>
          <p className="metric-label">{label}</p>
          <p className="metric-value">{value}</p>
          <p className="metric-foot">{foot}</p>
        </div>
      ))}
    </div>
  );
}
