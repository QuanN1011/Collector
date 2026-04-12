import { apiBaseUrl } from "./api";

function formatIssueError(status: number, data: { detail?: unknown }): string {
  const d = data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d
      .map((item) =>
        typeof item === "object" && item && "msg" in item ? String((item as { msg: string }).msg) : JSON.stringify(item),
      )
      .join("; ");
  }
  return `Issue failed (${status})`;
}

type GetAccessTokenSilently = (options?: object) => Promise<unknown>;

/**
 * Auth0 SPA: issue route expects the **ID token** (JWT with email), not the access token.
 * Same logic wherever “Get API key” / “Generate API key” is used.
 */
export async function getIdTokenForApiKeyIssue(
  getAccessTokenSilently: GetAccessTokenSilently,
): Promise<{ ok: true; idToken: string } | { ok: false; error: string }> {
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
    return {
      ok: false,
      error: "Could not read ID token. Try logging out and back in, or check Auth0 SPA settings.",
    };
  }
  return { ok: true, idToken };
}

export async function issueApiKeyWithIdToken(
  idToken: string,
): Promise<{ ok: true; api_key: string } | { ok: false; error: string }> {
  const r = await fetch(`${apiBaseUrl}/api/keys/issue`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${idToken}`,
      Accept: "application/json",
    },
  });
  const data = (await r.json().catch(() => ({}))) as { api_key?: string; detail?: unknown };
  if (!r.ok) {
    return { ok: false, error: formatIssueError(r.status, data) };
  }
  if (data.api_key) {
    return { ok: true, api_key: data.api_key };
  }
  return { ok: false, error: "No api_key in response" };
}
