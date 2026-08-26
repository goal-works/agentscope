import type { Metadata } from "next";

import { Sidebar } from "@/components/sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "AgentScope", template: "%s | AgentScope" },
  description: "Trace observability and deterministic diagnostics for AI agents.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Sidebar />
          <div className="content">
            <header className="topbar">
              <p>Incident Research Demo / Research Agent V1</p>
              <span className="live">Ingestion ready</span>
            </header>
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
