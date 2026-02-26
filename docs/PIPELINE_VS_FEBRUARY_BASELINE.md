# API Pipeline vs February_Baseline Notebook – Rules Verification

This document verifies that all rules and checks in the **February_Baseline** notebook (`loan_engine/inputs/93rd_buy/bin/February_Baseline.py`) are run in the API pipeline and aligned where applicable.

## 1. Purchase Price

| Notebook | API | Status |
|----------|-----|--------|
| `existing_file['purchase_price_check'] = Lender Price(%) == round(modeled_purchase_price*100, 2)` | `check_purchase_price()` on existing/final not applied to `existing_file` alone; applied to `buy_df` and `final_df` | ✓ Same logic |
| `buy_df['purchase_price_check']` | `check_purchase_price(buy_df)` | ✓ |
| `final_df['purchase_price_check']` | `check_purchase_price(final_df)` | ✓ |
| Exceptions from mismatches | `get_purchase_price_exceptions(final_df)` → DB + reports | ✓ |

**Note:** Notebook applies check to `existing_file` first; pipeline applies to `buy_df` and `final_df` (which includes post-2025-10-01 existing). Logic is equivalent.

---

## 2. Underwriting

| Notebook | API | Status |
|----------|-----|--------|
| Regular loans: exclude HD NOTE, exclude tuloans and HD NOTE seller IDs | `check_underwriting(..., is_notes=False)`; `check_df = buy_df[Application Type != 'HD NOTE']`, skip if in tuloans | ✓ |
| Notes: Application Type == 'HD NOTE', exclude tuloans, prog = loan program replace 'notes' | `check_underwriting(..., is_notes=True)`; prog.replace('notes','') | ✓ |
| balance = Orig. Balance - Stamp fee | `balance = row['Orig. Balance'] - row.get('Stamp fee', 0)` | ✓ |
| filter_one by finance_type_name_nls, monthly_income_min, fico_min; meet_crit = any(balance ≤ approval_high and dti ≤ dti_max) | Same in `rules/underwriting.py` | ✓ |
| If not meet_crit and FICO > 700: try without income, with pti ≤ pti_ratio | Same | ✓ |
| loan_ids / loan_ids_notes → flagged | `flagged_loans_sfy`, `flagged_loans_prime`, `flagged_notes` → exceptions + export | ✓ |

All underwriting rules are run and aligned.

---

## 3. CoMAP

| Notebook | API | Status |
|----------|-----|--------|
| Prime: only loans with `purchase_price_check == True`, non–HD NOTE | Same filter in `check_comap_prime` | ✓ |
| Prime: **Submit Date > 2025-10-24** → oct25 or oct25_2 grids | Per-loan `Submit Date` in `check_comap_prime`; oct25 / oct25_2 used when `submit_dt > 2025-10-24` | ✓ |
| Prime: **2020-06-11 < Submit Date ≤ 2025-10-24** → prime_comap_new | `prime_comap_new` loaded; branch in `check_comap_prime` for `prime_new_cutoff < submit_dt <= oct25_cutoff` | ✓ |
| Prime: else → prime_comap | Else branch uses `prime_comap` | ✓ |
| SFY: Submit Date > 2025-10-24 → sfy_comap_oct25 or sfy_comap_oct25_2 | Per-loan Submit Date in `check_comap_sfy` | ✓ |
| SFY: else → sfy_comap or sfy_comap2 | Same | ✓ |
| Notes: notes_comap (FICO bands 680-749, 750-769, 770-789, 790+) | `check_comap_notes(buy_df, notes_comap)` | ✓ |
| Reference sheets | Pipeline loads: SFY/Prime COMAP, Notes CoMAP; SFY COMAP-Oct25, SFY COMAP-Oct25-2, Prime CoMAP-Oct25, Prime CoMAP-Oct25-2, Prime CoMAP - New (with fallback to base sheet if missing) | ✓ |

All CoMAP rules are run. Date logic uses each loan’s **Submit Date** (not run pdate) to match the notebook.

---

## 4. Eligibility – Prime

| Check | Notebook | API | Status |
|-------|----------|-----|--------|
| A | Term ≤144, standard, FICO <700 &lt; 0.05 | check_a &lt; 0.05 | ✓ |
| B1 | Term >144, standard, FICO <700 &lt; 0.03 | check_b1 &lt; 0.03 | ✓ |
| B3 | Count-based (term>144, standard, FICO<700) &lt; 0.03 | check_b3 &lt; 0.03 | ✓ |
| C | Term >144, standard, FICO ≥700 &lt; 0.35 | check_c &lt; 0.35 | ✓ |
| D | Hybrid &lt; 0.35 | check_d &lt; 0.35 | ✓ |
| E | NINP &lt; 0.15 | check_e &lt; 0.15 | ✓ |
| F | EPNI &lt; 0.18 | check_f &lt; 0.18 | ✓ |
| G | WPDI &lt; 0.15 | check_g &lt; 0.15 | ✓ |
| H1 | Max Lender Price ≤ 102 | check_h1 ≤ 102 | ✓ Aligned |
| H2 | Price 100–103 ratio &lt; 0.35 | check_h2 &lt; 0.35 | ✓ |
| H3 | Dealer fee (weighted) &lt; 0.15 | check_h3 &lt; 0.15 | ✓ |
| I1 | Balance >50k ratio &lt; 0.38 | check_i1 &lt; 0.38 | ✓ |
| I2 | Mean balance &lt; 20000 | check_i2 &lt; 20000 | ✓ |
| J | Property State distribution | check_j_state_dist (informational) | ✓ |
| L1 | FICO &lt; 680 ratio &lt; 0.5 | check_l1 &lt; 0.5 | ✓ |
| L2 | FICO &lt; 700 ratio &lt; 0.7 | check_l2 &lt; 0.7 | ✓ |
| L3 | Weighted avg FICO > 700 | check_l3 > 700 | ✓ |
| Special asset (s1) | new_programs, Repurchase=False, prime &lt; 0.02 | check_s1 &lt; 0.02 | ✓ |

---

## 5. Eligibility – SFY

| Check | Notebook | API | Status |
|-------|----------|-----|--------|
| A1 | Hybrid &lt; 0.85 | check_a1 &lt; 0.85 | ✓ |
| A2 | Hybrid, APR &lt; 7 &lt; 0.25 | check_a2 &lt; 0.25 | ✓ |
| B1–B4 | NINP ratios and term/promo_term | check_b1–b4 | ✓ |
| C1 | EPNI ≤ 0.25 | check_c1 ≤ 0.25 | ✓ |
| D1–D4 | WPDI / wpdi_bd, promo_term | check_d1–d4 | ✓ |
| E1–E4 | Standard term >120 / >144 | check_e1–e4 | ✓ |
| F1 | Max Lender Price ≤ 101.25 | check_f1 ≤ 101.25 | ✓ Aligned |
| F2–F4 | Price 100–103 ratio, dealer fee | check_f2–f4 | ✓ |
| G1–G2 | Balance >50k, mean balance | check_g1–g2 | ✓ |
| H | Property State distribution | check_h_state_dist (informational) | ✓ |
| J1–J4 | FICO bands and weighted/mean | check_j1–j4 | ✓ |
| L1–L5 | wpdi_bd, standard_bd, L5 from buy_df | check_l1–l5 | ✓ |
| Special asset (s1) | new_programs, Repurchase=False, sfy &lt; 0.02 | check_s1 &lt; 0.02 | ✓ |

---

## 6. Outputs

| Notebook | API | Status |
|----------|-----|--------|
| purchase_price_mismatch.xlsx | export_exception_reports → purchase_price_mismatch | ✓ |
| flagged_loans_{folderx}.xlsx | flagged_loans | ✓ |
| NOTES_flagged_loans_{folderx}.xlsx | notes_flagged_loans | ✓ |
| comap_not_passed.xlsx | comap_not_passed | ✓ |
| Share (first 30 cols) | output_share with same names | ✓ |
| special_asset_prime.xlsx | special_asset_prime.xlsx | ✓ |
| special_asset_sfy (notebook prints ratio; we export same filter) | special_asset_sfy.xlsx | ✓ |
| Eligibility (notebook prints only) | eligibility_checks.json, eligibility_checks_summary.xlsx | ✓ Exported as first-class outputs |

---

## 7. Data Loading and Prep

| Notebook | API | Status |
|----------|-----|--------|
| Tape20Loans_{yesterday}, SFY/PRIME exhibits, MASTER_SHEET, Underwriting_Grids_COMAP, current_assets | discover_input_files + load_reference_data; Tday/pdate drive dates | ✓ |
| TU144 drop, Platform, loan program + 'notes' for HD NOTE | normalize + pipeline concat/rename | ✓ |
| buy_df merge with df_loans_types (MASTER + Notes) | enrich_buy_df(buy_df, df_loans_types, pdate, irr_target) | ✓ |
| Repurchase from tape, existing_file Repurchase flag | mark_repurchased_loans; existing_file.loc[repurchased_loans, 'Repurchase'] = True | ✓ |
| final_df = buy + existing Purchase_Date > 2025-10-01; final_df_all = buy + all existing | Same in pipeline | ✓ |

---

## 8. Summary

- **Purchase price:** Logic and exceptions match; applied to buy_df and final_df.
- **Underwriting:** All four grids (SFY, Prime, SFY Notes, Prime Notes) run with same criteria and tuloans/HD NOTE handling.
- **CoMAP:** All three paths (Prime, SFY, Notes) run; Prime uses per-loan Submit Date and prime_comap_new for 2020-06-11 to 2025-10-24; Oct25 sheets loaded when present.
- **Eligibility:** All Prime and SFY checks run; thresholds aligned (H1 ≤ 102, F1 ≤ 101.25).
- **Outputs:** All notebook outputs are produced and exposed as first-class API outputs (including special_asset and eligibility).

**Reference:** `loan_engine/inputs/93rd_buy/bin/February_Baseline.py` (manual dates: last_end, yestarday, pdate).
