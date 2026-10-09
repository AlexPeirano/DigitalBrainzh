"""
Simple EEG file validator for testing the DataLad pipeline.
Just checks file format and creates a processed copy - no real processing.

Usage:
    python code/preprocess.py \
        --input  data/raw/sub-01/ses-001/sub-01_ses-001_task-test_eeg.fif \
        --output data/processed/sub-01/ses-001/sub-01_ses-001_task-test_eeg_filtered.fif
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


def main():
    parser = argparse.ArgumentParser(description="Simple EEG validator")
    parser.add_argument("--input",  required=True, help="Input EEG file")
    parser.add_argument("--output", required=True, help="Output EEG file")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load and validate
    print(f"[INFO] Loading {input_path.name}")
    raw = load_eeg(input_path)

    n_channels = len(raw.ch_names)
    sfreq = raw.info["sfreq"]
    duration = raw.n_times / sfreq

    print(f"[INFO] {n_channels} channels | {sfreq} Hz | {duration:.1f}s")
    print(f"[OK] File format valid")

    # Save copy (no actual processing - just demonstrates pipeline works)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fif_path = output_path.parent / output_path.name.replace("_filtered.fif", "_eeg.fif")

    raw.save(str(fif_path), overwrite=True, verbose=False)
    print(f"[OK] Processed file → {fif_path}")

    # Simple success report
    report = {
        "input": str(input_path),
        "output": str(fif_path),
        "status": "success",
        "n_channels": n_channels,
        "sfreq_hz": sfreq,
        "duration_s": round(duration, 2)
    }

    report_path = fif_path.parent / fif_path.name.replace("_eeg.fif", "_report.json")
    report_path.write_text(json.dumps(report, indent=2))
    print(f"[OK] Report → {report_path}")


if __name__ == "__main__":
    main()
