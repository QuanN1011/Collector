import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // When the repo root also has package-lock.json, point Turbopack at this app (must match `npm run dev` cwd).
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
