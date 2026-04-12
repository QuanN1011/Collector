import type { AnalyzeBuildingResponse, BuildingEnriched, HealthResponse, StatesResponse } from "./types";

function normalizeApiBase(raw: string | undefined): string {
  const fallback = "http://127.0.0.1:8000";
  const t = raw?.trim();
  if (!t) return fallback;
  return t.replace(/\/$/, "");
}

/** FastAPI base URL (inlined in client bundles via NEXT_PUBLIC_*). */
export const apiBaseUrl = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL);

/** localStorage key for `X-Api-Key` on prospecting requests and API key UI. */
export const API_KEY_STORAGE_KEY = "rainuse_api_key";

function apiHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem(API_KEY_STORAGE_KEY);
  if (!key) return {};
  return { "X-Api-Key": key };
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBaseUrl}${path}`, { headers: apiHeaders() });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j: unknown = await res.json();
      if (j && typeof j === "object" && "detail" in j) {
        const d = (j as { detail: unknown }).detail;
        detail = typeof d === "string" ? d : JSON.stringify(d);
      }
    } catch {
      /* ignore */
    }
    if (res.status === 404) {
      detail = `${detail} — restart the API from backend/ (e.g. npm run dev:backend) so routes like ${path} exist, or fix NEXT_PUBLIC_API_URL if it points at the wrong server.`;
    }
    if (res.status === 429) {
      let msg = typeof detail === "string" ? detail : String(detail);
      if (msg.length > 900) {
        msg =
          "Gemini quota or rate limit exceeded. Wait and retry, set GEMINI_MODEL=gemini-2.0-flash in backend/.env, or enable billing. See https://ai.google.dev/gemini-api/docs/rate-limits";
      }
      throw new Error(msg);
    }
    if (res.status === 503) {
      let msg = typeof detail === "string" ? detail : String(detail);
      if (msg.length > 900 || msg.includes("'error':")) {
        msg =
          "Gemini is temporarily overloaded (503). Wait 1–2 minutes and retry, or try GEMINI_MODEL=gemini-2.0-flash in backend/.env.";
      }
      throw new Error(msg);
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

export async function fetchStates(): Promise<StatesResponse> {
  return apiGet<StatesResponse>("/states");
}

/** All buildings, or filter by state (USPS code). */
export async function fetchBuildings(state?: string): Promise<BuildingEnriched[]> {
  const q = state ? `?state=${encodeURIComponent(state)}` : "";
  return apiGet<BuildingEnriched[]>(`/buildings${q}`);
}

export async function fetchBuilding(id: string, liveCv: boolean): Promise<BuildingEnriched> {
  const q = `?live_cv=${liveCv ? "true" : "false"}`;
  return apiGet<BuildingEnriched>(`/building/${encodeURIComponent(id)}${q}`);
}

export type TopProspectsOptions = {
  /** When set with originLng, API blends viability with proximity (haversine). */
  originLat?: number;
  originLng?: number;
  /** 0 = viability only; 1 = mostly distance (default 0.35). */
  locationWeight?: number;
};

export async function fetchTopProspects(
  state: string,
  limit = 25,
  opts?: TopProspectsOptions,
): Promise<BuildingEnriched[]> {
  const params = new URLSearchParams({
    state,
    limit: String(limit),
  });
  if (opts?.originLat != null && opts?.originLng != null) {
    params.set("origin_lat", String(opts.originLat));
    params.set("origin_lng", String(opts.originLng));
    if (opts.locationWeight != null) {
      params.set("location_weight", String(opts.locationWeight));
    }
  }
  return apiGet<BuildingEnriched[]>(`/top-prospects?${params.toString()}`);
}

/** Address → geocode → Static Maps satellite chip → Gemini → rainwater / savings / viability. */
export async function fetchAnalyzeBuilding(address: string, state: string): Promise<AnalyzeBuildingResponse> {
  const q = new URLSearchParams({
    address: address.trim(),
    state: state.trim().toUpperCase(),
  });
  return apiGet<AnalyzeBuildingResponse>(`/analyze-building?${q.toString()}`);
}
