"use client";

import { useEffect, useRef, useState } from "react";

import { loadMapsScript, mapsJsKey } from "@/lib/googleMapsLoader";

export default function InteractiveSatelliteMap({ lat, lng }: { lat: number; lng: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [mapErr, setMapErr] = useState<string | null>(null);

  useEffect(() => {
    if (!mapsJsKey || !ref.current) return;
    let disposed = false;
    void (async () => {
      try {
        await loadMapsScript();
        if (disposed || !ref.current) return;
        const [{ Map, MapTypeId }, { Marker }] = await Promise.all([
          google.maps.importLibrary("maps") as Promise<google.maps.MapsLibrary>,
          google.maps.importLibrary("marker") as Promise<google.maps.MarkerLibrary>,
        ]);
        if (disposed || !ref.current) return;
        const center = { lat, lng };
        const map = new Map(ref.current, {
          center,
          zoom: 19,
          mapTypeId: MapTypeId.HYBRID,
        });
        new Marker({ position: center, map, title: "Site" });
      } catch (e) {
        if (!disposed) setMapErr(e instanceof Error ? e.message : "Map error");
      }
    })();
    return () => {
      disposed = true;
    };
  }, [lat, lng]);

  if (!mapsJsKey) {
    return (
      <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-600">
        Add <code className="rounded bg-white px-1 py-0.5 font-mono text-[11px]">NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY</code> for an
        interactive hybrid map (restrict by HTTP referrer).
      </p>
    );
  }
  if (mapErr) {
    return <p className="text-xs text-rose-700">{mapErr}</p>;
  }
  return <div ref={ref} className="h-[min(360px,50vw)] w-full min-h-[240px] rounded-xl border border-slate-200 shadow-sm" />;
}
