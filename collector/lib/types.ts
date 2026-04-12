/** Mirrors backend `models/building.py` API payloads. */

export type PhysicalAnalysis = {
  roof_catchment_sqft: number;
  large_roof: boolean;
  roof_confidence: number;
  roof_catchment_provenance: string;
  cooling_tower_detected: boolean;
  cooling_tower_confidence: number;
  imagery_source: string;
  vision_backend: string;
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
  cooling_tower_detected: boolean;
  cooling_tower_confidence: number;
  esg_signal_score: number;
  physical_analysis: PhysicalAnalysis;
  data_notes: string;
};

export type StatesResponse = {
  states: string[];
};

export type HealthResponse = {
  status: string;
};
