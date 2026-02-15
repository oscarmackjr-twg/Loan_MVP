# Input File Structure Guide

This document explains the expected directory structure and file naming conventions for pipeline input files.

## Directory Structure

The pipeline expects input files in a `files_required/` subdirectory:

```
your_input_folder/
├── files_required/
│   ├── Tape20Loans_MM-DD-YYYY.csv          (Required)
│   ├── SFY_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx  (Required)
│   ├── PRIME_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx  (Required)
│   ├── MASTER_SHEET.xlsx                   (Required)
│   ├── MASTER_SHEET - Notes.xlsx           (Required)
│   ├── current_assets.csv                  (Required)
│   ├── Underwriting_Grids_COMAP.xlsx        (Required)
│   ├── FX3_YYYY_MMM_DD.xlsx                (Optional)
│   └── FX4_YYYY_MMM_DD.xlsx                (Optional)
```

## File Naming Conventions

### Tape20Loans File (Required)

**Pattern**: `Tape20Loans_MM-DD-YYYY.csv`

**Example**: `Tape20Loans_01-22-2026.csv`

**Date**: Uses **yesterday's date** (MM-DD-YYYY format)

**Location**: `{input_folder}/files_required/Tape20Loans_MM-DD-YYYY.csv`

### SFY Exhibit File (Required)

**Pattern**: `SFY_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

**Example**: `SFY_01-22-2026_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

**Date**: Uses the date from the SFY file (usually same as Tape20Loans or most recent)

**Location**: `{input_folder}/files_required/SFY_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

### PRIME Exhibit File (Required)

**Pattern**: `PRIME_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

**Example**: `PRIME_01-22-2026_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

**Date**: Uses the date from the PRIME file (usually same as Tape20Loans or most recent)

**Location**: `{input_folder}/files_required/PRIME_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx`

### Reference Files (Required)

These files should be in `files_required/` and don't use date patterns:

- `MASTER_SHEET.xlsx`
- `MASTER_SHEET - Notes.xlsx`
- `current_assets.csv`
- `Underwriting_Grids_COMAP.xlsx`

### FX Files (Optional)

**Pattern**: `FX{number}_YYYY_MMM_DD.xlsx`

**Example**: `FX3_2025_010_31.xlsx` (for January 31, 2025)

**Date**: Last day of previous month (YYYY_MMM_DD format)

**Location**: `{input_folder}/files_required/FX3_YYYY_MMM_DD.xlsx`

## Date Calculation

The pipeline automatically calculates dates:

- **Tape20Loans**: Uses **yesterday's date** (MM-DD-YYYY)
- **SFY/PRIME**: Auto-discovers most recent file if date not specified
- **FX files**: Uses last day of previous month (YYYY_MMM_DD)

## Example Setup

For a run on January 23, 2026:

```
C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy/
└── files_required/
    ├── Tape20Loans_01-22-2026.csv
    ├── SFY_01-22-2026_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx
    ├── PRIME_01-22-2026_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx
    ├── MASTER_SHEET.xlsx
    ├── MASTER_SHEET - Notes.xlsx
    ├── current_assets.csv
    └── Underwriting_Grids_COMAP.xlsx
```

## Troubleshooting

### "No file found matching pattern"

**Error**: `No file found matching pattern 'Tape20Loans_01-22-2026.csv'`

**Solutions**:

1. **Check file exists**: Verify the file is in `{folder}/files_required/`

2. **Check date format**: File must use MM-DD-YYYY format
   - ✅ Correct: `Tape20Loans_01-22-2026.csv`
   - ❌ Wrong: `Tape20Loans_2026-01-22.csv`
   - ❌ Wrong: `Tape20Loans_1-22-2026.csv`

3. **Check directory structure**: Ensure `files_required/` subdirectory exists

4. **Use correct date**: The pipeline looks for **yesterday's date** by default
   - If today is Jan 23, it looks for Jan 22 files
   - If you need a different date, specify `pdate` parameter

5. **List available files**: The error message now shows available files in the directory

### "Directory not found"

**Error**: `Directory not found: C:/path/to/files_required`

**Solution**: Create the `files_required` subdirectory:
```bash
mkdir "C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy/files_required"
```

## Run archive

After each successful pipeline run, input and output files are copied to the archive area (configurable via `ARCHIVE_DIR`, default `./data/archive`). Layout:

```
{ARCHIVE_DIR}/
├── {run_id}/
│   ├── input/    ← copies of input files used for this run
│   │   ├── Tape20Loans_MM-DD-YYYY.csv
│   │   ├── MASTER_SHEET.xlsx
│   │   └── ...
│   └── output/   ← outputs produced for this run
│       ├── purchase_price_mismatch.xlsx
│       ├── flagged_loans.xlsx
│       ├── eligibility_checks.json
│       └── ...
```

With S3 storage, the same structure is used under the `archive` prefix in the bucket.

## Sales Team Isolation

If using sales team isolation, files should be in:

```
{base_input_dir}/sales_team_{id}/files_required/
```

Example:
```
data/inputs/sales_team_1/files_required/Tape20Loans_01-22-2026.csv
```
