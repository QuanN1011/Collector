"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

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
  onPlaceResolved: (place: ResolvedPlace) => void;
};

const DEBOUNCE_MS = 280;
const MIN_CHARS = 2;

/** New Places API (Autocomplete Data) — `PlacePrediction` from `importLibrary("places")`. */
type PlacePredictionNew = {
  placeId: string;
  mainText?: { text?: string };
  secondaryText?: { text?: string };
  text: { text: string };
  toPlace: () => google.maps.places.Place;
};

type RowModel = {
  key: string;
  main: string;
  secondary: string;
  prediction: PlacePredictionNew;
};

function locationToLatLng(
  loc: google.maps.LatLng | google.maps.LatLngLiteral | null | undefined,
): { lat: number; lng: number } | null {
  if (loc == null) return null;
  const lat = typeof (loc as google.maps.LatLng).lat === "function" ? (loc as google.maps.LatLng).lat() : (loc as google.maps.LatLngLiteral).lat;
  const lng = typeof (loc as google.maps.LatLng).lng === "function" ? (loc as google.maps.LatLng).lng() : (loc as google.maps.LatLngLiteral).lng;
  if (typeof lat !== "number" || typeof lng !== "number") return null;
  return { lat, lng };
}

function suggestionToRow(s: { placePrediction?: PlacePredictionNew }): RowModel | null {
  const p = s.placePrediction;
  if (!p?.placeId) return null;
  const main = p.mainText?.text ?? p.text?.text ?? "";
  const secondary = p.secondaryText?.text ?? "";
  return { key: p.placeId, main, secondary, prediction: p };
}

/**
 * Places API **(New)** programmatic autocomplete:
 * `AutocompleteSuggestion.fetchAutocompleteSuggestions` + `PlacePrediction.toPlace().fetchFields()`.
 * Does not use legacy `PlacesService`, `AutocompleteService`, or `getDetails`.
 */
export default function PlacesAutocompleteInput({
  id,
  placeholder = "Search places and addresses",
  className = "",
  disabled = false,
  value,
  onValueChange,
  onPlaceResolved,
}: Props) {
  const listId = useId();
  const wrapRef = useRef<HTMLDivElement>(null);
  const sessionRef = useRef<google.maps.places.AutocompleteSessionToken | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cbRef = useRef(onPlaceResolved);
  const onValueChangeRef = useRef(onValueChange);

  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<RowModel[]>([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [placesReady, setPlacesReady] = useState(false);

  useEffect(() => {
    cbRef.current = onPlaceResolved;
  }, [onPlaceResolved]);

  useEffect(() => {
    onValueChangeRef.current = onValueChange;
  }, [onValueChange]);

  useEffect(() => {
    if (!mapsJsKey || disabled) {
      setPlacesReady(false);
      return;
    }

    let cancelled = false;

    void (async () => {
      try {
        await loadMapsScript();
        await google.maps.importLibrary("places");
        if (cancelled) return;

        const fetchFn = google.maps.places.AutocompleteSuggestion?.fetchAutocompleteSuggestions;
        const hasNewAutocomplete = typeof fetchFn === "function";
        if (!cancelled) setPlacesReady(hasNewAutocomplete);
      } catch {
        if (!cancelled) setPlacesReady(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mapsJsKey, disabled]);

  useEffect(() => {
    if (disabled) {
      setOpen(false);
      setRows([]);
      setLoading(false);
    }
  }, [disabled]);

  const fetchPredictions = useCallback(async (raw: string) => {
    const q = raw.trim();
    if (!placesReady || q.length < MIN_CHARS) {
      setRows([]);
      setOpen(false);
      setLoading(false);
      return;
    }

    if (!sessionRef.current) {
      sessionRef.current = new google.maps.places.AutocompleteSessionToken();
    }

    setLoading(true);
    try {
      const { suggestions } = await google.maps.places.AutocompleteSuggestion.fetchAutocompleteSuggestions({
        input: q,
        sessionToken: sessionRef.current,
      });

      const next: RowModel[] = [];
      for (const s of suggestions ?? []) {
        const row = suggestionToRow(s as { placePrediction?: PlacePredictionNew });
        if (row) next.push(row);
      }

      if (next.length === 0) {
        setRows([]);
        setOpen(false);
      } else {
        setRows(next);
        setOpen(true);
        setActiveIndex(-1);
      }
    } catch {
      setRows([]);
      setOpen(false);
    } finally {
      setLoading(false);
    }
  }, [placesReady]);

  const scheduleFetch = useCallback(
    (raw: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        void fetchPredictions(raw);
      }, DEBOUNCE_MS);
    },
    [fetchPredictions],
  );

  const selectRow = useCallback(async (row: RowModel) => {
    try {
      const place = row.prediction.toPlace();
      await place.fetchFields({
        fields: ["displayName", "formattedAddress", "location"],
      });

      sessionRef.current = null;
      setOpen(false);
      setRows([]);

      const addr = (place.formattedAddress ?? place.displayName ?? row.prediction.text.text).trim();
      const coords = locationToLatLng(place.location);

      if (!addr) {
        onValueChangeRef.current(row.prediction.text.text);
        return;
      }

      onValueChangeRef.current(addr);

      if (coords) {
        cbRef.current({
          formattedAddress: addr,
          lat: coords.lat,
          lng: coords.lng,
        });
      }
    } catch {
      sessionRef.current = null;
      setOpen(false);
      setRows([]);
      onValueChangeRef.current(row.prediction.text.text);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const onInputChange = (v: string) => {
    onValueChange(v);
    if (!placesReady || !mapsJsKey) return;
    scheduleFetch(v);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!open || rows.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(rows.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault();
      void selectRow(rows[activeIndex]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const onInputFocus = () => {
    if (placesReady && value.trim().length >= MIN_CHARS) {
      void fetchPredictions(value);
    }
  };

  if (!mapsJsKey) {
    return (
      <input
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

  return (
    <div ref={wrapRef} className="relative w-full min-w-0">
      <input
        id={id}
        type="text"
        value={value}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={onKeyDown}
        onFocus={onInputFocus}
        disabled={disabled}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        className={`w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 text-slate-950 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 disabled:opacity-60 ${className}`}
      />

      {open && rows.length > 0 && !disabled ? (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-[9999] mt-1 max-h-[min(22rem,45vh)] overflow-y-auto rounded-xl border border-slate-200/95 bg-white py-1 shadow-2xl shadow-slate-900/15 ring-1 ring-black/5"
        >
          {rows.map((row, i) => (
            <li
              key={row.key}
              role="option"
              aria-selected={i === activeIndex}
              className={`cursor-pointer border-b border-slate-100 px-3 py-2.5 last:border-b-0 ${
                i === activeIndex ? "bg-slate-100" : "bg-white hover:bg-slate-50"
              }`}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseDown={(ev) => {
                ev.preventDefault();
                void selectRow(row);
              }}
            >
              <div className="text-[15px] font-medium leading-snug text-slate-900">{row.main}</div>
              {row.secondary ? (
                <div className="mt-0.5 text-sm leading-snug text-slate-500">{row.secondary}</div>
              ) : null}
            </li>
          ))}
          <li className="border-t border-slate-100 px-3 py-2">
            <a
              href="https://developers.google.com/maps/documentation/javascript/places-migration-autocomplete"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-slate-600"
              onMouseDown={(e) => e.stopPropagation()}
            >
              <img
                src="https://maps.gstatic.com/mapfiles/api-3/images/powered-by-google-on-white3_hdpi.png"
                alt=""
                width={120}
                height={14}
                className="h-3.5 w-auto opacity-80"
              />
            </a>
          </li>
        </ul>
      ) : null}

      {loading && placesReady && !disabled ? (
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-medium text-slate-400">
          …
        </div>
      ) : null}
    </div>
  );
}
