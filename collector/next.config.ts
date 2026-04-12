import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

/** Directory containing this file (the Next app root), not `process.cwd()` — avoids Turbopack 500s when `npm run dev` is launched from the repo root. */
const collectorRoot = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  turbopack: {
    root: collectorRoot,
  },
};

export default nextConfig;
