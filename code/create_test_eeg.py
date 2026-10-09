"""
Creates a minimal dummy EEG file for testing the DataLad pipeline.
Simple and fast - just demonstrates the CI workflow works.

Usage:
    python code/create_test_eeg.py --subject 01 --session 001 --task test
"""
import argparse
from pathlib import Path
import numpy as np
import mne

mne.set_log_level("WARNING")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject",    default="01")
    parser.add_argument("--session",    default="001")
    parser.add_argument("--task",       default="test")
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()

    # Use absolute path from git root to avoid creating files in wrong location
    git_root = Path(__file__).parent.parent
    output_dir = git_root / args.output_dir
    session_dir = output_dir / f"sub-{args.subject}" / f"ses-{args.session}"
    session_dir.mkdir(parents=True, exist_ok=True)
    base = f"sub-{args.subject}_ses-{args.session}_task-{args.task}"

    # Create minimal EEG file: 4 channels, 10 seconds, random noise
    n_channels, sfreq, duration = 4, 100.0, 10.0
    n_samples = int(sfreq * duration)
    data = np.random.randn(n_channels, n_samples) * 1e-6

    ch_names = [f"EEG{i+1}" for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=["eeg"] * n_channels)
    raw = mne.io.RawArray(data, info, verbose=False)

    eeg_path = session_dir / f"{base}_eeg.fif"
    raw.save(str(eeg_path), overwrite=True, verbose=False)
    print(f"Test EEG file created at {eeg_path}")
    print(f"\nNext step:")
    print(f"   datalad save -m \"data: test EEG sub-{args.subject} ses-{args.session}\"")


if __name__ == "__main__":
    main()
