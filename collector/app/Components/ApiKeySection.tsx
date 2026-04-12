"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { useCallback, useState } from "react";

import { API_KEY_STORAGE_KEY } from "@/lib/api";
import { isAuth0Configured } from "@/lib/auth0Env";
import { getIdTokenForApiKeyIssue, issueApiKeyWithIdToken } from "@/lib/issueApiKey";

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

/**
 * CTA block matching the “Ready to optimize…” section: centered title, primary pill button, outcome below.
 * Uses the same issue flow as `SettingsMenu` (`getIdTokenForApiKeyIssue` + `issueApiKeyWithIdToken`) so behavior
 * is identical wherever this block is mounted (must stay under `Auth0Provider` when Auth0 is configured).
 */
export function ApiKeySection() {
  if (!isAuth0Configured()) {
    return (
      <section className="relative border-t border-slate-100 bg-white py-16 px-6 text-center sm:px-10 lg:px-16">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-3xl font-semibold text-slate-950">API key</h2>
          <p className="mt-8 text-sm text-slate-600">Configure Auth0 (NEXT_PUBLIC_AUTH0_*) to enable API keys.</p>
        </div>
      </section>
    );
  }

  return <ApiKeySectionInner />;
}

function ApiKeySectionInner() {
  const { isAuthenticated, isLoading, user, getAccessTokenSilently } = useAuth0();
  const emailVerified = user?.email_verified === true;

  const [busy, setBusy] = useState(false);
  const [shownKey, setShownKey] = useState<string | null>(null);
  const [unverifiedMessage, setUnverifiedMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyHint, setCopyHint] = useState<string | null>(null);

  const copyKey = useCallback(async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopyHint("Copied");
      setTimeout(() => setCopyHint(null), 2000);
    } catch {
      setCopyHint("Copy failed");
      setTimeout(() => setCopyHint(null), 2000);
    }
  }, []);

  const handleGetApiKey = useCallback(async () => {
    setError(null);
    setCopyHint(null);
    setUnverifiedMessage(false);

    if (!isAuthenticated || !emailVerified) {
      setUnverifiedMessage(true);
      setShownKey(null);
      return;
    }

    const existing = typeof window !== "undefined" ? localStorage.getItem(API_KEY_STORAGE_KEY) : null;
    if (existing && existing.trim()) {
      setShownKey(existing.trim());
      return;
    }

    setBusy(true);
    try {
      const token = await getIdTokenForApiKeyIssue(getAccessTokenSilently);
      if (!token.ok) {
        setError(token.error);
        return;
      }
      const out = await issueApiKeyWithIdToken(token.idToken);
      if (!out.ok) {
        setError(out.error);
        return;
      }
      localStorage.setItem(API_KEY_STORAGE_KEY, out.api_key);
      setShownKey(out.api_key);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not get API key.");
    } finally {
      setBusy(false);
    }
  }, [isAuthenticated, emailVerified, getAccessTokenSilently]);

  return (
    <section className="relative border-t border-slate-100 bg-white py-16 px-6 text-center sm:px-10 lg:px-16">
      <div className="mx-auto max-w-3xl reveal" data-reveal>
        <h2 className="text-3xl font-semibold text-slate-950">API key</h2>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button
            type="button"
            disabled={busy || isLoading}
            onClick={() => void handleGetApiKey()}
            className="inline-flex items-center justify-center rounded-full bg-slate-950 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-800 disabled:opacity-60"
          >
            {busy || isLoading ? "…" : "Get api key"}
          </button>
        </div>

        {unverifiedMessage ? (
          <p className="mt-8 text-sm text-slate-600">API key for verified users only</p>
        ) : null}

        {error ? (
          <p className="mt-8 text-sm text-red-600" role="alert">
            {error}
          </p>
        ) : null}

        {shownKey ? (
          <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-left shadow-sm">
            <div className="flex items-start gap-3">
              <code className="min-w-0 flex-1 break-all font-mono text-[13px] leading-relaxed text-slate-800">{shownKey}</code>
              <button
                type="button"
                onClick={() => void copyKey(shownKey)}
                className="shrink-0 rounded-lg border border-slate-300 bg-white p-2 text-slate-600 transition hover:border-slate-400 hover:bg-slate-100 hover:text-slate-900"
                title="Copy API key"
                aria-label="Copy API key to clipboard"
              >
                <CopyClipboardIcon className="h-5 w-5" />
              </button>
            </div>
            {copyHint ? <p className="mt-2 text-xs text-slate-500">{copyHint}</p> : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
