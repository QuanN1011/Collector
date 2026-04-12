# Provenance model (API)

Each `BuildingEnriched` response includes:

- **`physical_analysis`:** Catalog roof lineage, optional tower inference metadata, `tower_status`.
- **`provenance`:** Structured object (JSON-serializable) describing sources and formulas.
- **`viability_completeness`:** `full` (rainfall + price + cooling tower pillar) or `partial` (rainfall + price only).
- **`viability_missing_components`:** e.g. `["cooling_tower"]` when live CV did not produce a result.

## `provenance` keys (stable)

| Key | Meaning |
|-----|---------|
| `state_context` | `source` (`postgres:state_context` or `csv:backend/data/state_context.csv`), state code, rainfall and price used |
| `rainwater` | Formula name, `catchment_sqft`, `catchment_source` (roof lineage string) |
| `annual_water_savings_usd` | Formula reference |
| `viability` | `computed_at_utc`, `completeness`, `missing_components`, `weights_applied` (per-pillar weights that sum to 1), formula description |
| `cooling_tower` | `tower_status`, `vision_backend`, imagery fields, inference model/time, `unavailable_reason` when applicable |
| `esg` | `status: unavailable` and `reason` until real data is linked |

## Scoring algebra

Implemented in `services/scoring.py`:

- Normalize rainfall and water price to 0–100 using documented reference scales.
- If `tower_status` is `real_detected` or `real_not_detected`, add cooling tower subscore and renormalize weights over **rainfall + water_price + cooling_tower** (original relative weights 0.35 / 0.25 / 0.25).
- If tower is **unavailable**, renormalize over **rainfall + water_price** only (0.35 / 0.25 → sum to 1).

No ESG pillar is included until real company data is available.

## Freshness

- **Viability:** `provenance.viability.computed_at_utc` — time of enrichment.
- **State context:** No per-row `updated_at` in MVP; source file/table name is given. Add DB columns in a future migration if audit timestamps are required.
- **Tower inference:** `physical_analysis.inference_timestamp_utc` when Gemini returns a parseable result; imagery composite range in `imagery_date_range`.

## UI expectations

The frontend labels **partial** viability, **unavailable** tower and ESG, and keeps the illustrative residential bill in `WaterEconomicsSection` explicitly marked as non-site-specific (see component copy).
