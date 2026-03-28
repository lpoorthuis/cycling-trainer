#!/usr/bin/env python3
"""Filter virtual ride FIT files from a Strava bulk export."""

import shutil
import sys
from pathlib import Path

try:
    from fitparse import FitFile
except ImportError:
    print("Missing dependency. Install with: pip install fitparse")
    sys.exit(1)


def is_virtual_ride(fit_path: Path) -> bool:
    """Check if a FIT file is a virtual ride (e.g. Zwift)."""
    try:
        fit = FitFile(str(fit_path))
        for record in fit.get_messages("sport"):
            for field in record.fields:
                if field.name == "sub_sport" and field.value == "virtual_activity":
                    return True
                if field.name == "sport" and field.value == "cycling":
                    # Keep looking for sub_sport confirmation
                    continue
        # Also check session records as fallback
        for record in fit.get_messages("session"):
            for field in record.fields:
                if field.name == "sub_sport" and field.value == "virtual_activity":
                    return True
    except Exception as e:
        print(f"  Skipping {fit_path.name}: {e}")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_virtual_rides.py <strava_export_dir> [output_dir]")
        print()
        print("  strava_export_dir  Path to extracted Strava export (contains 'activities' folder)")
        print("  output_dir         Where to copy virtual rides (default: ./virtual_rides)")
        sys.exit(1)

    export_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./virtual_rides")

    # Strava exports have an 'activities' subfolder
    activities_dir = export_dir / "activities"
    if not activities_dir.exists():
        # Maybe they pointed directly at the activities folder
        activities_dir = export_dir

    fit_files = sorted(activities_dir.glob("*.fit")) + sorted(activities_dir.glob("*.FIT"))
    if not fit_files:
        print(f"No FIT files found in {activities_dir}")
        sys.exit(1)

    print(f"Scanning {len(fit_files)} FIT files...")
    output_dir.mkdir(parents=True, exist_ok=True)

    found = 0
    for i, fit_path in enumerate(fit_files, 1):
        print(f"  [{i}/{len(fit_files)}] {fit_path.name}...", end="", flush=True)
        if is_virtual_ride(fit_path):
            shutil.copy2(fit_path, output_dir / fit_path.name)
            found += 1
            print(" ✓ virtual ride")
        else:
            print(" skip")

    print(f"\nDone! {found} virtual rides copied to {output_dir}")


if __name__ == "__main__":
    main()
