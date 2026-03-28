#!/usr/bin/env python3
"""Filter a Strava bulk export to remove Hammerhead Karoo rides (already on Intervals.icu).

Keeps everything else: Zwift rides, strength sessions, walks, runs, etc.
"""

import gzip
import shutil
import sys
from pathlib import Path

try:
    from fitparse import FitFile
except ImportError:
    print("Missing dependency. Install with: uv add fitparse")
    sys.exit(1)


def is_hammerhead_activity(fit_path: Path) -> bool:
    """Check if a FIT file was recorded on a Hammerhead device."""
    try:
        # Handle .fit.gz files
        if fit_path.suffixes == [".fit", ".gz"]:
            with gzip.open(fit_path, "rb") as f:
                fit = FitFile(f.read())
        else:
            fit = FitFile(str(fit_path))

        for record in fit.get_messages("device_info"):
            for field in record.fields:
                if field.name == "manufacturer" and field.value == "hammerhead":
                    return True
                if field.name == "product_name" and isinstance(field.value, str) and "karoo" in field.value.lower():
                    return True
        # Also check file_id for manufacturer
        for record in fit.get_messages("file_id"):
            for field in record.fields:
                if field.name == "manufacturer" and field.value == "hammerhead":
                    return True
    except Exception as e:
        print(f"  Error reading {fit_path.name}: {e}")
    return False


def is_fit_file(path: Path) -> bool:
    return path.suffixes == [".fit", ".gz"] or path.suffix.lower() == ".fit"


def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_strava_export.py <strava_export_dir> [output_dir]")
        print()
        print("  strava_export_dir  Path to extracted Strava export (contains 'activities' folder)")
        print("  output_dir         Where to copy non-Karoo activities (default: ./upload_to_intervals)")
        sys.exit(1)

    export_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./upload_to_intervals")

    # Strava exports have an 'activities' subfolder
    activities_dir = export_dir / "activities"
    if not activities_dir.exists():
        activities_dir = export_dir

    # Grab all activity files
    activity_files = sorted(
        f for f in activities_dir.iterdir()
        if is_fit_file(f) or f.suffix.lower() in {".gpx", ".tcx"}
    )
    if not activity_files:
        print(f"No activity files found in {activities_dir}")
        sys.exit(1)

    print(f"Scanning {len(activity_files)} activity files...")
    output_dir.mkdir(parents=True, exist_ok=True)

    kept = 0
    skipped = 0
    for i, path in enumerate(activity_files, 1):
        print(f"  [{i}/{len(activity_files)}] {path.name}...", end="", flush=True)

        if is_fit_file(path) and is_hammerhead_activity(path):
            skipped += 1
            print(" ✗ Karoo ride (already on Intervals.icu)")
        else:
            shutil.copy2(path, output_dir / path.name)
            kept += 1
            print(" ✓ kept")

    print(f"\nDone! Kept {kept} activities, skipped {skipped} Karoo rides.")
    print(f"Upload the files in {output_dir} to Intervals.icu.")


if __name__ == "__main__":
    main()
