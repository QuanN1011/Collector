"use client";

import type { ProspectingModel } from "../../lib/useProspecting";
import { apiBaseUrl } from "../../lib/api";
import { mapsJsKey } from "@/lib/googleMapsLoader";
import InteractiveSatelliteMap from "./InteractiveSatelliteMap";
import NexusAnalysisResults from "./NexusAnalysisResults";
import PlacesAutocompleteInput from "./PlacesAutocompleteInput";

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

  const showSatellite =
    p.addressAnalyzeResult != null ||
    (p.buildingDetail?.roof_area_sqft_catalog != null && p.addressAnalyzeResult == null);

  const latForMap = p.addressAnalyzeResult?.lat ?? p.buildingDetail?.latitude ?? null;
  const lngForMap = p.addressAnalyzeResult?.lng ?? p.buildingDetail?.longitude ?? null;

  const canRun =
    !!p.selectedState && (p.streetAddress.trim().length > 0 || !!p.selectedBuildingId) && !p.satelliteLoading;

  return (
    <section
      id="rainuse-nexus"
      className="relative z-[20] scroll-mt-24 border-y border-cyan-200/40 bg-gradient-to-b from-cyan-50/40 via-white to-white py-20 px-6 sm:px-10 lg:px-16"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="inline-flex rounded-full bg-cyan-500/15 px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-800">
                RainUSE Nexus
              </p>
              <h2 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">Site Prospecting Engine</h2>
            </div>
            <div className="space-y-2 border-l-2 border-cyan-400/60 pl-4">
              <p className="inline-flex rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-700">
                Prospecting
              </p>
              <h3 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">Sites &amp; viability</h3>
              <p className="max-w-2xl text-slate-700">
                Choose <strong>state</strong> and <strong>building</strong>, then <strong>Run satellite analysis</strong>. Add an
                address only if you want the geocoded pipeline instead of the catalog row.
              </p>
            </div>
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
            <a
              href="#rainuse-api-key"
              className="rounded-full border border-cyan-200 bg-cyan-50/80 px-4 py-2 text-xs font-semibold text-cyan-900 transition hover:bg-cyan-100/80"
            >
              Get API key
            </a>
          </div>
        </div>

        {p.error && (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">{p.error}</div>
        )}

        {/* TOP INPUT CARD — aligned label row + control row */}
        <div className="pointer-events-auto relative z-[1] mb-8 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-12 lg:items-end lg:gap-x-4">
            <div className="flex min-w-0 flex-col gap-2 lg:col-span-2">
              <span className="text-sm font-semibold leading-5 text-slate-800">State</span>
              <select
                value={p.selectedState}
                onChange={(e) => p.setSelectedState(e.target.value)}
                disabled={p.loadingStates || p.states.length === 0}
                className="h-11 w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3 text-sm text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60"
              >
                {p.states.length === 0 && !p.loadingStates ? <option value="">No states</option> : null}
                {p.states.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex min-w-0 flex-col gap-2 lg:col-span-4">
              <span className="text-sm font-semibold leading-5 text-slate-800">Building</span>
              <select
                value={p.selectedBuildingId}
                onChange={(e) => p.setSelectedBuildingId(e.target.value)}
                disabled={p.loadingBuildings || p.buildings.length === 0}
                className="h-11 w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3 text-sm text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60"
              >
                {p.buildings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                    {b.city ? ` — ${b.city}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex min-w-0 flex-col gap-2 lg:col-span-4">
              <div className="flex h-5 min-h-[1.25rem] items-center justify-between gap-2">
                <span className="text-sm font-semibold leading-5 text-slate-800">
                  Address <span className="font-normal text-slate-400">(optional)</span>
                </span>
                {p.streetAddress ? (
                  <button
                    type="button"
                    onClick={() => p.setStreetAddress("")}
                    className="shrink-0 text-xs font-medium text-cyan-700 hover:text-cyan-900"
                  >
                    Clear
                  </button>
                ) : (
                  <span className="w-10 shrink-0" aria-hidden="true"></span>
                )}
              </div>
              <div className="places-autocomplete-host flex min-h-[2.75rem] items-center rounded-xl border border-cyan-200/60 bg-gradient-to-b from-cyan-50/50 to-slate-50/40 px-1 shadow-sm shadow-cyan-900/5">
                {mapsJsKey ? (
                  <PlacesAutocompleteInput
                    placeholder="Search places or addresses"
                    disabled={p.satelliteLoading}
                    value={p.streetAddress}
                    onValueChange={p.setStreetAddress}
                    onPlaceResolved={(place) => p.setStreetAddress(place.formattedAddress)}
                    className="!min-h-[2.5rem] !border-0 !bg-transparent !shadow-none"
                  />
                ) : (
                  <input
                    type="text"
                    value={p.streetAddress}
                    onChange={(e) => p.setStreetAddress(e.target.value)}
                    disabled={p.satelliteLoading}
                    placeholder="Type an address"
                    className="h-11 w-full rounded-lg border-0 bg-transparent px-3 text-sm text-slate-950 outline-none focus:ring-0 disabled:opacity-60"
                  />
                )}
              </div>
            </div>

            <div className="flex flex-col gap-2 lg:col-span-2">
              <span className="h-5 min-h-[1.25rem] text-sm font-semibold leading-5 text-transparent select-none" aria-hidden>
                Run
              </span>
              <button
                type="button"
                disabled={!canRun}
                onClick={() => void p.runSatelliteAnalysis()}
                className="flex h-11 w-full items-center justify-center rounded-full bg-slate-950 px-4 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-800 disabled:opacity-50"
              >
                {p.satelliteLoading ? "Running…" : "Run satellite analysis"}
              </button>
            </div>
          </div>
        </div>

        {/* SATELLITE */}
        <div className="mb-10">
          {showSatellite ? (
            <div className="grid gap-6 lg:grid-cols-2">
              {p.addressAnalyzeResult ? (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600">Static satellite (API chip)</h4>
                  {/* eslint-disable-next-line @next/next/no-img-element -- signed Static Maps URL from API */}
                  <img
                    src={p.addressAnalyzeResult.satellite_image}
                    alt="Satellite view from Google Static Maps"
                    className="w-full rounded-2xl border border-slate-200 object-cover shadow-sm"
                  />
                </div>
              ) : (
                <div className="flex flex-col justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 p-6 text-sm text-slate-600">
                  <p className="font-semibold text-slate-800">Catalog building analysis</p>
                  <p className="mt-2 text-xs leading-relaxed">
                    Satellite imagery was fetched on the server (Static Maps + Gemini). Use the hybrid map for visual context.
                  </p>
                </div>
              )}
              {latForMap != null && lngForMap != null ? (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600">Interactive map</h4>
                  <InteractiveSatelliteMap lat={latForMap} lng={lngForMap} />
                  <a
                    href={`https://www.google.com/maps?q=${latForMap},${lngForMap}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-cyan-700 underline decoration-cyan-400/50 hover:text-cyan-900"
                  >
                    Open in Google Maps
                  </a>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-6 py-8 text-center text-sm text-slate-600">
              Satellite imagery and map appear here after you run analysis.
            </div>
          )}
        </div>

        {/* ANALYSIS RESULTS */}
        <NexusAnalysisResults
          loading={
            p.satelliteLoading || (!!p.selectedBuildingId && p.loadingDetail && !p.buildingDetail && !p.addressAnalyzeResult)
          }
          analyzeResult={p.addressAnalyzeResult}
          building={p.addressAnalyzeResult ? null : p.buildingDetail}
          stateContextBuilding={p.stateContextSample}
        />

        <div className="mt-8">
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-950">Top prospects</h3>
              <p className="text-sm text-slate-600">Sorted by viability for the selected state.</p>
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
                      {row.cooling_tower_detected ? `Yes (${(row.cooling_tower_confidence * 100).toFixed(0)}%)` : "No"}
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
