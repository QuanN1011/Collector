/**
 * Load Maps JavaScript API once. Includes `places` for Autocomplete + map widgets.
 * Enable: Maps JavaScript API + Places API (Autocomplete). Key: NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY
 */
export const mapsJsKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY ?? "";

export function loadMapsScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.google?.maps) return Promise.resolve();

  const existing = document.getElementById("google-maps-js");
  if (existing) {
    return new Promise((resolve, reject) => {
      const deadline = Date.now() + 25_000;
      const id = window.setInterval(() => {
        if (window.google?.maps) {
          window.clearInterval(id);
          resolve();
        } else if (Date.now() > deadline) {
          window.clearInterval(id);
          reject(new Error("Google Maps JS load timeout"));
        }
      }, 50);
    });
  }

  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.id = "google-maps-js";
    const key = encodeURIComponent(mapsJsKey);
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places&loading=async`;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Google Maps JavaScript API"));
    document.head.appendChild(s);
  });
}
