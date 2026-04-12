"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchAnalyzeBuilding,
  fetchBuilding,
  fetchBuildings,
  fetchHealth,
  fetchStates,
  fetchTopProspects,
} from "./api";
import { mergeAnalyzeIntoBuildingEnriched } from "./mergeAddressAnalysis";
import type { AnalyzeBuildingResponse, BuildingEnriched } from "./types";

type HealthState = "checking" | "ok" | "error";

export function useProspecting() {
  const [health, setHealth] = useState<HealthState>("checking");
  const [states, setStates] = useState<string[]>([]);
  const [selectedState, setSelectedState] = useState("");
  const [buildings, setBuildings] = useState<BuildingEnriched[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState("");
  const [buildingDetail, setBuildingDetail] = useState<BuildingEnriched | null>(null);
  const [topProspects, setTopProspects] = useState<BuildingEnriched[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingStates, setLoadingStates] = useState(true);
  const [loadingBuildings, setLoadingBuildings] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingTop, setLoadingTop] = useState(false);
  const [satelliteLoading, setSatelliteLoading] = useState(false);
  const [streetAddress, setStreetAddress] = useState("");
  const [addressAnalyzeResult, setAddressAnalyzeResult] = useState<AnalyzeBuildingResponse | null>(null);

  const refreshHealth = useCallback(async () => {
    setHealth("checking");
    try {
      const h = await fetchHealth();
      setHealth(h.status === "ok" ? "ok" : "error");
    } catch {
      setHealth("error");
    }
  }, []);

  useEffect(() => {
    void refreshHealth();
  }, [refreshHealth]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoadingStates(true);
      setError(null);
      try {
        const { states: list } = await fetchStates();
        if (cancelled) return;
        setStates(list);
        if (list.length) {
          setSelectedState((prev) => {
            if (prev) return prev;
            return list.includes("TX") ? "TX" : list[0];
          });
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load states");
      } finally {
        if (!cancelled) setLoadingStates(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setAddressAnalyzeResult(null);
  }, [selectedState]);

  useEffect(() => {
    if (!selectedState) {
      setBuildings([]);
      setSelectedBuildingId("");
      setBuildingDetail(null);
      setTopProspects([]);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoadingBuildings(true);
      setError(null);
      try {
        const list = await fetchBuildings(selectedState);
        if (cancelled) return;
        setBuildings(list);
        setSelectedBuildingId((prev) => {
          if (prev && list.some((b) => b.id === prev)) return prev;
          return list[0]?.id ?? "";
        });
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load buildings");
        setBuildings([]);
        setSelectedBuildingId("");
      } finally {
        if (!cancelled) setLoadingBuildings(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedState]);

  useEffect(() => {
    if (!selectedBuildingId) {
      setBuildingDetail(null);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoadingDetail(true);
      setError(null);
      setBuildingDetail(null);
      try {
        const b = await fetchBuilding(selectedBuildingId, false);
        if (!cancelled) setBuildingDetail(b);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load building");
          setBuildingDetail(null);
        }
      } finally {
        if (!cancelled) setLoadingDetail(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedBuildingId]);

  const stateContextSample = useMemo(() => {
    if (!buildings.length) return null;
    return buildings.find((b) => b.id === selectedBuildingId) ?? buildings[0] ?? null;
  }, [buildings, selectedBuildingId]);

  /** Merged row for water economics when address pipeline was used. */
  const economicsBuilding = useMemo((): BuildingEnriched | null => {
    if (addressAnalyzeResult) {
      if (!stateContextSample) return null;
      return mergeAnalyzeIntoBuildingEnriched(stateContextSample, addressAnalyzeResult);
    }
    return buildingDetail;
  }, [addressAnalyzeResult, stateContextSample, buildingDetail]);

  const runSatelliteAnalysis = useCallback(async () => {
    if (!selectedState) {
      setError("Select a state first.");
      return;
    }
    setError(null);
    setSatelliteLoading(true);
    try {
      const trimmed = streetAddress.trim();
      if (trimmed) {
        const r = await fetchAnalyzeBuilding(trimmed, selectedState);
        setAddressAnalyzeResult(r);
      } else {
        if (!selectedBuildingId) {
          setError("Select a catalog building or choose an address from search.");
          return;
        }
        setAddressAnalyzeResult(null);
        const b = await fetchBuilding(selectedBuildingId, true);
        setBuildingDetail(b);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setSatelliteLoading(false);
    }
  }, [selectedState, selectedBuildingId, streetAddress]);

  const refreshTopProspects = useCallback(async () => {
    if (!selectedState) return;
    setLoadingTop(true);
    setError(null);
    try {
      const rows = await fetchTopProspects(selectedState, 30);
      setTopProspects(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load top prospects");
      setTopProspects([]);
    } finally {
      setLoadingTop(false);
    }
  }, [selectedState]);

  useEffect(() => {
    if (selectedState) void refreshTopProspects();
  }, [selectedState, refreshTopProspects]);

  return {
    health,
    refreshHealth,
    states,
    selectedState,
    setSelectedState,
    buildings,
    selectedBuildingId,
    setSelectedBuildingId,
    buildingDetail,
    topProspects,
    refreshTopProspects,
    streetAddress,
    setStreetAddress,
    addressAnalyzeResult,
    stateContextSample,
    economicsBuilding,
    runSatelliteAnalysis,
    satelliteLoading,
    error,
    loadingStates,
    loadingBuildings,
    loadingDetail,
    loadingTop,
  };
}

export type ProspectingModel = ReturnType<typeof useProspecting>;
