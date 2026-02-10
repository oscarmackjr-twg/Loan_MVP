# Notebook-to-Application Rejection Criteria Mapping

This document maps **rejection criteria** from the original Jupyter Notebook to **application functions** and **canonical keys** used for day-of-week segregation and reporting (loans to purchase vs projected vs rejected).

---

## 1. Purchase Price

| Notebook concept | App function | exception_type | rejection_criteria key |
|------------------|--------------|----------------|------------------------|
| Lender price vs modeled purchase price (exact match) | `rules.purchase_price.check_purchase_price` | `purchase_price` | `notebook.purchase_price_mismatch` |
| Exceptions from mismatched loans | `rules.purchase_price.get_purchase_price_exceptions` | `purchase_price` | `notebook.purchase_price_mismatch` |

**Criteria**: Loan fails when `Lender Price(%) != round(modeled_purchase_price * 100, 2)`.

---

## 2. Underwriting

| Notebook concept | App function | exception_type | rejection_criteria key |
|------------------|--------------|----------------|------------------------|
| SFY underwriting grid (balance, DTI, FICO, income) | `rules.underwriting.check_underwriting` (with SFY grid) | `underwriting` (pipeline tags as SFY/Prime/notes) | `notebook.underwriting_sfy` |
| Prime underwriting grid | same, with Prime grid | — | `notebook.underwriting_prime` |
| Notes underwriting (HD NOTE) | same, `is_notes=True` | `underwriting_notes` | `notebook.underwriting_notes` |
| Exception records | `rules.underwriting.get_underwriting_exceptions` | `underwriting` / `underwriting_notes` | above keys |

**Criteria**: Loan fails when it does not meet any rule in the underwriting grid for its loan program (finance_type_name_nls), including balance vs approval_high, DTI vs dti_max, FICO vs fico_min, monthly income vs monthly_income_min; FICO > 700 allows waiver of income with PTI check.

---

## 3. CoMAP

| Notebook concept | App function | exception_type | rejection_criteria key |
|------------------|--------------|----------------|------------------------|
| Prime CoMAP (FICO bands, loan program in grid) | `rules.comap.check_comap_prime` | `comap_prime` | `notebook.comap_prime` |
| SFY CoMAP | `rules.comap.check_comap_sfy` | `comap_sfy` | `notebook.comap_sfy` |
| Notes CoMAP | `rules.comap.check_comap_notes` | `comap_notes` | `notebook.comap_notes` |

**Criteria**: Loan fails when (post purchase-price filter) it is not found in the appropriate CoMAP grid for its FICO band and loan program (and submit date for table selection).

---

## 4. Eligibility (portfolio-level; loan-level when applicable)

| Notebook concept | App function | exception_type | rejection_criteria key |
|------------------|--------------|----------------|------------------------|
| Prime eligibility checks (A, B, C, D, E, F, G, H, I, J, L, S) | `rules.eligibility.check_eligibility_prime` | — | `notebook.eligibility_prime` |
| SFY eligibility checks (L, etc.) | `rules.eligibility.check_eligibility_sfy` | — | `notebook.eligibility_sfy` |

**Criteria**: Portfolio-level pass/fail thresholds (e.g. % balance in certain buckets). Individual loans are not typically “rejected” by eligibility in the same way as purchase price/underwriting/CoMAP; when we flag loan-level eligibility, we use the above keys.

---

## 5. Disposition: To Purchase vs Projected vs Rejected

- **To purchase**: Loan is in the buy tape and passes **all** of: purchase price check, underwriting (SFY/Prime/notes as applicable), and CoMAP. Tracked as `disposition = to_purchase`.
- **Projected**: Loan is included in the pipeline run (in `final_df`) but not necessarily eligible to purchase; used for projection/analytics. Tracked as `disposition = projected`.
- **Rejected**: Loan failed at least one of purchase price, underwriting, or CoMAP. Tracked as `disposition = rejected` with `rejection_criteria` set to the **first** applicable notebook key above.

---

## 6. Day-of-Week Segregation

- **run_weekday**: Integer 0–6 (Monday = 0, Sunday = 6) derived from **pdate** (purchase date).
- **run_weekday_name**: String (e.g. `"Tuesday"`) for display.
- Activity (loans to purchase vs projected) is tracked **per run**; filter runs by `run_weekday` to get activity by day of week.

---

## 7. Summary Table: Rejection Reason → App Function

| Rejection reason | App module.function | rejection_criteria |
|------------------|---------------------|--------------------|
| Purchase price mismatch | rules.purchase_price.get_purchase_price_exceptions | notebook.purchase_price_mismatch |
| Underwriting (SFY) | rules.underwriting.check_underwriting + get_underwriting_exceptions | notebook.underwriting_sfy |
| Underwriting (Prime) | rules.underwriting.check_underwriting + get_underwriting_exceptions | notebook.underwriting_prime |
| Underwriting (Notes) | rules.underwriting.check_underwriting + get_underwriting_exceptions | notebook.underwriting_notes |
| CoMAP Prime | rules.comap.check_comap_prime | notebook.comap_prime |
| CoMAP SFY | rules.comap.check_comap_sfy | notebook.comap_sfy |
| CoMAP Notes | rules.comap.check_comap_notes | notebook.comap_notes |
| Eligibility Prime | rules.eligibility.check_eligibility_prime | notebook.eligibility_prime |
| Eligibility SFY | rules.eligibility.check_eligibility_sfy | notebook.eligibility_sfy |
