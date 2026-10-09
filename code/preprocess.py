"""
Simple EEG file validator for testing the DataLad pipeline.
Automatically detects new files in data/raw/ and processes them.

Usage:
    python code/preprocess.py                    # Auto-detect and process all new files
    python code/preprocess.py --input ... --output ...  # Process single file
"""
import argparse
import json
import sys
from pathlib import Path
import mne

mne.set_log_level("WARNING")


def load_eeg(input_path: Path) -> mne.io.BaseRaw:
    """Load EEG file based on extension."""
    ext = input_path.suffix.lower()

    if ext == ".edf":
        raw = mne.io.read_raw_edf(str(input_path), preload=True, verbose=False)
    elif ext == ".fif":
        raw = mne.io.read_raw_fif(str(input_path), preload=True, verbose=False)
    elif ext == ".set":
        raw = mne.io.read_raw_eeglab(str(input_path), preload=True, verbose=False)
    else:
        print(f"[ERROR] Unsupported format: {ext}", file=sys.stderr)
        sys.exit(1)

    return raw


def get_output_path(input_path: Path) -> Path:
    """Convert data/raw/... path to data/processed/... path."""
    path_str = str(input_path)
    output_str = path_str.replace("data/raw", "data/processed")

    # Change extension to _eeg.fif
    for ext in ["_eeg.edf", "_eeg.fif", "_eeg.set", ".edf", ".fif", ".set"]:
        if output_str.endswith(ext):
            output_str = output_str.replace(ext, "_processed.fif")
            break

    return Path(output_str)


def process_file(input_path: Path, output_path: Path) -> bool:
    """Process a single EEG file. Returns True if successful."""
    try:
        print(f"\n[INFO] Processing {input_path}")

        if not input_path.exists():
            print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
            return False

        # Load and validate
        raw = load_eeg(input_path)
        n_channels = len(raw.ch_names)
        sfreq = raw.info["sfreq"]
        duration = raw.n_times / sfreq

        print(f"[INFO] {n_channels} channels | {sfreq} Hz | {duration:.1f}s")

        # Save copy (no actual processing - just demonstrates pipeline works)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw.save(str(output_path), overwrite=True, verbose=False)
        print(f"[OK] Processed file → {output_path}")

        # Simple success report
        report = {
            "input": str(input_path),
            "output": str(output_path),
            "status": "success",
            "n_channels": n_channels,
            "sfreq_hz": sfreq,
            "duration_s": round(duration, 2)
        }

        report_path = output_path.parent / output_path.name.replace(".fif", "_report.json")
        report_path.write_text(json.dumps(report, indent=2))
        print(f"[OK] Report → {report_path}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to process {input_path}: {e}", file=sys.stderr)
        return False


def find_and_process_new_files():
    """Find all raw EEG files and process those not yet processed."""
    raw_dir = Path("data/raw")

    if not raw_dir.exists():
        print("[INFO] No data/raw directory found, nothing to process")
        return

    # Find all EEG files
    patterns = ["**/*_eeg.fif", "**/*_eeg.edf", "**/*_eeg.set", "**/*.fif", "**/*.edf", "**/*.set"]
    all_files = []
    for pattern in patterns:
        all_files.extend(raw_dir.glob(pattern))

    # Remove duplicates and sort
    all_files = sorted(set(all_files))

    if not all_files:
        print("[INFO] No EEG files found in data/raw")
        return

    print(f"[INFO] Found {len(all_files)} EEG file(s) in data/raw")

    processed_count = 0
    skipped_count = 0

    for input_file in all_files:
        output_file = get_output_path(input_file)

        if output_file.exists():
            print(f"[SKIP] Already processed: {input_file.name}")
            skipped_count += 1
            continue

        if process_file(input_file, output_file):
            processed_count += 1

    print(f"\n[SUMMARY] Processed: {processed_count} | Skipped: {skipped_count}")


def main():
    parser = argparse.ArgumentParser(description="Simple EEG validator")
    parser.add_argument("--input",  help="Input EEG file (optional, auto-detects if not provided)")
    parser.add_argument("--output", help="Output EEG file (required if --input is provided)")
    args = parser.parse_args()

    # Single file mode
    if args.input:
        if not args.output:
            print("[ERROR] --output is required when --input is provided", file=sys.stderr)
            sys.exit(1)

        input_path = Path(args.input)
        output_path = Path(args.output)
        success = process_file(input_path, output_path)
        sys.exit(0 if success else 1)

    # Auto-detect mode
    else:
        find_and_process_new_files()


if __name__ == "__main__":
    main()
