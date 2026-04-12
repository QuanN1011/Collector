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
  /** Fires when user picks a suggestion (lat/lng from Places geometry). */
  onPlaceResolved: (place: ResolvedPlace) => void;
};

type PlacesLibWithPac = google.maps.PlacesLibrary & {
  PlaceAutocompleteElement: typeof google.maps.places.PlaceAutocompleteElement;
};

function latLngParts(loc: google.maps.LatLng | google.maps.LatLngLiteral): { lat: number; lng: number } {
  const lat = typeof loc.lat === "function" ? loc.lat() : loc.lat;
  const lng = typeof loc.lng === "function" ? loc.lng() : loc.lng;
  return { lat, lng };
}

/**
 * Google Places autocomplete (new `PlaceAutocompleteElement`). Legacy `Autocomplete` is unavailable
 * for new API projects; requires browser key + Places API (New) / Maps JS places library.
 */
export default function PlacesAutocompleteInput({
  id,
  placeholder = "Start typing an address…",
  className = "",
  disabled = false,
  onPlaceResolved,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cbRef = useRef(onPlaceResolved);

  useEffect(() => {
    cbRef.current = onPlaceResolved;
  }, [onPlaceResolved]);

  useEffect(() => {
    if (!mapsJsKey || !containerRef.current || disabled) return;

    const container = containerRef.current;
    let cancelled = false;
    let pac: google.maps.places.PlaceAutocompleteElement | null = null;

    const onSelect = async (ev: Event) => {
      if (cancelled) return;
      const placePrediction = (ev as unknown as { placePrediction?: google.maps.places.PlacePrediction })
        .placePrediction;
      if (!placePrediction) return;

      try {
        const place = placePrediction.toPlace();
        await place.fetchFields({
          fields: ["displayName", "formattedAddress", "location"],
        });
        const loc = place.location;
        if (!loc) return;
        const { lat, lng } = latLngParts(loc);
        cbRef.current({
          formattedAddress:
            (place.formattedAddress ?? place.displayName ?? "").trim() ||
            (typeof (pac as unknown as { value?: string }).value === "string"
              ? (pac as unknown as { value: string }).value.trim()
              : ""),
          lat,
          lng,
        });
      } catch {
        /* ignore selection fetch errors */
      }
    };

    void (async () => {
      try {
        await loadMapsScript();
        const { PlaceAutocompleteElement } = (await google.maps.importLibrary(
          "places",
        )) as PlacesLibWithPac;
        if (cancelled || !container) return;

        const opts: google.maps.places.PlaceAutocompleteElementOptions = {
          types: ["geocode"],
        };
        const el = new PlaceAutocompleteElement(opts);
        if (id) el.id = id;
        el.setAttribute("placeholder", placeholder);

        el.addEventListener("gmp-select", onSelect);
        if (cancelled) {
          el.removeEventListener("gmp-select", onSelect);
          return;
        }
        container.appendChild(el);
        pac = el;
      } catch {
        /* load / library failure */
      }
    })();

    return () => {
      cancelled = true;
      if (pac) {
        pac.removeEventListener("gmp-select", onSelect);
        pac.remove();
        pac = null;
      }
    };
  }, [disabled, id, placeholder]);

  if (!mapsJsKey) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`places-autocomplete-host w-full min-w-0 [&_gmp-place-autocomplete]:block [&_gmp-place-autocomplete]:w-full ${className}`}
    />
  );
}
