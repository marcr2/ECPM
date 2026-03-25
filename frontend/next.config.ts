import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  devIndicators: false,
  output: "standalone",
  // Repo has a root package-lock.json; keep tracing rooted here so standalone is `.next/standalone/server.js`.
  outputFileTracingRoot: path.join(__dirname),
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
