# Using external water-price data (e.g. World Population Review)

This note explains how a ranking page like **[Water Prices by State](https://worldpopulationreview.com/state-rankings/water-prices-by-state)** relates to RainUSE’s **`water_price_per_1000_gal_usd`** field, and **how to ingest data without web scraping**.

---

## 1. What that page actually shows

World Population Review publishes an **estimated average *monthly water bill* (USD)** per state (e.g. their 2025 table). They cite third-party summaries such as LawnStarter and Forbes on the same page.

That is **not** the same unit as our database:

| Source metric | RainUSE field |
|---------------|----------------|
| **$/month** (typical residential bill) | **`water_price_per_1000_gal_usd`** — marginal-style **USD per 1,000 gallons** used in `services/roi.py` and scoring |

So you **cannot** paste the monthly dollar amount directly into `state_context.csv` without a **documented conversion** (or a different schema column).

---

## 2. Converting monthly bill → $/1,000 gal (illustrative)

Implied **effective** price per gallon:

\[
\text{USD per 1,000 gal} = \frac{\text{monthly\_bill\_usd}}{\text{gallons\_per\_month}} \times 1000
\]

**Gallons per month** is an assumption. Examples the same ecosystem often uses:

- **~100 gal/person/day** for a household (WPR text references a family-of-four example).
- For **4 people × 100 gal/day × ~30 days ≈ 12,000 gal/month**, then  
  `water_price_per_1000_gal ≈ monthly_bill / 12`.

Example: **Texas ~\$48/month** → \(48 / 12 \approx \$4.00\) per 1,000 gal (only as rough as the bill + usage assumptions).

**Caveats:**

- Bills may **include fixed fees**, **tiered rates**, or **sewer bundled** differently by state — a single divisor is a **proxy**, not a utility rate schedule.
- **Commercial / industrial** rates often differ from **residential** averages; for a B2B story you may later prefer **city or utility-specific** rates (see `CITY_UTILITY_OVERRIDES` in `services/seed_scoring.py`).

Document your chosen **gallons/month** (or persons × gpd × days) in the import README or CSV header comment.

---

## 3. Web scraping vs other methods

| Approach | Verdict |
|----------|--------|
| **Automated scraping** of World Population Review | **Not recommended.** Pages change, tables break, and **site Terms of Use** may prohibit bulk automated extraction. You also inherit **copyright/layout** risk for republishing. |
| **Official / primary sources** | Stronger for a real product: **utility rate tariffs**, **state PUC filings**, **AWWA / EPA references**, etc. More work, clearer rights. |
| **Manual snapshot → CSV in repo** | **Best default for a class/hackathon.** Copy the published numbers once (or type from the table), save e.g. `data/imports/water_monthly_bill_by_state_2025.csv`, **cite the URL + date** in a comment or `SOURCES.md`. |
| **One-off script reading *your* CSV** | Fine: a small `scripts/ingest_*` that reads **your** file and writes/merges **`water_price_per_1000_gal_usd`** into `state_context.csv` or Postgres — still **no** HTTP scrape of WPR. |
| **Public API from WPR** | They do **not** provide a standard public data API for this table; treat the site as **human-facing reference**, not a machine endpoint. |

---

## 4. Wiring into this codebase

1. **Keep** `backend/data/state_context.csv` (or DB `state_context`) as the source of truth for **`water_price_per_1000_gal_usd`**.
2. Add a **derived** or **import** CSV under e.g. `data/imports/` with columns like `state`, `monthly_water_bill_usd`, `source_url`, `retrieved_date`.
3. Either:
   - **Compute** `water_price_per_1000_gal_usd` in a script and merge (like `scripts/ingest_state_precip_open_meteo.py` does for rainfall), or  
   - **Manually** fill `water_price_per_1000_gal_usd` after spreadsheet conversion and commit.

4. Re-run **`seed_database.py`** (or your migration path) if Postgres should pick up new values.

---

## 5. Summary

- **Use** World Population Review (and its cited sources) as a **reference** to **populate or sanity-check** state-level rates.
- **Do not** rely on **scraping** that site in production.
- **Convert** monthly bill → **$/1,000 gal** only with **explicit, documented assumptions**, and prefer **city/utility** data when you move beyond a coarse state proxy.

---

*This document is guidance only, not legal advice. Check each publisher’s terms and your use case before automating downloads.*
