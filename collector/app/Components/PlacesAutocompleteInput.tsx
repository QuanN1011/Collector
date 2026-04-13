"use client";

import { useEffect, useRef } from "react";

import { loadMapsScript, mapsJsKey } from "@/lib/googleMapsLoader";

type Props = {
  id?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  value: string;
  onChange: (value: string) => void;
};

/**
 * Normal controlled text input so focus/typing always works. With a Maps key, attaches
 * classic `google.maps.places.Autocomplete` (`.pac-container` suggestions).
 */
export default function PlacesAutocompleteInput({
  id,
  placeholder = "Type or paste a full street address…",
  className = "",
  disabled = false,
  value,
  onChange,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const acRef = useRef<google.maps.places.Autocomplete | null>(null);
  const onChangeRef = useRef(onChange);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    const destroy = () => {
      const ac = acRef.current;
      acRef.current = null;
      if (ac && typeof google !== "undefined" && google.maps?.event) {
        google.maps.event.clearInstanceListeners(ac);
      }
    };

    destroy();

    if (!mapsJsKey || disabled) return;

    const input = inputRef.current;
    if (!input) return;

    let cancelled = false;

    void (async () => {
      try {
        await loadMapsScript();
        if (cancelled || !inputRef.current) return;
        const Autocomplete = google.maps.places.Autocomplete;
        if (!Autocomplete) {
          console.error("[PlacesAutocompleteInput] google.maps.places.Autocomplete missing");
          return;
        }

        const ac = new Autocomplete(inputRef.current, {
          fields: ["formatted_address", "geometry", "name"],
        });
        acRef.current = ac;
        ac.addListener("place_changed", () => {
          const place = ac.getPlace();
          const addr = (place.formatted_address ?? place.name ?? "").trim();
          if (addr) onChangeRef.current(addr);
        });
      } catch (err) {
        console.error("[PlacesAutocompleteInput] Autocomplete attach failed", err);
      }
    })();

    return () => {
      cancelled = true;
      destroy();
    };
  }, [disabled, mapsJsKey]);

  const inputClass =
    "w-full min-w-0 rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60";

  return (
    <input
      ref={inputRef}
      id={id}
      type="text"
      autoComplete="street-address"
      enterKeyHint="search"
      disabled={disabled}
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`${inputClass} ${className}`.trim()}
    />
  );
}
