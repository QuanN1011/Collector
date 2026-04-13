"use client";

import type { AnalyzeBuildingResponse, BuildingEnriched } from "@/lib/types";

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

function FinalViabilityFour({
  viability,
  roofSqft,
  roofSubtitle,
  largeRoof,
  coolingDetected,
  coolingConf,
  esg,
  esgNote,
}: {
  viability: number;
  roofSqft: number;
  roofSubtitle: string;
  largeRoof: boolean;
  coolingDetected: boolean;
  coolingConf: number;
  esg: number | null;
  esgNote?: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-950">Final viability</h3>
      <p className="mt-1 text-xs text-slate-500">Composite score and key physical signals from vision + defaults.</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-800">Viability score</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{viability.toFixed(1)}</p>
          <p className="mt-1 text-xs text-slate-600">0–100 composite</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Roof (vision + defaults)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{roofSqft.toLocaleString()} sq ft</p>
          <p className="mt-1 text-xs text-slate-600">{roofSubtitle}</p>
          <p className="mt-2 text-xs font-semibold text-cyan-800">Large roof (≥100k): {largeRoof ? "Yes" : "No"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Cooling tower</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{coolingDetected ? "Likely" : "Not detected"}</p>
          <p className="mt-1 text-xs text-slate-600">Confidence {(coolingConf * 100).toFixed(0)}%</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">ESG signal</p>
          {esg != null ? (
            <>
              <p className="mt-2 text-xl font-semibold text-slate-950">{esg.toFixed(0)}</p>
              <p className="mt-1 text-xs text-slate-600">Demo subscore (catalog rubric)</p>
            </>
          ) : (
            <>
              <p className="mt-2 text-xl font-semibold text-slate-400">—</p>
              <p className="mt-1 text-xs text-slate-500">{esgNote ?? "Not returned by address pipeline"}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function WaterEconomicsThree({
  rainfallIn,
  gallons,
  savingsUsd,
  rainfallNote,
}: {
  rainfallIn: number | null;
  gallons: number;
  savingsUsd: number;
  rainfallNote?: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-950">Water economics</h3>
      <p className="mt-1 text-xs text-slate-500">
        State reference rainfall and rate where available; capture and savings from the active analysis.
      </p>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual rainfall (state)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">
            {rainfallIn != null ? `${rainfallIn.toFixed(1)} in` : "—"}
          </p>
          {rainfallNote ? <p className="mt-1 text-xs text-slate-500">{rainfallNote}</p> : null}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Annual rainwater capture (gal)</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{Math.round(gallons).toLocaleString()}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Estimated annual savings</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">${Math.round(savingsUsd).toLocaleString()}</p>
          <p className="mt-1 text-xs text-slate-500">At reference $/1k gal</p>
        </div>
      </div>
    </div>
  );
}

export default function NexusAnalysisResults({
  loading,
  analyzeResult,
  building,
  stateContextBuilding,
}: {
  loading: boolean;
  analyzeResult: AnalyzeBuildingResponse | null;
  building: BuildingEnriched | null;
  stateContextBuilding: BuildingEnriched | null;
}) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-sm text-slate-600">Running analysis…</div>
    );
  }

  if (analyzeResult) {
    const ctx = stateContextBuilding;
    return (
      <div className="space-y-8">
        <FinalViabilityFour
          viability={analyzeResult.viability_score}
          roofSqft={analyzeResult.roof_area_sqft}
          roofSubtitle={`Estimate: ${analyzeResult.roof_estimate}`}
          largeRoof={analyzeResult.roof_area_sqft >= 100_000}
          coolingDetected={analyzeResult.cooling_tower_detected}
          coolingConf={analyzeResult.cooling_tower_confidence}
          esg={null}
          esgNote="Use a catalog building for demo ESG in the full /building rubric."
        />
        <WaterEconomicsThree
          rainfallIn={ctx?.rainfall_inches_annual ?? null}
          gallons={analyzeResult.rainwater_potential_gallons}
          savingsUsd={analyzeResult.annual_water_savings}
          rainfallNote={ctx ? undefined : "Load buildings for this state to show reference rainfall."}
        />
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-xs leading-relaxed text-slate-600">
          <p className="font-semibold text-slate-800">Address pipeline</p>
          <p className="mt-2">
            {analyzeResult.address} · {analyzeResult.lat.toFixed(5)}, {analyzeResult.lng.toFixed(5)}
          </p>
          <p className="mt-2">
            Powered by <code className="rounded bg-white px-1">GET /analyze-building</code> (Geocoding + Static Maps +
            Gemini). Viability breakdown bars are shown for catalog <code className="rounded bg-white px-1">/building</code>{" "}
            responses.
          </p>
        </div>
      </div>
    );
  }

  if (!building) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-8 text-sm text-slate-600">
        Select a state and building, optionally enter an address, then run satellite analysis.
      </div>
    );
  }

  const pa = building.physical_analysis;
  const mapHref =
    building.latitude != null && building.longitude != null
      ? `https://www.google.com/maps?q=${building.latitude},${building.longitude}`
      : null;

  return (
    <div className="space-y-8">
      <FinalViabilityFour
        viability={building.viability_score}
        roofSqft={pa.roof_catchment_sqft}
        roofSubtitle={pa.roof_catchment_provenance.replace(/_/g, " ")}
        largeRoof={pa.large_roof}
        coolingDetected={pa.cooling_tower_detected}
        coolingConf={pa.cooling_tower_confidence}
        esg={building.esg_signal_score}
      />
      <WaterEconomicsThree
        rainfallIn={building.rainfall_inches_annual}
        gallons={building.rainwater_potential_gallons}
        savingsUsd={building.annual_water_savings}
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-slate-950">Viability breakdown</h3>
        <p className="mt-1 text-xs text-slate-500">How each factor contributes to the overall score.</p>
        <div className="mt-4 space-y-3">
          {Object.entries(building.viability_breakdown).map(([key, val]) => (
            <BarRow key={key} label={BREAKDOWN_LABELS[key] ?? key} value={val} />
          ))}
        </div>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-xs leading-relaxed text-slate-600">
        <p className="font-semibold text-slate-800">Data notes</p>
        <p className="mt-2">{building.data_notes}</p>
        {building.cv_reasoning ? (
          <p className="mt-2">
            <span className="font-semibold text-slate-800">CV reasoning: </span>
            {building.cv_reasoning}
          </p>
        ) : null}
        {mapHref ? (
          <a
            href={mapHref}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block font-medium text-cyan-700 underline decoration-cyan-400/50 hover:text-cyan-900"
          >
            Open location in Maps
          </a>
        ) : null}
      </div>
    </div>
  );
}
