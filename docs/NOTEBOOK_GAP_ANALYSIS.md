# Notebook vs Application: What’s Implemented and What’s Missing

This document maps **Jupyter Notebook functionality** to the **current application** so you can show what is implemented, what is partial, and what is still missing.

---

## How to Use This for a Demo

1. **Implemented** – You can say: “This notebook step is fully in the app” and show the corresponding UI/API.
2. **Partial** – You can say: “We have this in the app but not every sub-check or detail from the notebook.”
3. **Missing / Not in UI** – You can say: “The notebook did this; we don’t have it in the app yet (or only in backend/API).”

Reference: **`backend/docs/NOTEBOOK_REJECTION_MAPPING.md`** maps each rejection reason to the app function and notebook concept.

---

## 1. Data Loading and File Discovery

| Notebook | Application | Status |
|----------|-------------|--------|
| Read Tape20Loans CSV by date | Dynamic file discovery: `Tape20Loans_MM-DD-YYYY.csv` (yesterday) | ✅ Implemented |
| Read SFY/PRIME Exhibit files by date | Dynamic discovery; optional “most recent” | ✅ Implemented |
| Read reference files (MASTER_SHEET, Underwriting, etc.) | Loaded from `files_required/` in pipeline | ✅ Implemented |
| Fixed/hardcoded file paths | Removed; uses date utils and discovery | ✅ Implemented |

**Demo**: “We no longer hardcode file names; we discover files by date and pattern.”

---

## 2. Date Logic

| Notebook | Application | Status |
|----------|-------------|--------|
| Purchase date = next Tuesday | `calculate_next_tuesday()`; used as `pdate` | ✅ Implemented |
| Yesterday for Tape20Loans | `calculate_yesterday()` (MM-DD-YYYY) | ✅ Implemented |
| Last month end for FX files | `calculate_last_month_end()` | ✅ Implemented |
| CoMAP table choice by submit date (e.g. post Oct 24, 2025) | Date-based branch in CoMAP rules | ✅ Implemented |

**Demo**: “Purchase date and file dates match the notebook logic (e.g. next Tuesday).”

---

## 3. Purchase Price Validation

| Notebook | Application | Status |
|----------|-------------|--------|
| Compare lender price to modeled price | `rules.purchase_price.check_purchase_price` | ✅ Implemented |
| Flag mismatches | `get_purchase_price_exceptions`; stored as exceptions | ✅ Implemented |
| Rounding (e.g. 2 decimals) | `round(modeled_purchase_price * 100, 2)` | ✅ Implemented |

**Demo**: Exceptions page → filter by **Purchase Price**; or API `GET /api/exceptions?exception_type=purchase_price`. Rejection key: `notebook.purchase_price_mismatch`.

---

## 4. Underwriting Checks

| Notebook | Application | Status |
|----------|-------------|--------|
| SFY underwriting grid (balance, DTI, FICO, income) | `check_underwriting` with SFY grid | ✅ Implemented |
| Prime underwriting grid | Same with Prime grid | ✅ Implemented |
| Notes (HD NOTE) underwriting | Same with Notes grid, `is_notes=True` | ✅ Implemented |
| FICO > 700 income waiver + PTI | In underwriting logic | ✅ Implemented |
| TU loans excluded from check | `tuloans` passed in; excluded in check | ✅ Implemented |

**Demo**: Exceptions → filter by **Underwriting** (or underwriting_notes). Rejection keys: `notebook.underwriting_sfy`, `notebook.underwriting_prime`, `notebook.underwriting_notes`.

---

## 5. CoMAP Validation

| Notebook | Application | Status |
|----------|-------------|--------|
| Prime CoMAP (FICO bands, loan program in grid) | `rules.comap.check_comap_prime` | ✅ Implemented |
| SFY CoMAP | `rules.comap.check_comap_sfy` | ✅ Implemented |
| Notes CoMAP | `rules.comap.check_comap_notes` | ✅ Implemented |
| Date-based table (e.g. Oct 25 tables) | Submit date > 2025-10-24 branch | ✅ Implemented |
| Missing columns in Excel (e.g. 780+) | Defensive checks; only use existing columns | ✅ Implemented |

**Demo**: Exceptions → filter by exception type that corresponds to CoMAP (e.g. comap_prime/comap_sfy/comap_notes if exposed). Rejection keys: `notebook.comap_prime`, `notebook.comap_sfy`, `notebook.comap_notes`.

---

## 6. Eligibility Checks (Portfolio-Level)

| Notebook | Application | Status |
|----------|-------------|--------|
| Prime: A, B1, B3, C, D, E, F, G (balance/type thresholds) | `rules.eligibility.check_eligibility_prime` | ✅ Implemented |
| Prime: H1, H2, H3 (lender price, dealer fee) | In eligibility module | ✅ Implemented |
| Prime: I1, I2 (balance > 50k, mean balance) | In eligibility module | ✅ Implemented |
| Prime: L1–L4 (FICO distribution) | In eligibility module | ✅ Implemented |
| Prime: S1 (new_programs) | In eligibility module | ✅ Implemented |
| Prime: Check J (property state distribution) | Informational / stored; not enforced as pass/fail | ⚠️ Partial |
| SFY: A, B, C, D, E, F, G, H, J, L, etc. | `rules.eligibility.check_eligibility_sfy` | ✅ Implemented (many checks) |
| SFY: Some BD-type and promo_term checks | In eligibility module | ✅ Implemented |
| Eligibility results in Excel report | Exported; path in run result | ✅ Implemented |
| Eligibility results in UI | Shown in run summary/detail if wired | ⚠️ Partial (backend has data; UI may not show all) |

**Demo**: “Portfolio eligibility (Prime and SFY) runs in the pipeline and is exported to Excel; we can show the file or the run result in the API.” For “what’s missing”: “Check J is informational only; we don’t enforce property state limits as pass/fail.”

---

## 7. Exception Reports and Excel Outputs

| Notebook | Application | Status |
|----------|-------------|--------|
| Purchase price mismatch report | Export + stored exceptions | ✅ Implemented |
| Underwriting flagged report | Export + stored exceptions | ✅ Implemented |
| CoMAP failed report | Export + stored exceptions | ✅ Implemented |
| Eligibility report (Prime/SFY) | `export_eligibility_report` | ✅ Implemented |
| Reports written to output directory | Sales-team-specific output paths | ✅ Implemented |
| View/download reports in UI | Not in UI; files on disk / share path | ❌ Missing (backend only) |

**Demo**: “Same exception and eligibility outputs as the notebook are generated and saved; we can open the output folder to show the Excel files.” For gap: “We don’t yet have a ‘Download report’ button in the UI.”

---

## 8. Day-of-Week and Disposition (Post-Notebook)

| Concept | Application | Status |
|---------|-------------|--------|
| Segregate by day of week | `run_weekday` / `run_weekday_name` on run (from pdate) | ✅ Implemented |
| Filter runs by weekday | API: `GET /api/runs?run_weekday=0..6` | ✅ Implemented |
| Loans “to purchase” vs “rejected” | `disposition` on loan facts; rejection_criteria set | ✅ Implemented |
| Filter loans by disposition | API: `GET /api/loans?run_id=...&disposition=to_purchase|rejected` | ✅ Implemented |
| Rejection reason → notebook | `rejection_criteria` (e.g. notebook.purchase_price_mismatch) | ✅ Implemented |
| Day/weekday and disposition in UI | Not yet in frontend | ❌ Missing (API ready) |

**Demo**: “We added day-of-week and to-purchase vs rejected tracking; you can see it in the API. The UI can be extended to show filters for weekday and disposition.”

---

## 9. Authentication and Multi-Tenancy (Not in Notebook)

| Feature | Application | Status |
|---------|-------------|--------|
| Login / JWT | Auth routes + frontend login | ✅ Implemented |
| Role-based access (Admin, Analyst, Sales) | Backend + frontend | ✅ Implemented |
| Sales team data isolation | Paths and queries filtered by sales_team_id | ✅ Implemented |
| Audit logging (e.g. login) | auth.audit | ✅ Implemented |

**Demo**: “The app adds login and per–sales-team isolation; the notebook had no auth.”

---

## 10. Scheduler and Automation (Not in Notebook)

| Feature | Application | Status |
|---------|-------------|--------|
| Daily scheduled run | APScheduler; configurable time | ✅ Implemented |
| Per–sales-team paths for scheduled run | In job_scheduler | ✅ Implemented |
| Notifications on run start/fail | In scheduler/notifications | ✅ Implemented |

**Demo**: “We can run the same pipeline on a schedule; the notebook was manual.”

---

## 11. Gaps Summary: How to Say “What’s Missing”

**Fully aligned with notebook**

- File discovery and date logic  
- Purchase price, underwriting, CoMAP validations  
- Exception generation and Excel exception reports  
- Eligibility checks (Prime/SFY) and eligibility Excel export  
- Rejection reason mapping to notebook concepts (`rejection_criteria`)

**Partial / different from notebook**

- **Check J (property state)**: Implemented for info only; not a pass/fail threshold.  
- **Eligibility in UI**: Data is in backend and in exported Excel; not every eligibility metric may be on the Run detail page.  
- **Report download**: Reports are on disk; no “Download report” in UI yet.

**Not in UI (but in API)**

- Filter runs by **weekday** (`run_weekday`).  
- Filter loans by **disposition** (to_purchase / rejected).  
- Filter exceptions by **rejection_criteria** (notebook key).

**Not implemented / future**

- Run retry logic (transient failures).  
- Per–sales-team run schedule configuration in UI.  
- In-app report viewer or download from UI.

---

## 12. One-Page “What to Show” Cheat Sheet

- **Login** → “Auth added; notebook had none.”  
- **Dashboard / Runs** → “Same runs as notebook; we can trigger from UI.”  
- **Exceptions + filter by type** → “Same validations as notebook (purchase price, underwriting, CoMAP); each row has a type and can map to `rejection_criteria`.”  
- **API docs** → “Runs, exceptions, loans (to_purchase/rejected), health; all notebook logic is behind these endpoints.”  
- **Excel outputs** → “Same exception and eligibility reports as notebook; we open the output folder.”  
- **What’s missing** → “Property state (J) is informational only; report download and weekday/disposition filters are in API, not yet in UI.”

Use **`backend/docs/NOTEBOOK_REJECTION_MAPPING.md`** when you need to point from a specific exception or rejection reason to the exact notebook concept and app function.
