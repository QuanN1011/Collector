import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

/** Directory containing this file (the Next app root), not `process.cwd()` — avoids Turbopack 500s when `npm run dev` is launched from the repo root. */
const collectorRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(collectorRoot, "..");

/**
 * Merge env from the git repo root (e.g. `/Collector/.env.local`) so `NEXT_PUBLIC_*` is not missed
 * when only `collector/.env.local` is documented but teammates keep secrets one level up after merge.
 */
loadEnvConfig(repoRoot);

const nextConfig: NextConfig = {
  turbopack: {
    root: collectorRoot,
  },
};

export default nextConfig;
