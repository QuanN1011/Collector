"use client";

import { useAuth0 } from "@auth0/auth0-react";

export function AuthBar() {
  const { isAuthenticated, isLoading, loginWithRedirect, logout, user, error } = useAuth0();

  if (isLoading) {
    return (
      <span className="pointer-events-auto rounded-lg border border-white/15 bg-slate-950/60 px-3 py-1.5 text-xs text-slate-400">
        Auth…
      </span>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="pointer-events-auto flex flex-col items-end gap-1">
        {error ? (
          <p className="max-w-[14rem] text-right text-[11px] text-red-300/90" role="alert">
            {error.message}
          </p>
        ) : null}
        <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: "signup" } })}
          className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3 py-1.5 text-xs font-medium text-cyan-200 transition hover:bg-cyan-500/20"
        >
          Sign up
        </button>
        <button
          type="button"
          onClick={() => loginWithRedirect()}
          className="rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-100 transition hover:bg-white/10"
        >
          Log in
        </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pointer-events-auto flex max-w-[min(100%,20rem)] items-center gap-2">
      <span className="truncate text-xs text-slate-300" title={user?.email ?? undefined}>
        {user?.email ?? user?.name ?? "Signed in"}
      </span>
      <button
        type="button"
        onClick={() =>
          logout({
            logoutParams: { returnTo: window.location.origin },
          })
        }
        className="shrink-0 rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-100 transition hover:bg-white/10"
      >
        Log out
      </button>
    </div>
  );
}
