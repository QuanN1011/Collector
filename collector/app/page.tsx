"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import InteractiveTopUI from "./Components/InteractiveTopUI";
import Header from "./Components/Header";
import Footer from "./Components/Footer";

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

const BACKEND_BASE = "http://localhost:8000";

function formatNumber(value: number, digits = 1) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function HeroLines() {
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-50" viewBox="0 0 1200 800" preserveAspectRatio="none">
      <path
        d="M40 580 C220 520 380 660 560 590 C780 500 920 620 1160 520"
        fill="none"
        stroke="#0891b2"
        strokeWidth="2"
        className="animate-stroke"
      />
      <path
        d="M40 400 C240 340 420 460 620 420 C820 380 940 520 1160 430"
        fill="none"
        stroke="#22d3ee"
        strokeWidth="1.5"
        className="animate-stroke delay-200"
      />
      <circle cx="240" cy="520" r="6" fill="#06b6d4" className="animate-pulse" />
      <circle cx="820" cy="450" r="6" fill="#22d3ee" className="animate-pulse delay-100" />
      <circle cx="1040" cy="530" r="8" fill="#0ea5e9" className="animate-pulse delay-300" />
    </svg>
  );
}

export default function Home() {
  const [backendBuilding, setBackendBuilding] = useState<BuildingEnriched | null>(null);
  const [loading, setLoading] = useState(true);
  const [backendError, setBackendError] = useState("");

  const [dailyVolume, setDailyVolume] = useState(INITIALS.dailyVolume);
  const [sourceElevation, setSourceElevation] = useState(INITIALS.sourceElevation);
  const [destinationElevation, setDestinationElevation] = useState(INITIALS.destinationElevation);
  const [pipeLength, setPipeLength] = useState(INITIALS.pipeLength);
  const [pumpEfficiency, setPumpEfficiency] = useState(INITIALS.pumpEfficiency);
  const [pumpCount, setPumpCount] = useState(INITIALS.pumpCount);
    const videoScrollContainerRef = useRef<HTMLDivElement>(null);
    const [videoProgress, setVideoProgress] = useState(0);
    const [scrollPastVideo, setScrollPastVideo] = useState(0);

    useEffect(() => {
      let ticking = false;
      const handleScroll = () => {
        if (!ticking) {
          window.requestAnimationFrame(() => {
            if (!videoScrollContainerRef.current) {
              ticking = false;
              return;
            }
            const rect = videoScrollContainerRef.current.getBoundingClientRect();
            
            // We only want to animate when the container's top hits the viewport
            const scrolled = -rect.top;
            const totalScrollable = rect.height - window.innerHeight;
            
            if (totalScrollable > 0) {
              const progress = Math.max(0, Math.min(1, scrolled / totalScrollable));
              setVideoProgress(progress);
              // How far past the video container we've scrolled (0→1 over 10vh)
              const pastAmount = Math.max(0, Math.min(1, (scrolled - totalScrollable) / (window.innerHeight * 0.1)));
              setScrollPastVideo(pastAmount);
            }
            ticking = false;
          });
          ticking = true;
        }
      };

      window.addEventListener("scroll", handleScroll, { passive: true });
      handleScroll(); // Initialize on mount
      return () => window.removeEventListener("scroll", handleScroll);
    }, []);
  useEffect(() => {
    async function fetchBuilding() {
      setLoading(true);
      setBackendError("");
      try {
        const response = await fetch(`${BACKEND_BASE}/top-prospects?state=TX&limit=1`);
        if (!response.ok) throw new Error(`API error ${response.status}`);
        const data: BuildingEnriched[] = await response.json();
        if (data.length === 0) throw new Error("No backend building data available");
        const building = data[0];
        setBackendBuilding(building);
        const dailyFromPotential = Math.max(INITIALS.dailyVolume, Math.round((building.rainwater_potential_gallons / 264.172 / 365) * 100) / 100);
        setDailyVolume(dailyFromPotential);
        setSourceElevation(80);
        setDestinationElevation(95);
        setPumpCount(1);
      } catch (error) {
        setBackendError(error instanceof Error ? error.message : "Unknown backend error");
      } finally {
        setLoading(false);
      }
    }
    void fetchBuilding();
  }, []);

  const estimate = useMemo(() => {
    const flowRate = dailyVolume / 86400;
    const flowLps = flowRate * 1000;
    const elevationGain = Math.max(destinationElevation - sourceElevation, 0);
    const head = elevationGain + 10 + pipeLength * 2;
    const efficiency = Math.max(0.2, Math.min(pumpEfficiency / 100, 1));
    const powerKw = (9.81 * 1000 * flowRate * head) / (1000 * efficiency);
    const energyKwh = powerKw * 24;
    const costPerDay = energyKwh * 0.18;
    const suggestedPumps = Math.max(1, Math.ceil(flowLps / 20));
    return { flowLps, head, powerKw, energyKwh, costPerDay, suggestedPumps };
  }, [dailyVolume, destinationElevation, sourceElevation, pipeLength, pumpEfficiency]);

  useEffect(() => {
    const targets = document.querySelectorAll<HTMLElement>("[data-reveal]");
    if (!targets.length) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("reveal-visible");
          }
        });
      },
      { threshold: 0.2 },
    );
    targets.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);



  // Nav visibility: fade out at 1-4% video progress, fade back in once scrolled past container
  const navOpacity = videoProgress < 0.01
    ? 1
    : videoProgress < 0.04
      ? 1 - ((videoProgress - 0.01) / 0.03)
      : scrollPastVideo > 0
        ? scrollPastVideo
        : 0;

  return (
    <div className="relative overflow-x-hidden bg-white text-slate-950">
      <Header navOpacity={navOpacity} />

      {/* Hero Section */}
      <section className="relative min-h-screen overflow-hidden pt-20 bg-white">
        <InteractiveTopUI />
        <div className="absolute inset-0 bg-gradient-to-b from-white/20 via-transparent to-transparent" style={{ zIndex: 1 }} />

        {/* SVG reveal animations */}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes content-reveal {
            0% { clip-path: inset(0 100% 0 0); opacity: 0; }
            100% { clip-path: inset(0 0 0 0); opacity: 1; }
          }
          .animate-reveal-left {
            animation: content-reveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
          .animate-reveal-right {
            animation: content-reveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s forwards;
            opacity: 0;
          }
        `}} />

        {/* White Cards - zIndex: 0 keeps them under the wave effect */}
        <div className="pointer-events-none absolute inset-x-0 top-32 flex justify-between px-4 2xl:px-12" style={{ zIndex: 0 }}>
          
          {/* Left Card: No Rain */}
          <div className="hidden xl:flex relative animate-reveal-left rounded-none bg-white shadow-[0_20px_50px_rgba(15,23,42,0.1)] border border-slate-100 items-center justify-center p-10 w-[35vw] max-w-[850px] h-[700px]" style={{ transform: 'translateX(-30px)' }}>
            <img src="/norain.svg" className="w-full h-full object-contain" alt="No Rain" />
            
              {/* Animated Dot for the 'A' in 'rain' - styled as a graphite brush stroke */}
              <div className="absolute flex items-center justify-center h-4 w-4" style={{ top: 'calc(50% + 2.5px)', left: 'calc(69% + 2.5px)' }}>
                <span className="animate-ping absolute inline-flex h-full w-full bg-zinc-500 opacity-40" style={{ borderRadius: '60% 40% 50% 70% / 50% 60% 40% 50%' }}></span>
                <span className="relative inline-flex h-[14px] w-[12px] bg-zinc-800/90" style={{ borderRadius: '40% 60% 70% 40% / 50% 40% 60% 50%', transform: 'rotate(12deg)', filter: 'drop-shadow(0px 1px 0px rgba(0,0,0,0.5))' }}></span>
            </div>
          </div>

          {/* Right Card: Pls */}
            <div className="hidden xl:flex animate-reveal-right rounded-none bg-white shadow-[0_20px_50px_rgba(15,23,42,0.1)] border border-slate-100 items-center justify-center p-10 w-[38vw] max-w-[950px] h-[600px] mt-24" style={{ transform: 'translateX(175px)' }}>
              <img src="/pls.svg" className="w-full h-full object-contain" alt="Pls" />
            </div>
        </div>

        <main className="relative z-10 mx-auto flex flex-col gap-6 px-6 sm:px-10 lg:px-16 pt-8">
          {/* Hero Section */}
          <section className="relative mx-auto flex w-full max-w-5xl flex-col items-center gap-10 pt-20 pb-4 text-center">
            <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden rounded-[2.5rem] opacity-90">
              <HeroLines />
            </div>
            <div className="space-y-6 reveal" data-reveal>
              <p className="inline-flex rounded-full bg-cyan-500/10 px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-700">
                Rainwater + system intelligence
              </p>
              <h1 className="text-5xl font-semibold tracking-tight text-slate-950 sm:text-6xl">
                Modern water systems, smarter management.
              </h1>
              <p className="mx-auto max-w-2xl text-base leading-8 text-slate-700 sm:text-lg">
                Collector combines rainwater capture modeling, pump optimization, and live operations data into one integrated platform for water infrastructure.
              </p>
            </div>

            <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center reveal" data-reveal>
              <a
                href="#optimizer"
                className="inline-flex items-center justify-center rounded-full bg-slate-950 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-800"
              >
                Try optimizer
              </a>
              <a
                href="#features"
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-8 py-4 text-sm font-semibold text-slate-950 transition hover:border-slate-400"
              >
                Learn more
              </a>
            </div>
          </section>
        </main>
      </section>

      {/* Full Screen Scroll Video Section */}
      <div className="relative w-full" ref={videoScrollContainerRef} style={{ height: '200vh', marginTop: '-27.5rem', marginBottom: '-100vh' }}>
        <div className="sticky top-0 h-screen w-full overflow-hidden">
          <div 
            className="absolute inset-0 flex items-center justify-center"
            style={{
              opacity: videoProgress > 0.85 ? 1 - ((videoProgress - 0.85) / 0.15) : 1,
            }}
          >
            <div 
              className="relative overflow-hidden bg-black will-change-transform"
              style={{
                width: `calc(82vw + ${Math.min(1, videoProgress * 7)} * 18vw)`,
                height: `calc(82vh + ${Math.min(1, videoProgress * 7)} * 18vh)`,
                borderRadius: `${2.5 * (1 - Math.min(1, videoProgress * 7))}rem`,
              }}
            >
              <video autoPlay loop muted playsInline className="h-full w-full object-cover">
                <source src="/Valve Oil Gauge Video.mp4" type="video/mp4" />
              </video>
              <div className="absolute left-6 bottom-6 rounded-full bg-white/10 backdrop-blur-md px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-white shadow-xl z-10">
                Live valve telemetry
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MVP Optimizer Section */}
      <section id="optimizer" className="relative py-20 px-6 sm:px-10 lg:px-16 bg-slate-50">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 space-y-4 text-center reveal" data-reveal>
            <p className="inline-flex rounded-full bg-cyan-500/10 px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-700 mx-auto">
              Pumping Optimizer
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Design your system with confidence.
            </h2>
            <p className="mx-auto max-w-2xl text-slate-700">
              Configure your water system parameters and instantly see energy consumption, head calculations, and cost estimates.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr] reveal" data-reveal>
            {/* Input Panel */}
            <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)] sm:p-10">
              <div className="mb-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Backend building data</p>
                    <p className="mt-2 text-base font-semibold text-slate-950">
                      {loading ? "Loading building data…" : backendError ? "Failed to load values" : backendBuilding?.name ?? "No building selected"}
                    </p>
                  </div>
                  <div className="rounded-3xl bg-white px-4 py-2 text-xs uppercase tracking-[0.18em] text-slate-500 border border-slate-200">
                    {backendBuilding ? backendBuilding.state : loading ? "Loading" : "Offline"}
                  </div>
                </div>
                {backendBuilding && (
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div className="rounded-3xl bg-white p-3 border border-slate-100">
                      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Roof area</p>
                      <p className="mt-2 text-sm font-semibold text-slate-950">{backendBuilding.roof_area_sqft.toLocaleString()} sqft</p>
                    </div>
                    <div className="rounded-3xl bg-white p-3 border border-slate-100">
                      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Annual capture</p>
                      <p className="mt-2 text-sm font-semibold text-slate-950">{Math.round(backendBuilding.rainwater_potential_gallons).toLocaleString()} gal</p>
                    </div>
                    <div className="rounded-3xl bg-white p-3 border border-slate-100">
                      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Water cost</p>
                      <p className="mt-2 text-sm font-semibold text-slate-950">${backendBuilding.water_price_per_1000_gal_usd.toFixed(2)}/1000 gal</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 border border-slate-200">
                  <span className="font-semibold text-slate-950">Daily volume</span>
                  <input
                    type="number"
                    value={dailyVolume}
                    onChange={(event) => setDailyVolume(Number(event.target.value))}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                    min={10}
                  />
                  <p className="text-xs text-slate-500">m³ per day</p>
                </label>

                <label className="space-y-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 border border-slate-200">
                  <span className="font-semibold text-slate-950">Pump efficiency</span>
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

                <label className="space-y-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 border border-slate-200">
                  <span className="font-semibold text-slate-950">Source elevation</span>
                  <input
                    type="number"
                    value={sourceElevation}
                    onChange={(event) => setSourceElevation(Number(event.target.value))}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  />
                  <p className="text-xs text-slate-500">meters</p>
                </label>

                <label className="space-y-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 border border-slate-200">
                  <span className="font-semibold text-slate-950">Destination elevation</span>
                  <input
                    type="number"
                    value={destinationElevation}
                    onChange={(event) => setDestinationElevation(Number(event.target.value))}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                  />
                  <p className="text-xs text-slate-500">meters</p>
                </label>

                <label className="space-y-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 border border-slate-200 sm:col-span-2">
                  <span className="font-semibold text-slate-950">Pipeline length</span>
                  <input
                    type="number"
                    value={pipeLength}
                    onChange={(event) => setPipeLength(Number(event.target.value))}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
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
                  className="rounded-2xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-cyan-600"
                >
                  Use Suggested Pump Count
                </button>
                <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                  <div className="flex items-center justify-between text-slate-950 font-semibold">
                    <span>Selected pumps</span>
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

            {/* Results Panel */}
            <div className="space-y-6 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)] sm:p-10">
              <div className="space-y-4">
                <div className="rounded-2xl bg-slate-50 p-5 border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-950">Optimization summary</h3>
                  <p className="mt-2 text-sm text-slate-600">Estimated metrics for your configuration.</p>
                </div>
                <div className="grid gap-4 text-sm">
                  <div className="rounded-2xl bg-gradient-to-br from-cyan-50 to-cyan-50 border border-cyan-200 p-5">
                    <p className="text-xs uppercase tracking-[0.18em] text-cyan-700">Flow</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{formatNumber(estimate.flowLps, 2)} <span className="text-lg text-slate-600">L/s</span></p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-600">Total head</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{formatNumber(estimate.head, 1)} <span className="text-lg text-slate-600">m</span></p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-600">Installed power</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{formatNumber(estimate.powerKw, 2)} <span className="text-lg text-slate-600">kW</span></p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-600">Daily energy</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{formatNumber(estimate.energyKwh, 1)} <span className="text-lg text-slate-600">kWh</span></p>
                  </div>
                  <div className="rounded-2xl bg-gradient-to-br from-green-50 to-green-50 border border-green-200 p-5">
                    <p className="text-xs uppercase tracking-[0.18em] text-green-700">Daily cost</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">${formatNumber(estimate.costPerDay, 2)}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-700">
                <h4 className="font-semibold text-slate-950">Notes</h4>
                <ul className="mt-4 space-y-3 list-disc pl-5 text-slate-600 text-xs">
                  <li>Elevation gain calculated from destination minus source.</li>
                  <li>Friction allowance added for pipeline length.</li>
                  <li>Energy cost uses baseline of $0.18 per kWh.</li>
                  <li>Optimize pump count to balance flow and redundancy.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-20 px-6 sm:px-10 lg:px-16 bg-white">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 space-y-4 text-center reveal" data-reveal>
            <h2 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Why Collector
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3 reveal" data-reveal>
            <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Streamline</p>
              <h3 className="mt-4 text-xl font-semibold text-slate-950">Rainwater capture planning</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Design collection systems with confidence using rainfall analytics and roof area forecasts.
              </p>
            </div>

            <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Optimize</p>
              <h3 className="mt-4 text-xl font-semibold text-slate-950">Pump & energy forecasting</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Balance head, flow, and efficiency in an intuitive model that speaks to teams and operators alike.
              </p>
            </div>

            <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Launch</p>
              <h3 className="mt-4 text-xl font-semibold text-slate-950">Operations-grade insights</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Share the right visuals with stakeholders, from plant managers to executive decision-makers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="relative py-20 px-6 sm:px-10 lg:px-16 bg-slate-50">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 rounded-[2rem] border border-slate-200 bg-white p-10 shadow-[0_30px_80px_rgba(15,23,42,0.08)] sm:grid-cols-[1fr_0.85fr] reveal" data-reveal>
            <div className="space-y-6">
              <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Collector platform</p>
              <h2 className="text-3xl font-semibold text-slate-950">Built for teams moving water infrastructure from concept to control.</h2>
              <p className="max-w-xl text-base leading-8 text-slate-700">
                Collector brings rainwater intelligence, pump system modeling, and valve performance monitoring together in a modern dashboard designed for fast, confident decisions.
              </p>
              <div className="grid gap-4 sm:grid-cols-2 pt-4">
                <div className="rounded-3xl bg-gradient-to-br from-cyan-50 to-cyan-50/50 p-5 border border-cyan-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-cyan-700 font-semibold">Deploy faster</p>
                  <p className="mt-3 text-sm text-slate-700">From feasibility to field-ready planning in fewer steps.</p>
                </div>
                <div className="rounded-3xl bg-slate-50 p-5 border border-slate-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-600 font-semibold">Stay aligned</p>
                  <p className="mt-3 text-sm text-slate-700">Keep stakeholders on the same page with clear data stories.</p>
                </div>
              </div>
            </div>

            <div className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-8">
              <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Ready for teams</p>
              <div className="mt-6 space-y-4">
                <div className="rounded-3xl bg-white p-5 shadow-sm shadow-slate-200/50 border border-slate-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500 font-semibold">Trusted by</p>
                  <p className="mt-3 text-lg font-semibold text-slate-950">Water utilities and industrial operators</p>
                </div>
                <div className="rounded-3xl bg-white p-5 shadow-sm shadow-slate-200/50 border border-slate-200">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500 font-semibold">Highlights</p>
                  <ul className="mt-3 space-y-3 text-sm leading-7 text-slate-600">
                    <li>Real-time operational visuals.</li>
                    <li>Rainwater capture modeling.</li>
                    <li>Energy cost forecasting.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="relative py-16 px-6 sm:px-10 lg:px-16 bg-white text-center">
        <div className="mx-auto max-w-3xl reveal" data-reveal>
          <h2 className="text-3xl font-semibold text-slate-950">Ready to optimize your water systems?</h2>
          <p className="mt-4 text-slate-700">Start with our interactive optimizer above, or request a full platform demo.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <a
              href="#optimizer"
              className="inline-flex items-center justify-center rounded-full bg-slate-950 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-800"
            >
              Get started
            </a>
            <a
              href="mailto:hello@collectorwater.com"
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-8 py-4 text-sm font-semibold text-slate-950 transition hover:border-slate-400"
            >
              Request demo
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
