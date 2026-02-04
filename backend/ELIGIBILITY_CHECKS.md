# Eligibility Checks Implementation

## Overview

This document describes the complete eligibility checks implementation, matching all checks from the original notebook.

## Prime Eligibility Checks

### Check A: Term <= 144, Standard, FICO < 700

- **Description**: Percentage of non-repurchased Prime loans with Term <= 144, type = standard, FICO < 700
- **Threshold**: < 5%
- **Implementation**: `check_a`

### Check B: Term > 144, Standard, FICO < 700

- **Description**: Percentage of non-repurchased Prime loans with Term > 144, type = standard, FICO < 700
- **Threshold**: < 3% (balance-based)
- **Implementation**: `check_b1`
- **Check B3**: Count-based version (also < 3%)
- **Implementation**: `check_b3`

### Check C: Term > 144, Standard, FICO >= 700

- **Description**: Percentage of Prime loans with Term > 144, type = standard, FICO >= 700
- **Threshold**: < 35%
- **Implementation**: `check_c`

### Check D: Hybrid

- **Description**: Percentage of Prime loans with type = hybrid
- **Threshold**: < 35%
- **Implementation**: `check_d`

### Check E: NINP

- **Description**: Percentage of Prime loans with type = ninp
- **Threshold**: < 15%
- **Implementation**: `check_e`

### Check F: EPNI

- **Description**: Percentage of Prime loans with type = epni
- **Threshold**: < 18%
- **Implementation**: `check_f`

### Check G: WPDI

- **Description**: Percentage of Prime loans with type = wpdi
- **Threshold**: < 15%
- **Implementation**: `check_g`

### Check H: Lender Price

- **H1**: Maximum Lender Price(%)
  - **Threshold**: < 101.87
  - **Implementation**: `check_h1`
- **H2**: Percentage of loans with Lender Price 100-103%
  - **Threshold**: < 35%
  - **Implementation**: `check_h2`
- **H3**: Weighted average Dealer Fee
  - **Threshold**: < 15%
  - **Implementation**: `check_h3`

### Check I: Balance > $50,000

- **I1**: Percentage of loans with Orig. Balance > $50,000
  - **Threshold**: < 38%
  - **Implementation**: `check_i1`
- **I2**: Mean Orig. Balance
  - **Threshold**: < $20,000
  - **Implementation**: `check_i2`

### Check J: Property State Distribution

- **Description**: Distribution of loans by Property State (informational only)
- **Implementation**: `check_j_state_dist`
- **Note**: Not validated, stored for reference

### Check L: FICO Distribution

- **L1**: Percentage of loans with FICO < 680
  - **Threshold**: < 50%
  - **Implementation**: `check_l1`
- **L2**: Percentage of loans with FICO < 700
  - **Threshold**: < 70%
  - **Implementation**: `check_l2`
- **L3**: Weighted average FICO
  - **Threshold**: > 700
  - **Implementation**: `check_l3`
- **L4**: Mean FICO (informational)
  - **Implementation**: `check_l4`

### Check S: Special Assets (New Programs)

- **Description**: Percentage of non-repurchased Prime loans with new_programs = True
- **Threshold**: < 2%
- **Implementation**: `check_s1`

## SFY Eligibility Checks

### Check A: Hybrid

- **A1**: Percentage of SFY loans with type = hybrid
  - **Threshold**: < 85%
  - **Implementation**: `check_a1`
- **A2**: Percentage of SFY loans with type = hybrid and APR < 7.0
  - **Threshold**: < 25%
  - **Implementation**: `check_a2`

### Check B: NINP

- **B1**: Percentage of SFY loans with type = ninp
  - **Threshold**: < 30%
  - **Implementation**: `check_b1`
- **B2**: Percentage of SFY loans with type = ninp and promo_term > 6
  - **Threshold**: < 27%
  - **Implementation**: `check_b2`
- **B3**: Percentage of SFY loans with type = ninp and promo_term > 12
  - **Threshold**: < 15%
  - **Implementation**: `check_b3`
- **B4**: Percentage of SFY loans with type = ninp and Term > 84
  - **Threshold**: <= 0%
  - **Implementation**: `check_b4`

### Check C: EPNI

- **Description**: Percentage of SFY loans with type = epni
- **Threshold**: <= 25%
- **Implementation**: `check_c1`

### Check D: WPDI

- **D1**: Percentage of SFY loans with type = wpdi
  - **Threshold**: <= 17%
  - **Implementation**: `check_d1`
- **D2**: Percentage of SFY loans with type = wpdi or wpdi_bd
  - **Threshold**: <= 17%
  - **Implementation**: `check_d2`
- **D3**: Percentage of SFY loans with type = wpdi and promo_term >= 12
  - **Threshold**: <= 9%
  - **Implementation**: `check_d3`
- **D4**: Percentage of SFY loans with type = wpdi/wpdi_bd and promo_term >= 12
  - **Threshold**: <= 9%
  - **Implementation**: `check_d4`

### Check E: Standard Term > 120

- **E1**: Percentage of SFY loans with type = standard and Term > 120
  - **Threshold**: <= 30%
  - **Implementation**: `check_e1`
- **E2**: Percentage of SFY loans with type = standard/standard_bd and Term > 120
  - **Threshold**: <= 30%
  - **Implementation**: `check_e2`
- **E3**: Percentage of SFY loans with type = standard and Term > 144
  - **Threshold**: <= 28%
  - **Implementation**: `check_e3`
- **E4**: Percentage of SFY loans with type = standard/standard_bd and Term > 144
  - **Threshold**: <= 28%
  - **Implementation**: `check_e4`

### Check F: Lender Price

- **F1**: Maximum Lender Price(%)
  - **Threshold**: <= 101.21
  - **Implementation**: `check_f1`
- **F2**: Percentage of loans with Lender Price 100-103%
  - **Threshold**: <= 40%
  - **Implementation**: `check_f2`
- **F3**: Percentage of loans with Lender Price 100-103% (excluding "Unsec Std - 999 - 120")
  - **Threshold**: <= 37%
  - **Implementation**: `check_f3`
- **F4**: Weighted average Dealer Fee
  - **Threshold**: <= 15%
  - **Implementation**: `check_f4`

### Check G: Balance > $50,000

- **G1**: Percentage of loans with Orig. Balance > $50,000
  - **Threshold**: <= 38%
  - **Implementation**: `check_g1`
- **G2**: Mean Orig. Balance
  - **Threshold**: <= $20,000
  - **Implementation**: `check_g2`

### Check H: Property State Distribution

- **Description**: Distribution of loans by Property State (informational only)
- **Implementation**: `check_h_state_dist`
- **Note**: Not validated, stored for reference

### Check J: FICO Distribution

- **J1**: Percentage of loans with FICO < 680
  - **Threshold**: <= 50%
  - **Implementation**: `check_j1`
- **J2**: Percentage of loans with FICO < 700
  - **Threshold**: <= 70%
  - **Implementation**: `check_j2`
- **J3**: Weighted average FICO
  - **Threshold**: >= 700
  - **Implementation**: `check_j3`
- **J4**: Mean FICO
  - **Threshold**: >= 700
  - **Implementation**: `check_j4`

### Check L: BD Types

- **L1**: Percentage of SFY loans with type = wpdi_bd
  - **Threshold**: <= 1%
  - **Implementation**: `check_l1`
- **L2**: Percentage of SFY loans with type = standard_bd (informational)
  - **Implementation**: `check_l2`
- **L3**: Percentage of all loans (Prime + SFY) with type = standard_bd or wpdi_bd (informational)
  - **Implementation**: `check_l3`
- **L4**: Percentage of all loans (Prime + SFY) with type = standard_bd or wpdi_bd, excluding Excess_Asset (informational)
  - **Implementation**: `check_l4`
- **L5**: Percentage of new SFY loans (from buy_df) with type = standard_bd (informational)
  - **Implementation**: `check_l5`
  - **Note**: Requires `buy_df` parameter

### Check S: Special Assets (New Programs)

- **Description**: Percentage of non-repurchased SFY loans with new_programs = True
- **Threshold**: < 2%
- **Implementation**: `check_s1`

## Implementation Details

### Function Signatures

```python
def check_eligibility_prime(final_df_all: pd.DataFrame) -> Dict[str, Any]:
    """Run Prime eligibility checks."""
    # Returns dict with check results

def check_eligibility_sfy(
    final_df_all: pd.DataFrame,
    buy_df: pd.DataFrame = None
) -> Dict[str, Any]:
    """Run SFY eligibility checks."""
    # buy_df is optional, used for check_l5
    # Returns dict with check results
```

### Result Format

Each check returns a dictionary with:

```python
{
    'check_name': {
        'value': float,  # Calculated value
        'pass': bool     # True if passes threshold, False if fails, True for informational
    }
}
```

### Usage in Pipeline

```python
# In pipeline execution
eligibility_prime = check_eligibility_prime(final_df_all)
eligibility_sfy = check_eligibility_sfy(final_df_all, buy_df=buy_df)

# Results are stored in run record and exported to JSON/Excel
```

## Reporting

### JSON Export

Eligibility results are exported to `eligibility_checks.json` with formatted structure:

- Summary statistics (total checks, passed, failed, informational)
- Detailed check results with thresholds
- Platform-specific sections

### Excel Export

Eligibility summary is exported to `eligibility_checks_summary.xlsx` with:

- Platform (Prime/SFY)
- Check name
- Value
- Threshold
- Status (PASS/FAIL/INFO)

## Testing

All checks are tested in:

- `tests/test_rules_eligibility.py` - Individual check tests
- `tests/test_eligibility_complete.py` - Comprehensive notebook coverage tests

## Verification Checklist

### Prime Checks

- [x] Check A: Term <= 144, standard, FICO < 700
- [x] Check B1: Term > 144, standard, FICO < 700 (balance)
- [x] Check B3: Term > 144, standard, FICO < 700 (count)
- [x] Check C: Term > 144, standard, FICO >= 700
- [x] Check D: Hybrid
- [x] Check E: NINP
- [x] Check F: EPNI
- [x] Check G: WPDI
- [x] Check H1: Max Lender Price
- [x] Check H2: Lender Price 100-103%
- [x] Check H3: Dealer Fee
- [x] Check I1: Balance > $50k
- [x] Check I2: Mean Balance
- [x] Check J: Property State (informational)
- [x] Check L1: FICO < 680
- [x] Check L2: FICO < 700
- [x] Check L3: Weighted FICO
- [x] Check L4: Mean FICO (informational)
- [x] Check S1: New Programs

### SFY Checks

- [x] Check A1: Hybrid
- [x] Check A2: Hybrid with APR < 7.0
- [x] Check B1: NINP
- [x] Check B2: NINP promo_term > 6
- [x] Check B3: NINP promo_term > 12
- [x] Check B4: NINP Term > 84
- [x] Check C1: EPNI
- [x] Check D1: WPDI
- [x] Check D2: WPDI/WPDI_BD
- [x] Check D3: WPDI promo_term >= 12
- [x] Check D4: WPDI/WPDI_BD promo_term >= 12
- [x] Check E1: Standard Term > 120
- [x] Check E2: Standard/Standard_BD Term > 120
- [x] Check E3: Standard Term > 144
- [x] Check E4: Standard/Standard_BD Term > 144
- [x] Check F1: Max Lender Price
- [x] Check F2: Lender Price 100-103%
- [x] Check F3: Lender Price 100-103% (excl. specific program)
- [x] Check F4: Dealer Fee
- [x] Check G1: Balance > $50k
- [x] Check G2: Mean Balance
- [x] Check H: Property State (informational)
- [x] Check J1: FICO < 680
- [x] Check J2: FICO < 700
- [x] Check J3: Weighted FICO
- [x] Check J4: Mean FICO
- [x] Check L1: WPDI_BD
- [x] Check L2: Standard_BD (informational)
- [x] Check L3: BD types all (informational)
- [x] Check L4: BD types excl. Excess (informational)
- [x] Check L5: Standard_BD from buy_df (informational)
- [x] Check S1: New Programs

## Summary

All eligibility checks from the notebook are now implemented and tested:

- **Prime**: 19 checks (including informational)
- **SFY**: 30 checks (including informational)
- **Total**: 49 checks

All checks match the notebook logic and thresholds exactly.
