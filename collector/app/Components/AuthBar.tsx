"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { isAuth0Configured } from "@/lib/auth0Env";

function AuthBarInner() {
  const { isLoading, error } = useAuth0();

  if (isLoading) {
    return (
      <span className="pointer-events-auto rounded-lg border border-white/15 bg-slate-950/60 px-3 py-1.5 text-xs text-slate-400">
        Auth…
      </span>
    );
  }

  if (error) {
    return (
      <p className="pointer-events-auto max-w-[14rem] rounded-lg border border-red-500/30 bg-red-950/40 px-3 py-1.5 text-right text-[11px] text-red-200" role="alert">
        {error.message}
      </p>
    );
  }

  return null;
}

/**
 * Loading / error only; Log in · Sign up · Log out are in `Header` to avoid duplicate CTAs.
 */
export function AuthBar() {
  if (!isAuth0Configured()) {
    return null;
  }

  return <AuthBarInner />;
}
