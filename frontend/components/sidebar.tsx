import Link from "next/link";

const navigation = [
  ["Overview", "/"],
  ["Trace explorer", "/traces"],
  ["Compare", "/compare"],
  ["Diagnostics", "/diagnostics"],
  ["SDK", "/documentation"],
] as const;

export function Sidebar() {
  return (
    <aside className="sidebar">
      <Link className="brand" href="/">
        Agent<span>Scope</span>
      </Link>
      <p className="brand-subtitle">Agent observability</p>
      <nav className="nav" aria-label="Primary">
        {navigation.map(([label, href]) => (
          <Link key={href} href={href}>
            {label}
          </Link>
        ))}
      </nav>
      <p className="environment">
        Data mode<br />
        <strong>Synthetic demo</strong>
      </p>
    </aside>
  );
}
