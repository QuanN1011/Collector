/** Mirrors backend `models/building.py` API payloads. */

export type TowerStatus = "real_detected" | "real_not_detected" | "unavailable";

export type PhysicalAnalysis = {
  roof_catchment_sqft: number;
  large_roof: boolean;
  roof_confidence: number;
  roof_catchment_provenance: string;
  tower_status: TowerStatus;
  cooling_tower_detected: boolean | null;
  cooling_tower_confidence: number | null;
  tower_unavailable_reason: string | null;
  imagery_source: string;
  vision_backend: string;
  inference_model: string | null;
  inference_timestamp_utc: string | null;
  imagery_date_range: string | null;
  imagery_provider: string | null;
  selected_roof_source: string;
  selected_cooling_tower_source: string;
  raw_sources_available: Record<string, unknown>;
};

export type BuildingEnriched = {
  id: string;
  name: string;
  state: string;
  city?: string | null;
  roof_area_sqft: number;
  latitude?: number | null;
  longitude?: number | null;
  rainfall_inches_annual: number;
  water_price_per_1000_gal_usd: number;
  rainwater_potential_gallons: number;
  annual_water_savings: number;
  viability_score: number;
  viability_breakdown: Record<string, number>;
  viability_completeness: "full" | "partial";
  viability_missing_components: string[];
  cooling_tower_detected: boolean | null;
  cooling_tower_confidence: number | null;
  company_id?: string | null;
  esg_score: number | null;
  esg_source: string | null;
  esg_confidence: number | null;
  esg_status: "unavailable" | "real" | "proxy";
  esg_details: Record<string, unknown>;
  esg_signal_score: number | null;
  esg_unavailable_reason?: string | null;
  physical_analysis: PhysicalAnalysis;
  data_notes: string;
  provenance?: Record<string, unknown>;
};

export type StatesResponse = {
  states: string[];
};

export type HealthResponse = {
  status: string;
};
