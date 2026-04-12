"use client";

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
            <a href="#prospecting" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Prospecting
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
            <a href="#prospecting" className={`text-sm font-medium transition hover:opacity-80 ${tc}`}>
              Prospecting
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
