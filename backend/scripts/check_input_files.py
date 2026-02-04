"""Check if required input files exist and list what's available."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.date_utils import calculate_yesterday, calculate_last_month_end
from utils.file_discovery import discover_input_files
from config.settings import settings


def check_input_files(folder: str = None):
    """Check input files and report what's missing."""
    if folder is None:
        folder = settings.INPUT_DIR
    
    folder_path = Path(folder)
    files_required_dir = folder_path / "files_required"
    
    print(f"Checking input files in: {folder}")
    print(f"Expected directory: {files_required_dir}")
    print()
    
    # Check if directory exists
    if not files_required_dir.exists():
        print(f"❌ Directory does not exist: {files_required_dir}")
        print(f"\nCreate it with:")
        print(f"  mkdir \"{files_required_dir}\"")
        return
    
    print(f"✅ Directory exists: {files_required_dir}")
    print()
    
    # List all files in directory
    all_files = list(files_required_dir.iterdir())
    if all_files:
        print(f"Files found in directory ({len(all_files)} total):")
        for f in sorted(all_files):
            if f.is_file():
                size = f.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                print(f"  - {f.name} ({size_str})")
        print()
    else:
        print("⚠️  Directory is empty")
        print()
    
    # Check for required files
    yesterday = calculate_yesterday()
    last_end = calculate_last_month_end()
    
    print("Checking required files:")
    print(f"  Date used: {yesterday} (yesterday)")
    print()
    
    required_files = {
        f"Tape20Loans_{yesterday}.csv": "Tape20Loans file (required)",
        "MASTER_SHEET.xlsx": "Master sheet (required)",
        "MASTER_SHEET - Notes.xlsx": "Master sheet notes (required)",
        "current_assets.csv": "Current assets (required)",
        "Underwriting_Grids_COMAP.xlsx": "Underwriting grids (required)",
    }
    
    optional_files = {
        f"FX3_{last_end}.xlsx": "FX3 file (optional)",
        f"FX4_{last_end}.xlsx": "FX4 file (optional)",
    }
    
    missing_required = []
    found_required = []
    
    for filename, description in required_files.items():
        file_path = files_required_dir / filename
        if file_path.exists():
            print(f"  ✅ {filename} - {description}")
            found_required.append(filename)
        else:
            print(f"  ❌ {filename} - {description} - MISSING")
            missing_required.append(filename)
    
    print()
    print("Optional files:")
    for filename, description in optional_files.items():
        file_path = files_required_dir / filename
        if file_path.exists():
            print(f"  ✅ {filename} - {description}")
        else:
            print(f"  ⚠️  {filename} - {description} - Not found (optional)")
    
    print()
    
    # Check for SFY and PRIME files (pattern matching)
    sfy_files = list(files_required_dir.glob("SFY_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"))
    prime_files = list(files_required_dir.glob("PRIME_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"))
    
    print("SFY and PRIME files:")
    if sfy_files:
        print(f"  ✅ Found {len(sfy_files)} SFY file(s):")
        for f in sfy_files:
            print(f"     - {f.name}")
    else:
        print(f"  ❌ No SFY files found (pattern: SFY_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx)")
    
    if prime_files:
        print(f"  ✅ Found {len(prime_files)} PRIME file(s):")
        for f in prime_files:
            print(f"     - {f.name}")
    else:
        print(f"  ❌ No PRIME files found (pattern: PRIME_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx)")
    
    print()
    
    # Summary
    if missing_required:
        print("❌ MISSING REQUIRED FILES:")
        for f in missing_required:
            print(f"   - {f}")
        print()
        print("The pipeline will fail without these files.")
    elif not sfy_files or not prime_files:
        print("⚠️  Missing SFY or PRIME files - pipeline will fail")
    else:
        print("✅ All required files found!")
    
    print()
    print("For more information, see: backend/docs/FILE_STRUCTURE.md")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check input files for pipeline")
    parser.add_argument(
        "--folder",
        type=str,
        default=None,
        help="Input folder path (default: from settings.INPUT_DIR)"
    )
    
    args = parser.parse_args()
    
    check_input_files(args.folder)
