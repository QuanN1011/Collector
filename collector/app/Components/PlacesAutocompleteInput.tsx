"use client";

import { useEffect, useRef } from "react";

import { loadMapsScript, mapsJsKey } from "@/lib/googleMapsLoader";

export type ResolvedPlace = {
  formattedAddress: string;
  lat: number;
  lng: number;
};

type Props = {
  id?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  value: string;
  onValueChange: (value: string) => void;
  /** Fires when user picks a suggestion (lat/lng from Places geometry). */
  onPlaceResolved: (place: ResolvedPlace) => void;
};

function latLngParts(loc: google.maps.LatLng | google.maps.LatLngLiteral): { lat: number; lng: number } {
  const lat = typeof loc.lat === "function" ? loc.lat() : loc.lat;
  const lng = typeof loc.lng === "function" ? loc.lng() : loc.lng;
  return { lat, lng };
}

/**
 * Native text field so typing always works in React. When a Maps key is set, optionally attaches
 * legacy `google.maps.places.Autocomplete` to the same input for suggestions (when the API still exposes it).
 * The `PlaceAutocompleteElement` web component was dropped — it conflicted with React + shadow DOM in practice.
 */
export default function PlacesAutocompleteInput({
  id,
  placeholder = "Start typing an address…",
  className = "",
  disabled = false,
  value,
  onValueChange,
  onPlaceResolved,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const acRef = useRef<google.maps.places.Autocomplete | null>(null);
  const cbRef = useRef(onPlaceResolved);
  const onValueChangeRef = useRef(onValueChange);

  useEffect(() => {
    cbRef.current = onPlaceResolved;
  }, [onPlaceResolved]);

  useEffect(() => {
    onValueChangeRef.current = onValueChange;
  }, [onValueChange]);

  useEffect(() => {
    if (!mapsJsKey || disabled) {
      const ac = acRef.current;
      acRef.current = null;
      if (ac && typeof google !== "undefined" && google.maps?.event) {
        google.maps.event.clearInstanceListeners(ac);
      }
      return;
    }

    let cancelled = false;

    void (async () => {
      try {
        await loadMapsScript();
        await google.maps.importLibrary("places");
        if (cancelled || !inputRef.current) return;

        const AutocompleteCtor = (
          google.maps.places as unknown as {
            Autocomplete?: new (input: HTMLInputElement, opts?: google.maps.places.AutocompleteOptions) => google.maps.places.Autocomplete;
          }
        ).Autocomplete;

        if (typeof AutocompleteCtor !== "function") return;

        const ac = new AutocompleteCtor(inputRef.current, {
          types: ["geocode"],
          fields: ["formatted_address", "geometry"],
        });
        acRef.current = ac;

        ac.addListener("place_changed", () => {
          const place = ac.getPlace();
          const loc = place.geometry?.location;
          const addr = (place.formatted_address ?? "").trim();
          if (!loc || !addr) return;
          const { lat, lng } = latLngParts(loc);
          onValueChangeRef.current(addr);
          cbRef.current({ formattedAddress: addr, lat, lng });
        });
      } catch {
        /* Autocomplete unavailable for this key/project — plain typing still works */
      }
    })();

    return () => {
      cancelled = true;
      const ac = acRef.current;
      acRef.current = null;
      if (ac && typeof google !== "undefined" && google.maps?.event) {
        google.maps.event.clearInstanceListeners(ac);
      }
    };
  }, [mapsJsKey, disabled]);

  return (
    <input
      ref={inputRef}
      id={id}
      type="text"
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      disabled={disabled}
      placeholder={placeholder}
      autoComplete="street-address"
      spellCheck={false}
      className={`w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60 ${className}`}
    />
  );
}
