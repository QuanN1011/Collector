/** True when Auth0 SPA env vars are set (client may use `useAuth0` only inside `Auth0Provider`). */
export function isAuth0Configured(): boolean {
  return (
    typeof process.env.NEXT_PUBLIC_AUTH0_DOMAIN === "string" &&
    process.env.NEXT_PUBLIC_AUTH0_DOMAIN.length > 0 &&
    typeof process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID === "string" &&
    process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID.length > 0
  );
}
