"use client";

import type { BuildingEnriched } from "../../lib/types";

const BREAKDOWN_LABELS: Record<string, string> = {
  rainfall: "Rainfall",
  water_price: "Water price",
  cooling_tower: "Cooling tower signal",
  esg_mock: "ESG (demo)",
};

function BarRow({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span className="font-medium text-slate-800">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-cyan-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
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

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-800">Viability score</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{building.viability_score.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-600">0–100 composite score</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual savings proxy</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">${building.annual_water_savings.toLocaleString()}</p>
          <p className="mt-1 text-xs text-slate-500">Rainwater offset at state reference water rate</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">ESG signal (demo)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{building.esg_signal_score.toFixed(0)}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual rainfall (state)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{building.rainfall_inches_annual.toFixed(1)} in</p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-slate-950">Viability breakdown</h3>
        <p className="mt-1 text-xs text-slate-500">How each factor contributes to the overall score.</p>
        <div className="mt-4 space-y-3">
          {Object.entries(building.viability_breakdown).map(([key, val]) => (
            <BarRow key={key} label={BREAKDOWN_LABELS[key] ?? key} value={val} />
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-slate-950">Site imagery &amp; cooling signal</h3>
        <p className="mt-1 text-xs text-slate-500">
          Roof area comes from catalog data; cooling cues may use satellite imagery and AI when enabled.
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
            <dt className="text-xs uppercase tracking-wider text-slate-500">Roof confidence (catalog lineage)</dt>
            <dd className="font-medium text-slate-950">{(pa.roof_confidence * 100).toFixed(0)}%</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs uppercase tracking-wider text-slate-500">Catchment provenance</dt>
            <dd className="font-medium text-slate-950">{pa.roof_catchment_provenance}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Cooling tower</dt>
            <dd className="font-medium text-slate-950">
              {pa.cooling_tower_detected ? "Detected" : "Not detected"} ({(pa.cooling_tower_confidence * 100).toFixed(0)}% conf.)
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-slate-500">Analysis mode</dt>
            <dd className="font-medium text-slate-950">
              {pa.vision_backend === "gemini_vision" ? "Satellite + AI" : "Standard (catalog)"}
              {pa.imagery_source !== "none" ? ` · ${pa.imagery_source}` : ""}
            </dd>
          </div>
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
