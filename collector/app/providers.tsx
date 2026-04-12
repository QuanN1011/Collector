"use client";

import { Auth0Provider } from "@auth0/auth0-react";
import { useMemo, useSyncExternalStore, type ReactNode } from "react";

/** Matches Auth0 dashboard Allowed Callback / Logout / Web Origins (default Next dev URL). */
function defaultAppOrigin(): string {
  const env = process.env.NEXT_PUBLIC_APP_BASE_URL;
  if (typeof env === "string" && env.length > 0) {
    return env.replace(/\/$/, "");
  }
  return "http://localhost:3000";
}

const noopSubscribe = () => () => {};

/**
 * Same idea as Auth0’s SPA quickstart (`authorizationParams.redirect_uri: window.location.origin`),
 * implemented without `useEffect` so SSR/hydration stay consistent (React `useSyncExternalStore`).
 */
function useAppOrigin(): string {
  return useSyncExternalStore(
    noopSubscribe,
    () => (typeof window !== "undefined" ? window.location.origin : defaultAppOrigin()),
    defaultAppOrigin,
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
  const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
  const origin = useAppOrigin();
  const redirectUri = origin.replace(/\/$/, "");

  const providerKey = useMemo(() => redirectUri, [redirectUri]);

  if (!domain || !clientId) {
    return <>{children}</>;
  }

  return (
    <Auth0Provider
      key={providerKey}
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: redirectUri,
        scope: "openid profile email",
      }}
      cacheLocation="memory"
      useRefreshTokens={false}
    >
      {children}
    </Auth0Provider>
  );
}
