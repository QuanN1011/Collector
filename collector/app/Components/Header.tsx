"use client";

import { Montagu_Slab } from "next/font/google";
import { useEffect, useRef, useState } from "react";

const montaguSlab = Montagu_Slab({
  subsets: ["latin"],
  weight: ["500", "600"],
});

export default function Header({ navOpacity = 1 }: { navOpacity?: number }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [backgroundType, setBackgroundType] = useState<'light' | 'dark' | 'gradient'>('light');
  const menuRef = useRef<HTMLDivElement | null>(null);
import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useState } from "react";

import { isAuth0Configured } from "@/lib/auth0Env";

function useHeaderBackground() {
  const [backgroundType, setBackgroundType] = useState<"light" | "dark" | "gradient">("light");

  useEffect(() => {
    const handleScroll = () => {
      const sections = document.querySelectorAll("section");
      let currentBg: "light" | "dark" | "gradient" = "light";

      sections.forEach((section) => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
          const bg = window.getComputedStyle(section).backgroundColor;
          if (bg.includes("rgb(15, 23, 42)") || bg.includes("#0f172a")) {
            currentBg = "dark";
          } else if (bg.includes("gradient")) {
            currentBg = "gradient";
          } else {
            currentBg = "light";
          }
        }
      });

      setBackgroundType(currentBg);
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const getGlassmorphismClasses = () => {
    const baseClasses = "fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out";
  return backgroundType;
}

function getGlassmorphismClasses(backgroundType: "light" | "dark" | "gradient") {
  const baseClasses = "fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out";

  if (backgroundType === "dark") {
    return `${baseClasses} bg-slate-900/60 backdrop-blur-xl border-b border-slate-700/30`;
  }
  if (backgroundType === "gradient") {
    return `${baseClasses} bg-white/5 backdrop-blur-xl border-b border-white/10`;
  }
  return `${baseClasses} bg-white/80 backdrop-blur-xl border-b border-slate-200/50`;
}

function getTextClasses(backgroundType: "light" | "dark" | "gradient") {
  return backgroundType === "dark" ? "text-white" : "text-slate-950";
}

  const getTextClasses = () => {
    return backgroundType === 'dark' ? 'text-white' : 'text-[#3e3d3c]';
  };

  const getDropdownPanelClasses = () => {
    if (backgroundType === 'dark') {
      return 'bg-slate-900';
    }
    if (backgroundType === 'gradient') {
      return 'bg-white';
    }
    return 'bg-white';
  };

  return (
    <header className={getGlassmorphismClasses()} style={{ opacity: navOpacity, pointerEvents: navOpacity < 0.1 ? 'none' : 'auto', transition: 'opacity 0.3s ease' }}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          {/* Logo */}
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes gentle-shake {
              0% { transform: rotate(-8deg); }
              15% { transform: rotate(-13deg) scale(1.15); }
              30% { transform: rotate(-4deg) scale(1.18); }
              45% { transform: rotate(-12deg) scale(1.15); }
              60% { transform: rotate(-5deg) scale(1.12); }
              75% { transform: rotate(-10deg) scale(1.06); }
              100% { transform: rotate(-8deg) scale(1); }
            }
            .logo-hover:hover {
              animation: gentle-shake 1s ease-in-out;
            }
            .menu-underline {
              position: relative;
              display: inline-flex;
              width: fit-content;
            }
            .menu-underline::after {
              content: '';
              position: absolute;
              left: 0;
              bottom: -5px;
              width: 100%;
              height: 2px;
              background: currentColor;
              transform: scaleX(0);
              transform-origin: left;
              transition: transform 300ms ease;
            }
            .menu-underline:hover::after,
            .menu-underline:focus-visible::after {
              transform: scaleX(1);
            }
          `}} />

          {/* Left dropdown navigation */}
          <div className="flex items-center justify-start">
            <div ref={menuRef} className="relative hidden lg:block">
              <button
                type="button"
                onClick={() => setIsMenuOpen((prev) => !prev)}
                aria-expanded={isMenuOpen}
                aria-controls="header-dropdown-nav"
                aria-label="Open section menu"
                className={`inline-flex h-14 w-14 items-center justify-center overflow-visible transition ${getTextClasses()}`}
              >
                <span className="relative block h-8 w-8" aria-hidden="true">
                  <span
                    className={`absolute left-1/2 top-[9px] h-[2.5px] w-6 -translate-x-1/2 bg-current origin-center transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? 'top-[52%] -translate-y-1/2 rotate-45' : ''}`}
                  />
                  <span
                    className={`absolute left-1/2 top-[18px] h-[2.5px] w-6 -translate-x-1/2 bg-current origin-center transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? 'top-[52%] -translate-y-1/2 -rotate-45' : ''}`}
                  />
                </span>
              </button>

              <div
                id="header-dropdown-nav"
                className={`absolute left-0 top-full mt-2 w-[184px] rounded-none px-5 pt-5 pb-7 shadow-[0_12px_30px_rgba(15,23,42,0.14)] backdrop-blur-xl transition-all duration-300 ${getDropdownPanelClasses()} ${isMenuOpen ? 'pointer-events-auto translate-y-0 opacity-100' : 'pointer-events-none -translate-y-2 opacity-0'}`}
              >
                <div className="mb-4 flex items-center gap-2">
                  <img
                    src="/bucket.svg"
                    alt="Collector"
                    className="h-5 w-5"
                  />
                  <span className={`text-xs font-bold uppercase tracking-[0.2em] transition-opacity duration-300 ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Collector
                  </span>
                </div>
                <nav className="grid gap-5">
                  <a href="#optimizer" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Optimizer
                  </a>
                  <a href="#features" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    Features
                  </a>
                  <a href="#about" onClick={() => setIsMenuOpen(false)} className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
                    About
                  </a>
                </nav>
              </div>
            </div>
          </div>

          {/* Center logo */}
          <div className="flex items-center justify-center gap-3 justify-self-center">
            <img
              src="/bucket.svg"
              alt="Collector"
              className="h-8 w-8 logo-hover transition-transform duration-700 ease-in-out"
              style={{ transform: 'rotate(-8deg)' }}
            />
            <span className={`text-xl font-bold uppercase tracking-wide transition-opacity duration-300 ${getTextClasses()} ${isScrolled ? 'opacity-60' : 'opacity-100'}`}>
              Collector
            </span>
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center justify-end gap-3">
            <button className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${getTextClasses()}`}>
              Log in
            </button>
            <button className="rounded-full bg-[#3e3d3c] px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110 hover:bg-[#2c2b2a]">
              Sign up
            </button>
/** Nav shell when Auth0 env is not configured (no `useAuth0` — avoids hook outside provider). */
function HeaderWithoutAuth0() {
  const backgroundType = useHeaderBackground();
  const tc = getTextClasses(backgroundType);

  return (
    <header className={getGlassmorphismClasses(backgroundType)}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg">
              <span className="text-lg font-bold">C</span>
            </div>
            <span className={`text-xl font-bold uppercase tracking-wide ${tc}`}>Collector</span>
          </div>

          <nav className="hidden items-center gap-8 md:flex">
            <a href="#rainuse-nexus" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              RainUSE Nexus
            </a>
            <a href="#water-economics" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Water economics
            </a>
            <a href="#features" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Features
            </a>
            <a href="#about" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              About
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <span className={`text-sm ${tc}`}>Log in</span>
            <span className="rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white">Sign up</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function HeaderWithAuth0() {
  const backgroundType = useHeaderBackground();
  const { isAuthenticated, isLoading, loginWithRedirect, logout, user } = useAuth0();
  const tc = getTextClasses(backgroundType);

  return (
    <header className={getGlassmorphismClasses(backgroundType)}>
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg">
              <span className="text-lg font-bold">C</span>
            </div>
            <span className={`text-xl font-bold uppercase tracking-wide ${tc}`}>Collector</span>
          </div>

          <nav className="hidden items-center gap-8 md:flex">
            <a href="#rainuse-nexus" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              RainUSE Nexus
            </a>
            <a href="#water-economics" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Water economics
            </a>
            <a href="#features" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Features
            </a>
            <a href="#about" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              About
            </a>
          </nav>

          <div className="flex min-w-0 max-w-[min(100%,14rem)] items-center justify-end gap-3 sm:max-w-none">
            {isLoading ? (
              <span className={`text-sm ${tc}`}>…</span>
            ) : isAuthenticated ? (
              <>
                <span className={`hidden truncate text-sm sm:inline ${tc}`} title={user?.email ?? undefined}>
                  {user?.email ?? user?.name ?? "Signed in"}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    logout({
                      logoutParams: { returnTo: typeof window !== "undefined" ? window.location.origin : undefined },
                    })
                  }
                  className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition-all duration-300 hover:scale-105 ${
                    backgroundType === "dark"
                      ? "border-white/30 bg-white/10 text-white hover:bg-white/20"
                      : "border-slate-300 bg-white text-slate-950 hover:bg-slate-50"
                  }`}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => loginWithRedirect()}
                  className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${tc}`}
                >
                  Log in
                </button>
                <button
                  type="button"
                  onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: "signup" } })}
                  className="rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110"
                >
                  Sign up
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Header() {
  if (!isAuth0Configured()) {
    return <HeaderWithoutAuth0 />;
  }

  return <HeaderWithAuth0 />;
}
