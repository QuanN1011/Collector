"use client";

import type { ProspectingModel } from "../../lib/useProspecting";
import { apiBaseUrl } from "../../lib/api";
import BuildingInsights from "./BuildingInsights";

export default function ProspectingSection({ model }: { model: ProspectingModel }) {
  const p = model;

  const healthLabel =
    p.health === "ok" ? "Connected" : p.health === "checking" ? "Checking…" : "Offline";

  const healthClass =
    p.health === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : p.health === "checking"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : "border-rose-200 bg-rose-50 text-rose-900";

  return (
    <section id="prospecting" className="relative scroll-mt-24 py-20 px-6 sm:px-10 lg:px-16 bg-white">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-3">
            <p className="inline-flex rounded-full bg-cyan-500/10 px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-700">
              Prospecting
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">Sites & viability</h2>
            <p className="max-w-2xl text-slate-700">
              Pick a state and building to load rankings, economics, and optional satellite-backed cooling signals. Use the
              section below to explore state water rates and rainwater value for the same site.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-wider ${healthClass}`}>
              {healthLabel}
            </span>
            <button
              type="button"
              onClick={() => void p.refreshHealth()}
              className="rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-800 transition hover:bg-slate-50"
            >
              Check connection
            </button>
            <a
              href={`${apiBaseUrl}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-800 transition hover:bg-slate-50"
            >
              API reference
            </a>
          </div>
        </div>

        {p.error && (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">{p.error}</div>
        )}

        <div className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-slate-200 bg-slate-50 p-6 sm:flex-row sm:flex-wrap sm:items-end">
          <label className="flex min-w-[140px] flex-1 flex-col gap-2 text-sm">
            <span className="font-semibold text-slate-800">State</span>
            <select
              value={p.selectedState}
              onChange={(e) => p.setSelectedState(e.target.value)}
              disabled={p.loadingStates || p.states.length === 0}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60"
            >
              {p.states.length === 0 && !p.loadingStates ? <option value="">No states in dataset</option> : null}
              {p.states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-w-[220px] flex-[2] flex-col gap-2 text-sm">
            <span className="font-semibold text-slate-800">Building</span>
            <select
              value={p.selectedBuildingId}
              onChange={(e) => p.setSelectedBuildingId(e.target.value)}
              disabled={p.loadingBuildings || p.buildings.length === 0}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60"
            >
              {p.buildings.length === 0 && !p.loadingBuildings && p.selectedState ? (
                <option value="">No buildings loaded for this state</option>
              ) : null}
              {p.buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                  {b.city ? ` — ${b.city}` : ""}
                </option>
              ))}
            </select>
          </label>

          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-800 sm:min-w-[280px]">
            <input
              type="checkbox"
              checked={p.liveCv}
              onChange={(e) => p.setLiveCv(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
            />
            <span>
              Satellite + AI refresh{" "}
              <span className="text-xs font-normal text-slate-500">(slower; needs Earth Engine &amp; Gemini configured)</span>
            </span>
          </label>
        </div>

        <BuildingInsights building={p.buildingDetail} loading={p.loadingDetail} />

        <div className="mt-12">
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-950">Top prospects</h3>
              <p className="text-sm text-slate-600">
                Sorted by viability score for the state you selected (partial scores omit cooling tower when live CV is off).
              </p>
            </div>
            <button
              type="button"
              onClick={() => void p.refreshTopProspects()}
              disabled={p.loadingTop || !p.selectedState}
              className="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
            >
              {p.loadingTop ? "Loading…" : "Refresh rankings"}
            </button>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">#</th>
                  <th className="px-4 py-3 font-semibold">Building</th>
                  <th className="px-4 py-3 font-semibold">City</th>
                  <th className="px-4 py-3 font-semibold">Viability</th>
                  <th className="px-4 py-3 font-semibold">Savings $/yr</th>
                  <th className="px-4 py-3 font-semibold">Large roof</th>
                  <th className="px-4 py-3 font-semibold">Tower</th>
                  <th className="px-4 py-3 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {p.topProspects.length === 0 && !p.loadingTop ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                      No rankings loaded yet.
                    </td>
                  </tr>
                ) : null}
                {p.topProspects.map((row, i) => (
                  <tr key={row.id} className={row.id === p.selectedBuildingId ? "bg-cyan-50/60" : "hover:bg-slate-50/80"}>
                    <td className="px-4 py-3 text-slate-600">{i + 1}</td>
                    <td className="px-4 py-3 font-medium text-slate-950">{row.name}</td>
                    <td className="px-4 py-3 text-slate-600">{row.city ?? "—"}</td>
                    <td className="px-4 py-3 font-semibold text-cyan-800">{row.viability_score.toFixed(1)}</td>
                    <td className="px-4 py-3 text-slate-700">${row.annual_water_savings.toLocaleString()}</td>
                    <td className="px-4 py-3 text-slate-700">{row.physical_analysis.large_roof ? "Yes" : "No"}</td>
                    <td className="px-4 py-3 text-slate-700">
                      {row.physical_analysis.tower_status === "unavailable"
                        ? "Unavailable"
                        : row.cooling_tower_detected
                          ? `Yes (${((row.cooling_tower_confidence ?? 0) * 100).toFixed(0)}%)`
                          : `No (${((row.cooling_tower_confidence ?? 0) * 100).toFixed(0)}%)`}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => p.setSelectedBuildingId(row.id)}
                        className="font-semibold text-cyan-700 underline decoration-cyan-400/40 hover:text-cyan-900"
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
