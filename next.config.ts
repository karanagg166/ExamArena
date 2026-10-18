import type { NextConfig } from "next";

const isVercel = Boolean(process.env.VERCEL || process.env.VERCEL_ENV);
const isStandalone = Boolean(process.env.OUTPUT_STANDALONE || process.env.DOCKER_BUILD);

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  ...(isStandalone && !isVercel ? { output: "standalone" } : {}),
};

export default nextConfig;
