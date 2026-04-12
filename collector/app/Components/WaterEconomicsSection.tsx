"use client";

import { useMemo, useState } from "react";
import type { BuildingEnriched } from "../../lib/types";

/** Same formula as backend `services/roi.py`. */
function annualWaterSavingsUsd(gallonsAnnual: number, pricePer1000Gal: number): number {
  return (gallonsAnnual / 1000) * pricePer1000Gal;
}

/**
 * Illustrative only: maps $/1000 gal to a rough monthly bill using ~12k gal/month
 * (typical “family of four” order of magnitude; see backend/docs/DATA_SOURCES_WATER_PRICING.md).
 */
const ILLUSTRATIVE_GALLONS_PER_MONTH = 12_000;

function formatNumber(value: number, digits = 1) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

export default function WaterEconomicsSection({
  building,
  loading,
  backendError,
}: {
  building: BuildingEnriched | null;
  loading: boolean;
  backendError: string;
}) {
  const [ratePct, setRatePct] = useState(100);

  const basePrice = building?.water_price_per_1000_gal_usd ?? 0;
  const stressedPrice = basePrice * (ratePct / 100);
  const stressedSavings = building ? annualWaterSavingsUsd(building.rainwater_potential_gallons, stressedPrice) : 0;

  const impliedMonthlyBill = useMemo(() => {
    if (!building) return 0;
    return (building.water_price_per_1000_gal_usd / 1000) * ILLUSTRATIVE_GALLONS_PER_MONTH;
  }, [building]);

  const dailyCaptureGal = building ? building.rainwater_potential_gallons / 365 : 0;

  return (
    <div className="grid gap-8 lg:grid-cols-[1.15fr_1fr]">
      <div className="space-y-6 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)] sm:p-10">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">State water context (US)</p>
          <h3 className="mt-2 text-xl font-semibold text-slate-950">Rates &amp; rainfall</h3>
          <p className="mt-2 text-sm text-slate-600">
            Reference values come from the RainUSE state dataset (rainfall and water rate per 1,000 gallons). Update those
            values to match public state water rankings or tariffs—then every building in that state picks them up automatically.
          </p>
        </div>

        {backendError ? <p className="text-sm text-rose-700">{backendError}</p> : null}

        {loading ? (
          <p className="text-sm text-slate-600">Loading site context…</p>
        ) : !building ? (
          <p className="text-sm text-slate-600">Select a building above to see state water economics for that site.</p>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-cyan-200 bg-cyan-50/50 p-4">
                <p className="text-[11px] uppercase tracking-wider text-cyan-800">State</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">{building.state}</p>
                <p className="mt-1 text-xs text-slate-600">Applied to {building.name}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wider text-slate-600">Reference water rate</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">${basePrice.toFixed(2)}</p>
                <p className="mt-1 text-xs text-slate-600">per 1,000 gallons (potable proxy)</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wider text-slate-600">Annual rainfall (state)</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">{building.rainfall_inches_annual.toFixed(1)} in</p>
                <p className="mt-1 text-xs text-slate-600">Used in capture modeling</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wider text-slate-600">Illustrative residential bill</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">${impliedMonthlyBill.toFixed(0)}</p>
                <p className="mt-1 text-xs text-slate-600">
                  ~{ILLUSTRATIVE_GALLONS_PER_MONTH.toLocaleString()} gal/mo at this rate — compare to state “avg bill” tables
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-6 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)] sm:p-10">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">This site</p>
          <h3 className="mt-2 text-xl font-semibold text-slate-950">Rainwater value</h3>
          <p className="mt-2 text-sm text-slate-600">
            Annual value if harvested water offsets potable purchases at the reference rate (same logic as the API).
          </p>
        </div>

        {!building || loading ? (
          <p className="text-sm text-slate-500">{loading ? "Loading…" : "Select a building to run the scenario."}</p>
        ) : (
          <>
            <div className="grid gap-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wider text-slate-600">Modeled annual capture</p>
                <p className="mt-1 text-xl font-semibold text-slate-950">
                  {Math.round(building.rainwater_potential_gallons).toLocaleString()} gal/yr
                </p>
                <p className="mt-1 text-xs text-slate-600">~{formatNumber(dailyCaptureGal, 0)} gal/day average</p>
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4">
                <p className="text-[11px] uppercase tracking-wider text-emerald-900">Annual offset value (API)</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">${building.annual_water_savings.toLocaleString()}</p>
                <p className="mt-1 text-xs text-slate-600">At {building.state} reference ${basePrice.toFixed(2)}/1k gal</p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <label htmlFor="water-price-sensitivity" className="block text-sm font-semibold text-slate-950">
                Water price sensitivity
              </label>
              <p className="mt-1 text-xs text-slate-600">
                See how annual value changes as water price varies from the reference rate.
              </p>
              <input
                id="water-price-sensitivity"
                type="range"
                min={70}
                max={150}
                value={ratePct}
                onChange={(e) => setRatePct(Number(e.target.value))}
                className="mt-4 w-full"
              />
              <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>70%</span>
                <span className="font-medium text-slate-800">{ratePct}%</span>
                <span>150%</span>
              </div>
              <p className="mt-4 text-center text-lg font-semibold text-cyan-900">
                ${formatNumber(stressedSavings, 0)}<span className="text-sm font-normal text-slate-600"> /yr estimated</span>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
