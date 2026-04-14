/**
 * Load Maps JavaScript API once. Address search uses `importLibrary("places")` and the **Places API
 * (New)** programmatic autocomplete (`AutocompleteSuggestion.fetchAutocompleteSuggestions`, `Place.fetchFields`).
 * In Google Cloud enable **Maps JavaScript API** and **Places API (New)**. Key: HTTP referrer–restricted.
 * @see https://developers.google.com/maps/documentation/javascript/places-migration-autocomplete
 */
export const mapsJsKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY ?? "";

const BOOTSTRAP_POLL_MS = 50;
const BOOTSTRAP_TIMEOUT_MS = 25_000;

/** The script `onload` can run before the bootstrap attaches `importLibrary`; wait until it exists. */
function waitForImportLibrary(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();

  const deadline = Date.now() + BOOTSTRAP_TIMEOUT_MS;
  return new Promise((resolve, reject) => {
    const tick = () => {
      if (typeof window.google?.maps?.importLibrary === "function") {
        resolve();
        return;
      }
      if (Date.now() > deadline) {
        reject(
          new Error(
            "Google Maps JS loaded but `importLibrary` never appeared. Enable Maps JavaScript API, use a valid browser key, and check the browser console for Maps errors.",
          ),
        );
        return;
      }
      window.setTimeout(tick, BOOTSTRAP_POLL_MS);
    };
    tick();
  });
}

/**
 * Injects the Maps script once and waits until `google.maps.importLibrary` is callable.
 * Do not resolve on `onload` alone — `importLibrary` is attached asynchronously after load.
 */
export async function loadMapsScript(): Promise<void> {
  if (typeof window === "undefined") return;

  if (typeof window.google?.maps?.importLibrary === "function") {
    return;
  }

  const existing = document.getElementById("google-maps-js");
  if (existing) {
    await waitForImportLibrary();
    return;
  }

  if (!mapsJsKey) {
    throw new Error("NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY is not set");
  }

  await new Promise<void>((resolve, reject) => {
    const s = document.createElement("script");
    s.id = "google-maps-js";
    const key = encodeURIComponent(mapsJsKey);
    // `v=weekly` keeps the dynamic-import bootstrap current; `loading=async` defers execution.
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&loading=async&v=weekly`;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Google Maps JavaScript API"));
    document.head.appendChild(s);
  });

  await waitForImportLibrary();
}
