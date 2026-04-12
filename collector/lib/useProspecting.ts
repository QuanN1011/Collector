"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchBuilding, fetchBuildings, fetchHealth, fetchStates, fetchTopProspects } from "./api";
import type { BuildingEnriched } from "./types";

type HealthState = "checking" | "ok" | "error";

export function useProspecting() {
  const [health, setHealth] = useState<HealthState>("checking");
  const [states, setStates] = useState<string[]>([]);
  const [selectedState, setSelectedState] = useState("");
  const [buildings, setBuildings] = useState<BuildingEnriched[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState("");
  const [buildingDetail, setBuildingDetail] = useState<BuildingEnriched | null>(null);
  const [topProspects, setTopProspects] = useState<BuildingEnriched[]>([]);
  const [liveCv, setLiveCv] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStates, setLoadingStates] = useState(true);
  const [loadingBuildings, setLoadingBuildings] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingTop, setLoadingTop] = useState(false);

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
      try {
        const b = await fetchBuilding(selectedBuildingId, liveCv);
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
  }, [selectedBuildingId, liveCv]);

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
    liveCv,
    setLiveCv,
    error,
    loadingStates,
    loadingBuildings,
    loadingDetail,
    loadingTop,
  };
}

export type ProspectingModel = ReturnType<typeof useProspecting>;
