"""
Crée un fichier EEG de test minimal et valide (.fif) avec MNE-Python.
Pas de téléchargement — fichier généré localement en quelques secondes.

Usage:
    python code/create_test_eeg.py --subject 01 --session 001 --task mario
"""
import argparse
import json
from pathlib import Path
import numpy as np
import mne

mne.set_log_level("WARNING")


def create_test_raw(n_channels: int = 32, sfreq: float = 250.0, duration_s: float = 60.0) -> mne.io.RawArray:
    """Crée un objet Raw MNE avec un signal EEG synthétique réaliste."""
    rng = np.random.default_rng(42)
    n_samples = int(sfreq * duration_s)
    t = np.linspace(0, duration_s, n_samples)

    data = rng.normal(0, 10e-6, (n_channels, n_samples))      # bruit ~10µV
    data += 15e-6 * np.sin(2 * np.pi * 10 * t)                # oscillations alpha
    data[:4] += 80e-6 * (rng.random((4, n_samples)) > 0.995)  # clignements frontaux

    ch_names = [f"EEG{i+1:03d}" for i in range(n_channels)]
    ch_types = ["eeg"] * n_channels
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    info.set_montage("colin27_1020", on_missing="ignore")

    return mne.io.RawArray(data, info, verbose=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject",    default="01")
    parser.add_argument("--session",    default="001")
    parser.add_argument("--task",       default="mario")
    parser.add_argument("--duration",   type=float, default=60.0)
    parser.add_argument("--sfreq",      type=float, default=250.0)
    parser.add_argument("--channels",   type=int,   default=32)
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()

    session_dir = Path(args.output_dir) / f"sub-{args.subject}" / f"ses-{args.session}"
    session_dir.mkdir(parents=True, exist_ok=True)
    base = f"sub-{args.subject}_ses-{args.session}_task-{args.task}"

    # Créer le fichier .fif
    raw = create_test_raw(args.channels, args.sfreq, args.duration)
    eeg_path = session_dir / f"{base}_eeg_raw.fif"
    raw.save(str(eeg_path), overwrite=True, verbose=False)
    print(f"[OK] Fichier EEG test → {eeg_path}  ({eeg_path.stat().st_size // 1024} Ko)")

    # Métadonnées
    meta = {
        "subject": args.subject, "session": args.session, "task": args.task,
        "sfreq_hz": args.sfreq, "n_channels": args.channels,
        "duration_s": args.duration, "format": "fif (MNE synthetic)",
    }
    (session_dir / f"{base}_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[OK] Métadonnées    → {session_dir}/{base}_meta.json")
    print(f"\nProchaine étape :")
    print(f"   datalad save -m \"data: EEG test sub-{args.subject} ses-{args.session}\"")


if __name__ == "__main__":
    main()
