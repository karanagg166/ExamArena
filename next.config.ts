import type { NextConfig } from "next";

const isVercel = Boolean(process.env.VERCEL || process.env.VERCEL_ENV);

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  ...(isVercel ? {} : { output: "standalone" }),
};

export default nextConfig;
