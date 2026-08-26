import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  experimental: {
    useTypeScriptCli: false,
  },
  poweredByHeader: false,
};

export default nextConfig;
