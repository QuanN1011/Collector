"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "rainuse_api_key";

const defaultApiBase = "http://127.0.0.1:8000";

function apiBaseUrl() {
  const u = process.env.NEXT_PUBLIC_API_URL;
  return typeof u === "string" && u.length > 0 ? u.replace(/\/$/, "") : defaultApiBase;
}

function formatIssueError(status: number, data: { detail?: unknown }): string {
  const d = data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d
      .map((item) => (typeof item === "object" && item && "msg" in item ? String((item as { msg: string }).msg) : JSON.stringify(item)))
      .join("; ");
  }
  return `Issue failed (${status})`;
}

function CopyClipboardIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  );
}

export function SettingsMenu() {
  const { isAuthenticated, isLoading, user, getAccessTokenSilently } = useAuth0();
  const emailVerified = user?.email_verified === true;
  const [menuOpen, setMenuOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  /** Only set after a successful Generate click — never from localStorage on load. */
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copyHint, setCopyHint] = useState<string | null>(null);
  const copyHintTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const detailsRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    return () => {
      if (copyHintTimer.current) clearTimeout(copyHintTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e: MouseEvent) => {
      const root = rootRef.current;
      const details = detailsRef.current;
      if (root && details?.open && !root.contains(e.target as Node)) {
        details.open = false;
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  const copyKey = useCallback(async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopyHint("Copied");
      if (copyHintTimer.current) clearTimeout(copyHintTimer.current);
      copyHintTimer.current = setTimeout(() => setCopyHint(null), 2000);
    } catch {
      setCopyHint("Copy failed");
      if (copyHintTimer.current) clearTimeout(copyHintTimer.current);
      copyHintTimer.current = setTimeout(() => setCopyHint(null), 2000);
    }
  }, []);

  const generateApiKey = useCallback(async () => {
    setMessage(null);
    setCopyHint(null);
    setBusy(true);
    try {
      const tokenOpts = {
        detailedResponse: true as const,
        authorizationParams: { scope: "openid profile email" },
      };
      let res = await getAccessTokenSilently(tokenOpts);
      let idToken = (res as { id_token?: string }).id_token;
      if (!idToken) {
        res = await getAccessTokenSilently({
          ...tokenOpts,
          cacheMode: "off" as const,
        });
        idToken = (res as { id_token?: string }).id_token;
      }
      if (!idToken) {
        setMessage("Could not read ID token. Try logging out and back in, or check Auth0 SPA settings.");
        return;
      }

      const r = await fetch(`${apiBaseUrl()}/api/keys/issue`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken}`,
          Accept: "application/json",
        },
      });
      const data = (await r.json().catch(() => ({}))) as { api_key?: string; detail?: unknown };
      if (!r.ok) {
        setMessage(formatIssueError(r.status, data));
        return;
      }
      if (data.api_key) {
        localStorage.setItem(STORAGE_KEY, data.api_key);
        setGeneratedKey(data.api_key);
        setMessage("API key generated. Use the copy control to copy it.");
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not generate API key.");
    } finally {
      setBusy(false);
    }
  }, [getAccessTokenSilently]);

  if (isLoading) {
    return (
      <span className="pointer-events-auto rounded-lg border border-white/10 bg-slate-950/50 px-2 py-1.5 text-xs text-slate-500">
        …
      </span>
    );
  }

  return (
    <div ref={rootRef} className="pointer-events-auto relative">
      <details
        ref={detailsRef}
        className="relative"
        onToggle={(e) => {
          const next = e.currentTarget.open;
          setMenuOpen(next);
          if (!next) {
            setMessage(null);
            setCopyHint(null);
          }
        }}
      >
        <summary className="cursor-pointer list-none rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-100 transition hover:bg-white/10 [&::-webkit-details-marker]:hidden">
          Settings
        </summary>
        <div className="absolute right-0 z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-white/15 bg-slate-950/95 p-3 text-left shadow-xl backdrop-blur-md">
          <p className="text-xs text-slate-400">API</p>
          {!isAuthenticated ? (
            <p className="mt-2 text-xs text-slate-500">Log in to generate an API key (required when the API uses Postgres).</p>
          ) : !emailVerified ? (
            <p className="mt-2 text-xs text-amber-200/90">Verify your email in Auth0 before generating an API key.</p>
          ) : (
            <>
              <button
                type="button"
                disabled={busy}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  void generateApiKey();
                }}
                className="mt-2 w-full rounded-lg border border-cyan-500/35 bg-cyan-500/10 px-3 py-2 text-xs font-medium text-cyan-100 transition hover:bg-cyan-500/20 disabled:opacity-50"
              >
                {busy ? "Generating…" : "Generate API key"}
              </button>
              {generatedKey ? (
                <div className="mt-3 rounded-lg border border-white/10 bg-slate-900/90 p-2">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Your API key</p>
                  <div className="mt-2 flex gap-2">
                    <code className="min-w-0 flex-1 break-all font-mono text-[11px] leading-relaxed text-cyan-100/95">{generatedKey}</code>
                    <button
                      type="button"
                      onMouseDown={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        void copyKey(generatedKey);
                      }}
                      className="shrink-0 rounded-md border border-white/15 p-1.5 text-slate-300 transition hover:border-cyan-500/40 hover:bg-white/5 hover:text-cyan-200"
                      title="Copy API key"
                      aria-label="Copy API key to clipboard"
                    >
                      <CopyClipboardIcon className="h-4 w-4" />
                    </button>
                  </div>
                  {copyHint ? <p className="mt-1.5 text-[11px] text-slate-400">{copyHint}</p> : null}
                </div>
              ) : null}
            </>
          )}
          {message ? <p className="mt-2 text-xs text-slate-300">{message}</p> : null}
          <p className="mt-3 border-t border-white/10 pt-2 text-[11px] text-slate-500">API: {apiBaseUrl()}</p>
        </div>
      </details>
    </div>
  );
}
