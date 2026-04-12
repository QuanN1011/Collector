# Optional future work: condensate modeling

This document explains why **condensate (HVAC / cooling-coil) water yield is not implemented** in the current RainUSE Nexus prototype, how it **could** be added later, and **why it would help** the product story and scoring—without implying it is required for the hackathon MVP.

---

## Current state (not implemented)

The backend scores buildings using **roof area**, **state-level rainfall and water price** (and related mocks for **cooling tower detection** and **ESG**). There is **no** psychrometric or mass-balance calculation of **condensate flow** (gallons per day or per year), and no field dedicated solely to “condensate gallons” in the seeded demo path.

That matches the **challenge brief’s minimum physical layer**: **roof catchment**, **cooling tower presence** with **confidence**, then **financial / regulatory / corporate** signals for a **holistic viability score**. The brief does **not** require condensate volume as a deliverable.

---

## What condensate modeling would mean

**Condensate** is water removed from air as it passes through cooling coils (AHUs, chillers, and related equipment). The engineering approach (as in typical MEP references) is:

1. Determine **entering / leaving** air conditions (dry bulb, humidity or wet bulb—or RH).
2. Compute **humidity ratio** change across the coil and **air mass flow**.
3. Derive **condensate mass flow**, then convert to **volume** (e.g. gallons per unit time).

Doing this **well** requires **assumptions or inputs** the prototype does not yet ingest at scale: **design airflow**, **coil conditions**, **operating hours**, and **local weather** (or a representative climate profile).

---

## How you could implement it later

1. **Inputs (per building or prototype default):**
   - Weather: e.g. **cooling-season** temperature / humidity (from a national weather or climate API, or gridded historical normals keyed by `latitude` / `longitude`).
   - HVAC: **rough airflow or tonnage** estimates from building type and size (or defaults when unknown).
2. **Computation:** Encapsulate psychrometrics in a small **pure Python module** (formulas or a vetted library), not by embedding third-party calculator UIs.
3. **Persistence:** Store annual or peak **condensate potential** (and assumptions) on **`water_yield_estimates`** or a dedicated JSON note on **`building_scores`** / pipeline metadata—aligned with **`docs/DATABASE_DECISIONS.md`** (single source of truth for rollups).
4. **Scoring:** Fold into **`water_yield_score`** or a separate sub-pillar only if the team agrees on weights; otherwise use it for **explainability** in the UI (“additional onsite non-potable supply”).

---

## Why it would help the project (when implemented)

| Benefit | Explanation |
|--------|--------------|
| **Stronger cooling-tower story** | Towers and large **HVAC** footprints correlate with **evaporative load**. Condensate is another **recoverable onsite water stream** beside **rainwater**, which matches Net Zero / reuse narratives (e.g. condensate + rainwater to **cooling makeup** or **non-potable** uses). |
| **Better differentiation between sites** | Two buildings with similar roofs can differ sharply in **HVAC intensity**; condensate potential helps separate **data centers / industrial / large commercial** candidates. |
| **Alignment with climate stress** | Hot, humid periods drive **more** coil condensate; combining condensate with **drought / stress** signals can reinforce **why** onsite supply matters in **water-scarce** or **restriction-prone** regions. |
| **Investor / judge clarity** | A second quantitative “water opportunity” number (even approximate) makes the **ROI and impact** story more concrete than roof-only harvest. |

---

## Summary

- **Not implemented today** by design (scope and data constraints).
- **Not required** to satisfy the stated RainUSE Nexus **MVP** physical requirements.
- **Worth adding later** if the team wants a deeper **HVAC-linked water opportunity** layer and is willing to document **assumptions** and **inputs** clearly.

For the current prototype, prioritize **CV footprint + tower detection + utility/policy + ESG/climate**; treat condensate as an **optional enhancement** documented here.

---

*See also: `docs/DATABASE_DECISIONS.md` (schema and scoring principles).*
