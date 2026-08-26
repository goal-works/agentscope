"use client";

export default function ErrorPage({ reset }: Readonly<{ reset: () => void }>) {
  return (
    <main className="main">
      <p className="eyebrow">API unavailable</p>
      <h1>Trace data could not be loaded.</h1>
      <p className="lede">Start the AgentScope API on port 8001, then try again.</p>
      <button className="button primary" onClick={reset} type="button">Try again</button>
    </main>
  );
}
