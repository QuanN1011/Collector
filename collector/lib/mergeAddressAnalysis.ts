import type { AnalyzeBuildingResponse, BuildingEnriched } from "./types";

/** Merge geocoded address analysis with a catalog row so water economics keeps state rainfall and rates. */
export function mergeAnalyzeIntoBuildingEnriched(
  base: BuildingEnriched,
  r: AnalyzeBuildingResponse,
): BuildingEnriched {
  const large = r.roof_area_sqft >= 100_000;
  return {
    ...base,
    name: r.building_name,
    city: null,
    roof_area_sqft: r.roof_area_sqft,
    latitude: r.lat,
    longitude: r.lng,
    rainwater_potential_gallons: r.rainwater_potential_gallons,
    annual_water_savings: r.annual_water_savings,
    viability_score: r.viability_score,
    cooling_tower_detected: r.cooling_tower_detected,
    cooling_tower_confidence: r.cooling_tower_confidence,
    physical_analysis: {
      ...base.physical_analysis,
      roof_catchment_sqft: r.roof_area_sqft,
      large_roof: large,
      cooling_tower_detected: r.cooling_tower_detected,
      cooling_tower_confidence: r.cooling_tower_confidence,
      vision_backend: "gemini_vision",
      imagery_source: "google_static_maps",
      roof_confidence: 0.75,
      roof_catchment_provenance: "analyze_building_pipeline",
      roof_area_estimated_cv: r.roof_area_sqft,
      cv_reasoning: r.roof_estimate,
    },
    data_notes: "",
    roof_area_sqft_catalog: base.roof_area_sqft,
    roof_area_estimated_cv: r.roof_area_sqft,
    cv_reasoning: r.roof_estimate,
  };
}
