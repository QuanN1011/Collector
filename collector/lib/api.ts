import type { BuildingEnriched, HealthResponse, StatesResponse } from "./types";

/** FastAPI base URL (inlined in client bundles via NEXT_PUBLIC_*). */
export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function apiHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem("rainuse_api_key");
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

export async function fetchTopProspects(state: string, limit = 25): Promise<BuildingEnriched[]> {
  return apiGet<BuildingEnriched[]>(
    `/top-prospects?state=${encodeURIComponent(state)}&limit=${encodeURIComponent(String(limit))}`,
  );
}
