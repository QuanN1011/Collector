"use client";

import { useMemo, useState } from "react";
import InteractiveTopUI from "./Components/InteractiveTopUI";

type BuildingEnriched = {
  id: string;
  name: string;
  state: string;
  city?: string | null;
  roof_area_sqft: number;
  rainfall_inches_annual: number;
  water_price_per_1000_gal_usd: number;
  rainwater_potential_gallons: number;
  annual_water_savings: number;
  viability_score: number;
  viability_breakdown: Record<string, number>;
  cooling_tower_detected: boolean;
  cooling_tower_confidence: number;
  esg_signal_score: number;
  data_notes: string;
};

const INITIALS = {
  dailyVolume: 250,
  sourceElevation: 100,
  destinationElevation: 132,
  pipeLength: 2,
  pumpEfficiency: 72,
  pumpCount: 1,
};

/** Static sample row for the mock UI (swap for live API data when wired). */
const MOCK_BUILDING: BuildingEnriched = {
  id: "demo-1",
  name: "Austin Logistics Hub",
  state: "TX",
  city: "Austin",
  roof_area_sqft: 128_000,
  rainfall_inches_annual: 34,
  water_price_per_1000_gal_usd: 4.25,
  rainwater_potential_gallons: 2_450_000,
  annual_water_savings: 180_000,
  viability_score: 0.82,
  viability_breakdown: {},
  cooling_tower_detected: true,
  cooling_tower_confidence: 0.71,
  esg_signal_score: 0.76,
  data_notes: "Demo dataset",
};

function formatNumber(value: number, digits = 1) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

export default function Home() {
  const [dailyVolume, setDailyVolume] = useState(INITIALS.dailyVolume);
  const [sourceElevation, setSourceElevation] = useState(INITIALS.sourceElevation);
  const [destinationElevation, setDestinationElevation] = useState(
    INITIALS.destinationElevation,
  );
  const [pipeLength, setPipeLength] = useState(INITIALS.pipeLength);
  const [pumpEfficiency, setPumpEfficiency] = useState(INITIALS.pumpEfficiency);
  const [pumpCount, setPumpCount] = useState(INITIALS.pumpCount);

  const backendBuilding = MOCK_BUILDING;

  const estimate = useMemo(() => {
    const flowRate = dailyVolume / 86400;
    const flowLps = flowRate * 1000;
    const elevationGain = Math.max(destinationElevation - sourceElevation, 0);
    const head = elevationGain + 10 + pipeLength * 2;
    const efficiency = Math.max(0.2, Math.min(pumpEfficiency / 100, 1));
    const powerKw = (9.81 * 1000 * flowRate * head) / (1000 * efficiency);
    const energyKwh = powerKw * 24;
    const costPerDay = energyKwh * 0.18;
    const suggestedPumps = Math.max(
      1,
      Math.ceil(flowLps / 20),
    );

    return {
      flowLps,
      head,
      powerKw,
      energyKwh,
      costPerDay,
      suggestedPumps,
    };
  }, [dailyVolume, destinationElevation, sourceElevation, pipeLength, pumpEfficiency]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Interactive TopUI Background */}
      <InteractiveTopUI />

      {/* Valve Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-30"
        style={{ zIndex: 2 }}
      >
        <source src="/Valve Oil Gauge Video.mp4" type="video/mp4" />
      </video>

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/80 via-slate-950/70 to-slate-950/95" style={{ zIndex: 3 }} />
      <main className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-10 px-6 py-12 sm:px-10 lg:px-16" style={{ zIndex: 4 }}>
        <section className="grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-start">
          <div className="rounded-[32px] border border-white/10 bg-slate-950/80 p-8 shadow-2xl shadow-slate-950/40 backdrop-blur-xl sm:p-10">
            <span className="inline-flex rounded-full bg-cyan-500/15 px-4 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">
              Pumping Optimizer
            </span>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              Water Pumping Cost & Energy Optimizer
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
              Configure the source, destination, and pipe conditions to estimate pumping head,
              energy consumption, and the best pump arrangement for reliable operation.
            </p>
            <div className="mt-8 rounded-3xl border border-white/10 bg-slate-900/80 p-5 text-sm text-slate-300 shadow-inner shadow-black/5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Building data (demo)</p>
                  <p className="mt-2 text-base font-semibold text-white">{backendBuilding.name}</p>
                </div>
                <div className="rounded-3xl bg-slate-950/90 px-4 py-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {backendBuilding.state}
                </div>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-3xl bg-slate-950/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Roof area</p>
                  <p className="mt-2 text-sm font-semibold text-white">{backendBuilding.roof_area_sqft.toLocaleString()} sqft</p>
                </div>
                <div className="rounded-3xl bg-slate-950/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Annual capture</p>
                  <p className="mt-2 text-sm font-semibold text-white">{Math.round(backendBuilding.rainwater_potential_gallons).toLocaleString()} gal</p>
                </div>
                <div className="rounded-3xl bg-slate-950/80 p-3">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Water cost</p>
                  <p className="mt-2 text-sm font-semibold text-white">${backendBuilding.water_price_per_1000_gal_usd.toFixed(2)}/1000 gal</p>
                </div>
              </div>
            </div>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              <label className="space-y-2 rounded-3xl bg-slate-900/80 p-4 text-sm text-slate-300 shadow-inner shadow-black/10">
                <span className="font-semibold text-slate-100">Daily volume</span>
                <input
                  type="number"
                  value={dailyVolume}
                  onChange={(event) => setDailyVolume(Number(event.target.value))}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
                  min={10}
                />
                <p className="text-xs text-slate-500">m³ per day</p>
              </label>

              <label className="space-y-2 rounded-3xl bg-slate-900/80 p-4 text-sm text-slate-300 shadow-inner shadow-black/10">
                <span className="font-semibold text-slate-100">Pump efficiency</span>
                <input
                  type="range"
                  min={30}
                  max={95}
                  value={pumpEfficiency}
                  onChange={(event) => setPumpEfficiency(Number(event.target.value))}
                  className="w-full"
                />
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{pumpEfficiency}%</span>
                  <span>Efficiency</span>
                </div>
              </label>

              <label className="space-y-2 rounded-3xl bg-slate-900/80 p-4 text-sm text-slate-300 shadow-inner shadow-black/10">
                <span className="font-semibold text-slate-100">Source elevation</span>
                <input
                  type="number"
                  value={sourceElevation}
                  onChange={(event) => setSourceElevation(Number(event.target.value))}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
                />
                <p className="text-xs text-slate-500">meters</p>
              </label>

              <label className="space-y-2 rounded-3xl bg-slate-900/80 p-4 text-sm text-slate-300 shadow-inner shadow-black/10">
                <span className="font-semibold text-slate-100">Destination elevation</span>
                <input
                  type="number"
                  value={destinationElevation}
                  onChange={(event) => setDestinationElevation(Number(event.target.value))}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
                />
                <p className="text-xs text-slate-500">meters</p>
              </label>

              <label className="space-y-2 rounded-3xl bg-slate-900/80 p-4 text-sm text-slate-300 shadow-inner shadow-black/10 sm:col-span-2">
                <span className="font-semibold text-slate-100">Pipeline length</span>
                <input
                  type="number"
                  value={pipeLength}
                  onChange={(event) => setPipeLength(Number(event.target.value))}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
                  min={0.1}
                  step={0.1}
                />
                <p className="text-xs text-slate-500">kilometers</p>
              </label>
            </div>
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <button
                type="button"
                onClick={() => setPumpCount(estimate.suggestedPumps)}
                className="rounded-3xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
              >
                Use Suggested Pump Count
              </button>
              <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-4 text-sm text-slate-300">
                <div className="flex items-center justify-between text-slate-200">
                  <span className="font-semibold">Selected pumps</span>
                  <span>{pumpCount}</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={6}
                  value={pumpCount}
                  onChange={(event) => setPumpCount(Number(event.target.value))}
                  className="mt-3 w-full"
                />
              </div>
            </div>
          </div>

          <aside className="space-y-6 rounded-[32px] border border-white/10 bg-slate-950/70 p-8 shadow-2xl shadow-slate-950/40 backdrop-blur-xl sm:p-10">
            <div className="space-y-4">
              <div className="rounded-3xl bg-slate-900/80 p-5">
                <h2 className="text-lg font-semibold text-white">Optimizer summary</h2>
                <p className="mt-2 text-sm text-slate-400">Estimated energy, head, and cost for your configuration.</p>
              </div>
              <div className="grid gap-4 text-sm">
                <div className="rounded-3xl bg-slate-900/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Flow</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{formatNumber(estimate.flowLps, 2)} L/s</p>
                </div>
                <div className="rounded-3xl bg-slate-900/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Total head</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{formatNumber(estimate.head, 1)} m</p>
                </div>
                <div className="rounded-3xl bg-slate-900/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Installed power</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{formatNumber(estimate.powerKw, 2)} kW</p>
                </div>
                <div className="rounded-3xl bg-slate-900/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Daily energy</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{formatNumber(estimate.energyKwh, 1)} kWh</p>
                </div>
                <div className="rounded-3xl bg-slate-900/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Cost estimate</p>
                  <p className="mt-3 text-3xl font-semibold text-white">${formatNumber(estimate.costPerDay, 2)}</p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl bg-slate-900/80 p-5 text-sm text-slate-300">
              <h3 className="font-semibold text-white">Notes</h3>
              <ul className="mt-4 space-y-3 list-disc pl-5 text-slate-400">
                <li>Elevation gain is based on destination minus source elevation.</li>
                <li>A fixed friction allowance is added for pipeline length.</li>
                <li>Energy cost uses a baseline of $0.18 per kWh.</li>
                <li>Optimize pump count to balance flow and redundancy.</li>
              </ul>
            </div>
          </aside>
        </section>

        <section className="grid gap-6 lg:grid-cols-[3fr_2fr]">
          <div className="rounded-[32px] border border-white/10 bg-slate-950/80 p-8 shadow-2xl shadow-slate-950/40 backdrop-blur-xl sm:p-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-cyan-300/80">Topographic model</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">Terrain and Pumping Path</h2>
              </div>
              <span className="rounded-full bg-white/10 px-4 py-2 text-xs text-slate-300">
                Elevation profile</span>
            </div>
            <div className="mt-8 rounded-[28px] bg-slate-900/80 p-6 text-slate-300">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl bg-slate-950/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">From</p>
                  <p className="mt-3 text-lg font-semibold text-white">{sourceElevation} m</p>
                </div>
                <div className="rounded-3xl bg-slate-950/80 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">To</p>
                  <p className="mt-3 text-lg font-semibold text-white">{destinationElevation} m</p>
                </div>
              </div>
              <div className="mt-6 overflow-hidden rounded-[26px] border border-white/10 bg-slate-950/90">
                <div className="h-72 bg-[radial-gradient(circle_at_20%_30%,rgba(56,189,248,0.26),transparent_20%),radial-gradient(circle_at_80%_20%,rgba(14,165,233,0.18),transparent_18%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(15,23,42,0.72))] p-6">
                  <div className="relative h-full overflow-hidden rounded-[22px] border border-white/5 bg-[url('/topui.jpg')] bg-cover bg-center opacity-90">
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-950/10 to-slate-950/90" />
                    <div className="absolute left-8 top-10 h-3 w-3 rounded-full bg-cyan-400 shadow-[0_0_18px_rgba(56,189,248,0.4)]" />
                    <div className="absolute right-8 bottom-16 h-3 w-3 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.32)]" />
                    <div className="absolute left-14 bottom-28 h-1.5 w-3/4 rounded-full bg-gradient-to-r from-cyan-300/80 via-cyan-100/50 to-emerald-300/60" />
                    <div className="absolute bottom-[-10px] left-0 right-0 h-4 bg-gradient-to-t from-slate-950 to-transparent" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[32px] border border-white/10 bg-slate-950/80 p-8 shadow-2xl shadow-slate-950/40 backdrop-blur-xl sm:p-10">
            <h2 className="text-2xl font-semibold text-white">Pump performance</h2>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              Use the suggested pump count and conservative efficiency estimate to size the system and forecast daily energy usage.
            </p>
            <dl className="mt-8 grid gap-4 text-sm text-slate-300">
              <div className="rounded-3xl bg-slate-900/80 p-5">
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Recommended pumps</dt>
                <dd className="mt-3 text-3xl font-semibold text-white">{estimate.suggestedPumps}</dd>
              </div>
              <div className="rounded-3xl bg-slate-900/80 p-5">
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Target pump power</dt>
                <dd className="mt-3 text-3xl font-semibold text-white">{formatNumber(estimate.powerKw / estimate.suggestedPumps, 2)} kW each</dd>
              </div>
              <div className="rounded-3xl bg-slate-900/80 p-5">
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Estimated pipeline loss</dt>
                <dd className="mt-3 text-3xl font-semibold text-white">{formatNumber(pipeLength * 2, 1)} m</dd>
              </div>
            </dl>
          </div>
        </section>
      </main>
    </div>
  );
}
