const API_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001/api";

export type Overview = {
  executions: number;
  success_rate: number;
  error_rate: number;
  average_latency_ms: number;
  average_cost: number;
  total_tokens: number;
  common_tools: { name: string; uses: number }[];
};

export type TraceSummary = {
  id: string;
  external_id: string;
  name: string;
  status: "running" | "success" | "error";
  started_at: string;
  ended_at: string | null;
  duration_ms: number;
  total_tokens: number;
  estimated_cost: string;
  error_message: string | null;
  agent: { id: string; key: string; name: string };
  project: { id: string; name: string; slug: string };
  diagnostic_count: number;
};

export type Diagnostic = {
  id: string;
  type: string;
  severity: "info" | "warning" | "critical";
  title: string;
  explanation: string;
  evidence: Record<string, unknown>;
};

export type Span = {
  id: string;
  external_id: string;
  parent_span_id: string | null;
  name: string;
  type: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number;
  input: unknown;
  output: unknown;
  attributes: Record<string, unknown>;
};

export type Event = {
  id: string;
  external_id: string;
  span_id: string | null;
  type: string;
  name: string;
  sequence: number;
  timestamp: string;
  payload: Record<string, unknown>;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: string;
};

export type TraceDetail = TraceSummary & {
  input_tokens: number;
  output_tokens: number;
  input: Record<string, unknown>;
  final_result: unknown;
  trace_metadata: Record<string, unknown>;
  spans: Span[];
  events: Event[];
  diagnostics: Diagnostic[];
};

export type TraceComparison = {
  traces: [TraceDetail, TraceDetail];
  delta: {
    duration_ms: number;
    total_tokens: number;
    estimated_cost: number;
    tool_calls: number;
    errors: number;
  };
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`AgentScope API returned ${response.status} for ${path}`);
  }
  return response.json() as Promise<T>;
}

export function getOverview() {
  return get<Overview>("/overview");
}

export function getTraces(query = "") {
  return get<TraceSummary[]>(`/traces${query ? `?${query}` : ""}`);
}

export function getTrace(id: string) {
  return get<TraceDetail>(`/traces/${id}`);
}

export function compareTraces(left: string, right: string) {
  const query = new URLSearchParams();
  query.append("trace_ids", left);
  query.append("trace_ids", right);
  return get<TraceComparison>(`/traces/compare?${query}`);
}

export function formatDuration(durationMs: number): string {
  if (durationMs >= 60_000) return `${(durationMs / 60_000).toFixed(1)}m`;
  if (durationMs >= 1_000) return `${(durationMs / 1_000).toFixed(1)}s`;
  return `${durationMs}ms`;
}

export function formatCost(value: string | number): string {
  return `$${Number(value).toFixed(4)}`;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(new Date(value));
}
