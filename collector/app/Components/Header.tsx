"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { Montagu_Slab } from "next/font/google";
import { useEffect, useRef, useState } from "react";

import { isAuth0Configured } from "@/lib/auth0Env";

const montaguSlab = Montagu_Slab({
  subsets: ["latin"],
  weight: ["500", "600"],
});

type HeaderProps = {
  navOpacity?: number;
};

type BackgroundType = "light" | "dark" | "gradient";

function useHeaderBackground() {
  const [backgroundType, setBackgroundType] = useState<BackgroundType>("light");

  useEffect(() => {
    const handleScroll = () => {
      const sections = document.querySelectorAll("section");
      let currentBg: BackgroundType = "light";

      sections.forEach((section) => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
          const bg = window.getComputedStyle(section).backgroundColor;
          if (bg.includes("rgb(15, 23, 42)") || bg.includes("#0f172a")) {
            currentBg = "dark";
          } else {
            currentBg = "light";
          }
        }
      });

      setBackgroundType(currentBg);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return backgroundType;
}

function getGlassmorphismClasses(backgroundType: BackgroundType) {
  const baseClasses =
    "fixed top-0 left-0 right-0 z-50 border-b backdrop-blur-xl transition-all duration-300 ease-in-out";

  if (backgroundType === "dark") {
    return `${baseClasses} border-slate-700/30 bg-slate-900/60`;
  }
  if (backgroundType === "gradient") {
    return `${baseClasses} border-white/10 bg-white/5`;
  }
  return `${baseClasses} border-slate-200/50 bg-white/80`;
}

function getTextClasses(backgroundType: BackgroundType) {
  return backgroundType === "dark" ? "text-white" : "text-[#3e3d3c]";
}

function getDropdownPanelClasses(backgroundType: BackgroundType) {
  if (backgroundType === "dark") {
    return "bg-slate-900";
  }
  return "bg-white";
}

function HeaderAuthActions({ backgroundType }: { backgroundType: BackgroundType }) {
  const { isAuthenticated, isLoading, loginWithRedirect, logout, user } = useAuth0();
  const textClasses = getTextClasses(backgroundType);

  if (isLoading) {
    return <span className={`pointer-events-auto text-sm ${textClasses}`}>...</span>;
  }

  if (isAuthenticated) {
    return (
      <div className="pointer-events-auto inline-flex min-w-0 max-w-full items-center justify-end gap-3">
        <span className={`hidden truncate text-sm sm:inline ${textClasses}`} title={user?.email ?? undefined}>
          {user?.email ?? user?.name ?? "Signed in"}
        </span>
        <button
          type="button"
          onClick={() =>
            logout({
              logoutParams: {
                returnTo: typeof window !== "undefined" ? window.location.origin : undefined,
              },
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
      </div>
    );
  }

  return (
    <div className="pointer-events-auto inline-flex items-center justify-end gap-3">
      <button
        type="button"
        onClick={() => loginWithRedirect()}
        className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${textClasses}`}
      >
        Log in
      </button>
      <button
        type="button"
        onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: "signup" } })}
        className="rounded-full bg-[#3e3d3c] px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110 hover:bg-[#2c2b2a]"
      >
        Sign up
      </button>
    </div>
  );
}

function HeaderContent({ navOpacity = 1, withAuth0 }: HeaderProps & { withAuth0: boolean }) {
  const backgroundType = useHeaderBackground();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const textClasses = getTextClasses(backgroundType);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 24);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
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
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  return (
    <header
      className={`${getGlassmorphismClasses(backgroundType)} pointer-events-none`}
      style={{
        opacity: navOpacity,
        transition: "opacity 0.3s ease",
      }}
    >
      <div className="mx-auto max-w-7xl px-6 py-4 sm:px-10 lg:px-16">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          <style
            dangerouslySetInnerHTML={{
              __html: `
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
                  content: "";
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
              `,
            }}
          />

          <div className="flex items-center justify-start">
            <div ref={menuRef} className="relative hidden lg:block pointer-events-auto">
              <button
                type="button"
                onClick={() => setIsMenuOpen((prev) => !prev)}
                aria-expanded={isMenuOpen}
                aria-controls="header-dropdown-nav"
                aria-label="Open section menu"
                className={`inline-flex h-14 w-14 items-center justify-center overflow-visible transition ${textClasses}`}
              >
                <span className="relative block h-8 w-8" aria-hidden="true">
                  <span
                    className={`absolute left-1/2 top-[9px] h-[2.5px] w-6 -translate-x-1/2 origin-center bg-current transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? "top-[52%] -translate-y-1/2 rotate-45" : ""}`}
                  />
                  <span
                    className={`absolute left-1/2 top-[18px] h-[2.5px] w-6 -translate-x-1/2 origin-center bg-current transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${isMenuOpen ? "top-[52%] -translate-y-1/2 -rotate-45" : ""}`}
                  />
                </span>
              </button>

              <div
                id="header-dropdown-nav"
                className={`absolute left-0 top-full mt-2 w-[184px] rounded-none px-5 pt-5 pb-7 shadow-[0_12px_30px_rgba(15,23,42,0.14)] backdrop-blur-xl transition-all duration-300 ${getDropdownPanelClasses(backgroundType)} ${isMenuOpen ? "pointer-events-auto translate-y-0 opacity-100" : "pointer-events-none -translate-y-2 opacity-0"}`}
              >
                <div className="mb-4 flex items-center gap-2">
                  <img src="/bucket.svg" alt="Collector" className="h-5 w-5" />
                  <span
                    className={`text-xs font-bold uppercase tracking-[0.2em] transition-opacity duration-300 ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
                  >
                    Collector
                  </span>
                </div>
                <nav className="grid gap-5">
                  <a
                    href="#water-economics"
                    onClick={() => setIsMenuOpen(false)}
                    className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
                  >
                    Water Economics
                  </a>
                  <a
                    href="#rainuse-nexus"
                    onClick={() => setIsMenuOpen(false)}
                    className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
                  >
                    Site Prospecting Engine
                  </a>
                  <a
                    href="#features"
                    onClick={() => setIsMenuOpen(false)}
                    className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
                  >
                    Features
                  </a>
                  <a
                    href="#about"
                    onClick={() => setIsMenuOpen(false)}
                    className={`menu-underline items-center text-lg transition-opacity duration-300 ${montaguSlab.className} ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
                  >
                    About
                  </a>
                </nav>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 justify-self-center">
            <div className="pointer-events-auto inline-flex items-center gap-3">
              <img
                src="/bucket.svg"
                alt="Collector"
                className="logo-hover h-8 w-8 transition-transform duration-700 ease-in-out"
                style={{ transform: "rotate(-8deg)" }}
              />
              <span
                className={`text-xl font-bold uppercase tracking-wide transition-opacity duration-300 ${textClasses} ${isScrolled ? "opacity-60" : "opacity-100"}`}
              >
                Collector
              </span>
            </div>
          </div>

          <div className="flex min-w-0 items-center justify-end gap-3">
            {withAuth0 ? (
              <HeaderAuthActions backgroundType={backgroundType} />
            ) : (
              <div className="pointer-events-auto inline-flex items-center gap-3">
                <button className={`text-sm font-medium transition-all duration-300 hover:scale-110 ${textClasses}`}>
                  Log in
                </button>
                <button className="rounded-full bg-[#3e3d3c] px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-110 hover:bg-[#2c2b2a]">
                  Sign up
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Header({ navOpacity = 1 }: HeaderProps) {
  if (!isAuth0Configured()) {
    return <HeaderContent navOpacity={navOpacity} withAuth0={false} />;
  }

  return <HeaderContent navOpacity={navOpacity} withAuth0 />;
}
