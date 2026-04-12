"use client";

import type { BuildingEnriched } from "../../lib/types";

const BREAKDOWN_LABELS: Record<string, string> = {
  rainfall: "Rainfall (state context)",
  water_price: "Water price (state context)",
  cooling_tower: "Cooling tower (live CV)",
  esg: "ESG (company, SBTi)",
};

function esgBandLabel(score: number): "High" | "Medium" | "Low" {
  if (score >= 70) return "High";
  if (score >= 45) return "Medium";
  return "Low";
}

function esgSourceLabel(source: string | null | undefined): string {
  const s = (source || "").trim();
  if (!s) return "—";
  if (s.toLowerCase().startsWith("sbti")) return "SBTi";
  if (s === "documented_industry_proxy" || s === "documented_proxy") return "Industry proxy";
  return s;
}

function BarRow({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span className="font-medium text-slate-800">{value.toFixed(1)}</span>
      </div>
      <svg
        className="h-2 w-full overflow-visible rounded-full"
        viewBox="0 0 100 2"
        preserveAspectRatio="none"
        aria-hidden
      >
        <rect x="0" y="0" width="100" height="2" className="fill-slate-200" rx="1" />
        <rect x="0" y="0" width={pct} height="2" className="fill-cyan-500 transition-[width] duration-300 ease-out" rx="1" />
      </svg>
    </div>
  );
}

export default function BuildingInsights({
  building,
  loading,
}: {
  building: BuildingEnriched | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">Loading building analysis…</div>
    );
  }
  if (!building) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-6 text-sm text-slate-600">
        Select a building to see viability, economics, and site analysis.
      </div>
    );
  }

  const pa = building.physical_analysis;
  const mapHref =
    building.latitude != null && building.longitude != null
      ? `https://www.google.com/maps?q=${building.latitude},${building.longitude}`
      : null;

  const hasEsg = building.esg_status !== "unavailable" && building.esg_score != null;
  const viabilityLabel =
    building.viability_completeness === "full"
      ? `0–100 composite (rainfall + price + cooling tower${hasEsg ? " + ESG" : ""})`
      : `0–100 composite (rainfall + price + optional ESG; cooling tower unavailable — weights renormalized)`;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-800">Viability score</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{building.viability_score.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-600">{viabilityLabel}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual savings proxy</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">${building.annual_water_savings.toLocaleString()}</p>
          <p className="mt-1 text-xs text-slate-500">Rainwater offset at state reference water rate</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">ESG signal</p>
          {building.esg_status === "unavailable" || building.esg_score == null ? (
            <>
              <p className="mt-2 text-lg font-semibold text-slate-600">Unavailable</p>
              <p className="mt-1 text-xs text-slate-500">
                {building.esg_unavailable_reason ?? "No SBTi-backed company profile for this building’s company_id."}
              </p>
            </>
          ) : (
            <>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{esgBandLabel(building.esg_score)}</p>
              <p className="mt-1 text-xs text-slate-600">
                Score {building.esg_score.toFixed(0)} · Source: {esgSourceLabel(building.esg_source)}
                {building.esg_status === "proxy" ? " (documented proxy)" : ""}
              </p>
              {building.esg_confidence != null ? (
                <p className="mt-1 text-xs text-slate-500">Confidence {(building.esg_confidence * 100).toFixed(0)}%</p>
              ) : null}
            </>
          )}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual rainfall (state)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{building.rainfall_inches_annual.toFixed(1)} in</p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-slate-950">Viability breakdown</h3>
        <p className="mt-1 text-xs text-slate-500">Normalized pillar scores before weighting (see API provenance.weights_applied).</p>
        {building.viability_completeness === "partial" ? (
          <p className="mt-2 text-xs text-amber-800">
            Partial score: {building.viability_missing_components.join(", ")} omitted — remaining pillars reweighted.
          </p>
        ) : null}
        <div className="mt-4 space-y-3">
          {Object.entries(building.viability_breakdown).map(([key, val]) => (
            <BarRow key={key} label={BREAKDOWN_LABELS[key] ?? key} value={val} />
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-slate-950">Site imagery &amp; cooling signal</h3>
        <p className="mt-1 text-xs text-slate-500">
          Catchment and tower use explicit source selection: valid CV when stored and allowed, else catalog baseline (e.g. US
          footprints), with tower unavailable when no completed inference.
        </p>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Catchment used (sq ft)</dt>
            <dd className="font-medium text-slate-950">{pa.roof_catchment_sqft.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Large roof (≥100k sq ft)</dt>
            <dd className="font-medium text-slate-950">{pa.large_roof ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Roof confidence (selected source)</dt>
            <dd className="font-medium text-slate-950">{(pa.roof_confidence * 100).toFixed(0)}%</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Selected roof source</dt>
            <dd className="font-medium text-slate-950">{pa.selected_roof_source}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Selected cooling tower source</dt>
            <dd className="font-medium text-slate-950">{pa.selected_cooling_tower_source}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs uppercase tracking-wider text-slate-500">Catchment provenance</dt>
            <dd className="font-medium text-slate-950">{pa.roof_catchment_provenance}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs uppercase tracking-wider text-slate-500">Cooling tower</dt>
            <dd className="font-medium text-slate-950">
              {pa.tower_status === "unavailable" ? (
                <span>
                  Unavailable
                  {pa.tower_unavailable_reason ? (
                    <span className="mt-1 block text-xs font-normal text-slate-600">{pa.tower_unavailable_reason}</span>
                  ) : null}
                </span>
              ) : pa.tower_status === "real_detected" ? (
                <>
                  Detected (real inference, {(pa.cooling_tower_confidence ?? 0) * 100}% conf.)
                </>
              ) : (
                <>
                  Not detected (real inference, {(pa.cooling_tower_confidence ?? 0) * 100}% conf.)
                </>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Inference</dt>
            <dd className="font-medium text-slate-950">
              {pa.vision_backend === "gemini_vision" ? "Gemini vision on Sentinel-2 chip" : "None (no successful inference)"}
              {pa.inference_model ? ` · ${pa.inference_model}` : ""}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Imagery</dt>
            <dd className="font-medium text-slate-950">
              {pa.imagery_source !== "none" ? pa.imagery_source : "—"}
              {pa.imagery_provider ? ` · ${pa.imagery_provider}` : ""}
              {pa.imagery_date_range ? ` · ${pa.imagery_date_range}` : ""}
            </dd>
          </div>
          {pa.inference_timestamp_utc ? (
            <div className="sm:col-span-2">
              <dt className="text-xs uppercase tracking-wider text-slate-500">Inference time (UTC)</dt>
              <dd className="font-medium text-slate-950">{pa.inference_timestamp_utc}</dd>
            </div>
          ) : null}
        </dl>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-xs leading-relaxed text-slate-600">
        <p className="font-semibold text-slate-800">Data notes</p>
        <p className="mt-2">{building.data_notes}</p>
        {mapHref && (
          <a
            href={mapHref}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block font-medium text-cyan-700 underline decoration-cyan-400/50 hover:text-cyan-900"
          >
            Open location in Maps
          </a>
        )}
      </div>
    </div>
  );
}
