"use client";

import { useEffect } from "react";
import { AuthBar } from "./Components/AuthBar";
import { EmailVerificationBanner } from "@/app/Components/EmailVerificationBanner";
import { SettingsMenu } from "@/app/Components/SettingsMenu";
import InteractiveTopUI from "./Components/InteractiveTopUI";
import Header from "./Components/Header";
import Footer from "./Components/Footer";
import ProspectingSection from "./Components/ProspectingSection";
import WaterEconomicsSection from "./Components/WaterEconomicsSection";
import { ApiKeySection } from "./Components/ApiKeySection";
import { useProspecting } from "../lib/useProspecting";

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
  const prospecting = useProspecting();

  const optimizerKey = `${prospecting.selectedBuildingId}-${prospecting.buildingDetail ? "ok" : "pending"}`;
  const optimizerLoading =
    !!prospecting.selectedBuildingId && (prospecting.loadingDetail || prospecting.satelliteLoading);
  const optimizerError =
    prospecting.error &&
    !prospecting.economicsBuilding &&
    !prospecting.loadingDetail &&
    !prospecting.satelliteLoading
      ? prospecting.error
      : "";

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

  return (
    <div className="relative overflow-x-hidden bg-slate-50 text-slate-950">
      <Header />
      <div className="fixed right-4 top-20 z-[60] flex flex-col items-end gap-2 sm:right-6 sm:top-24">
        <AuthBar />
        <EmailVerificationBanner />
        <SettingsMenu />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-screen overflow-hidden pt-20">
        <InteractiveTopUI />
        <div className="absolute inset-0 z-[1] bg-gradient-to-b from-white/60 via-white/40 to-slate-50/40" />

        <main className="relative z-10 mx-auto flex flex-col gap-6 px-6 sm:px-10 lg:px-16 pt-8">
          {/* Hero Section */}
          <section className="relative mx-auto flex w-full max-w-5xl flex-col items-center gap-10 py-20 text-center">
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
                Collector combines rainwater capture, state-level water economics, and prospecting signals into one view for water infrastructure decisions.
              </p>
            </div>

            <div className="flex flex-col items-center gap-4 sm:flex-row sm:flex-wrap sm:justify-center reveal" data-reveal>
              <a
                href="#rainuse-nexus"
                className="inline-flex items-center justify-center rounded-full bg-cyan-600 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-cyan-900/15 transition hover:bg-cyan-700"
              >
                RainUSE Nexus
              </a>
              <a
                href="#water-economics"
                className="inline-flex items-center justify-center rounded-full bg-slate-950 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-800"
              >
                Water economics
              </a>
              <a
                href="#rainuse-nexus"
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-8 py-4 text-sm font-semibold text-slate-950 transition hover:border-slate-400"
              >
                Site prospecting
              </a>
            </div>

            <div className="relative w-full overflow-hidden rounded-[2.5rem] border border-slate-200 bg-white shadow-[0_35px_100px_rgba(15,23,42,0.12)] sm:h-[560px] reveal" data-reveal>
              <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-slate-50/80 to-transparent" />
              <video autoPlay loop muted playsInline className="h-[420px] w-full object-cover sm:h-full">
                <source src="/Valve Oil Gauge Video.mp4" type="video/mp4" />
              </video>
              <div className="absolute left-6 bottom-6 rounded-full bg-slate-950/95 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-white shadow-xl shadow-slate-950/20">
                Live valve telemetry
              </div>
            </div>
          </section>
        </main>
      </section>

      <ProspectingSection model={prospecting} />

      <section id="water-economics" className="relative scroll-mt-24 py-20 px-6 sm:px-10 lg:px-16 bg-slate-50">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 space-y-4 text-center reveal" data-reveal>
            <p className="inline-flex rounded-full bg-cyan-500/10 px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-cyan-700 mx-auto">
              Water economics
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              State rates &amp; rainwater value
            </h2>
            <p className="mx-auto max-w-2xl text-slate-700">
              Tie public state water tables to your model: reference $/1,000 gal and rainfall drive savings. Stress-test rates to
              see how the same capture volume changes in value.
            </p>
          </div>

          <div className="reveal" data-reveal>
            <WaterEconomicsSection
              key={optimizerKey}
              building={prospecting.economicsBuilding}
              loading={optimizerLoading}
              backendError={optimizerError}
            />
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
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Economics</p>
              <h3 className="mt-4 text-xl font-semibold text-slate-950">State rates &amp; savings</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Connect public water-price tables to modeled capture and stress-test utility rates against the same site.
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
          <p className="mt-4 text-slate-700">Start with prospecting and state water economics above, or request a full platform demo.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <a
              href="#rainuse-nexus"
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

      <ApiKeySection />

      <Footer />
    </div>
  );
}
