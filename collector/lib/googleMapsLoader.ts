/**
 * Load Maps JavaScript API once (core + Places for address autocomplete).
 *
 * Uses **classic** `google.maps.*` APIs. Loads `libraries=places` and polls until
 * `Map` + `places.Autocomplete` exist. If an older script tag is present without
 * Places, we try `importLibrary("places")` when the runtime supports it.
 */
export const mapsJsKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY ?? "";

const SCRIPT_ID = "google-maps-js";
const READY_POLL_MS = 50;
const NEW_SCRIPT_WAIT_MS = 60_000;
const EXISTING_SCRIPT_WAIT_MS = 60_000;

function isMapsReady(): boolean {
  return Boolean(
    typeof window !== "undefined" &&
      window.google?.maps?.Map &&
      window.google?.maps?.places?.Autocomplete,
  );
}

function scriptIncludesPlaces(el: Element): boolean {
  if (!(el instanceof HTMLScriptElement) || !el.src) return false;
  try {
    const u = new URL(el.src);
    const libs = u.searchParams.get("libraries") ?? "";
    return libs.split(",").some((p) => p.trim().toLowerCase() === "places");
  } catch {
    return false;
  }
}

/** Best-effort: attach Places if core Maps already bootstrapped without `libraries=places`. */
async function ensurePlacesLibrary(): Promise<void> {
  if (window.google?.maps?.places?.Autocomplete) return;
  const maps = window.google?.maps;
  if (!maps || typeof maps.importLibrary !== "function") return;
  try {
    await maps.importLibrary("places");
  } catch {
    // Caller will time out or retry; avoid throwing here so we still poll.
  }
}

function waitUntilReady(deadlineMs: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + deadlineMs;
    const id = window.setInterval(() => {
      if (isMapsReady()) {
        window.clearInterval(id);
        resolve();
      } else if (Date.now() > deadline) {
        window.clearInterval(id);
        reject(
          new Error(
            "Google Maps did not become ready in time. Check NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY, " +
              "enable Maps JavaScript API + Places API for the key, and referrer restrictions.",
          ),
        );
      }
    }, READY_POLL_MS);
  });
}

let inflight: Promise<void> | null = null;

function doLoad(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (!mapsJsKey.trim()) {
    return Promise.reject(new Error("NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY is empty"));
  }
  if (isMapsReady()) return Promise.resolve();

  const existing = document.getElementById(SCRIPT_ID);

  if (existing) {
    return (async () => {
      if (!scriptIncludesPlaces(existing)) {
        await ensurePlacesLibrary();
      }
      await waitUntilReady(EXISTING_SCRIPT_WAIT_MS);
    })();
  }

  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.id = SCRIPT_ID;
    const key = encodeURIComponent(mapsJsKey);
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&loading=async&v=weekly&libraries=places`;
    s.async = true;
    s.onload = () => {
      void (async () => {
        try {
          await ensurePlacesLibrary();
          await waitUntilReady(NEW_SCRIPT_WAIT_MS);
          resolve();
        } catch (e) {
          reject(e);
        }
      })();
    };
    s.onerror = () => {
      s.remove();
      reject(new Error("Failed to load Google Maps JavaScript API"));
    };
    document.head.appendChild(s);
  });
}

export function loadMapsScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (isMapsReady()) return Promise.resolve();

  if (!inflight) {
    inflight = doLoad()
      .then(() => {
        inflight = null;
      })
      .catch((err) => {
        inflight = null;
        throw err;
      });
  }

  return inflight;
}
