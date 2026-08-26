import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  ...(process.env.NEXT_STANDALONE === "true"
    ? { output: "standalone" as const }
    : {}),
  outputFileTracingRoot: process.cwd(),
  experimental: {
    useTypeScriptCli: false,
  },
  poweredByHeader: false,
};

export default nextConfig;
