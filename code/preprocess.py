"""
Prétraitement EEG minimal avec MNE-Python.

Étapes :
  1. Lecture du fichier .edf brut
  2. Filtre passe-bande 1-40 Hz (supprime dérive lente + bruit haute fréquence)
  3. Référence moyenne (recadre le signal par rapport à la moyenne de tous les canaux)
  4. Détection des canaux bruyants (amplitude anormale)
  5. Sauvegarde en .fif (format natif MNE)
  6. Rapport qualité JSON

Usage:
    python code/preprocess.py \
        --input  data/raw/sub-01/ses-001/sub-01_ses-001_task-motor_eeg.edf \
        --output data/processed/sub-01/ses-001/sub-01_ses-001_task-motor_eeg_filtered.fif
"""
import argparse
import json
import sys
from pathlib import Path

import mne
import numpy as np

# Désactive les logs verbeux de MNE pour garder une sortie lisible
mne.set_log_level("WARNING")


def load_eeg(input_path: Path) -> mne.io.BaseRaw:
    """Charge le fichier EEG selon son extension."""
    ext = input_path.suffix.lower()

    if ext == ".edf":
        raw = mne.io.read_raw_edf(str(input_path), preload=True, verbose=False)
    elif ext == ".fif":
        raw = mne.io.read_raw_fif(str(input_path), preload=True, verbose=False)
    elif ext == ".set":
        raw = mne.io.read_raw_eeglab(str(input_path), preload=True, verbose=False)
    else:
        print(f"[ERROR] Format non supporté : {ext}", file=sys.stderr)
        sys.exit(1)

    return raw


def detect_bad_channels(raw: mne.io.BaseRaw, z_threshold: float = 3.0) -> list[str]:
    """
    Détecte les canaux dont l'amplitude est anormale (z-score > seuil).
    Un canal est 'bad' s'il est trop bruité ou trop plat.
    """
    data = raw.get_data()  # shape: (n_channels, n_samples)
    channel_std = np.std(data, axis=1)

    # Z-score des écarts-types inter-canaux
    mean_std = np.mean(channel_std)
    std_std  = np.std(channel_std)

    if std_std == 0:
        return []

    z_scores = np.abs((channel_std - mean_std) / std_std)
    bad_idx  = np.where(z_scores > z_threshold)[0]

    return [raw.ch_names[i] for i in bad_idx]


def main():
    parser = argparse.ArgumentParser(
        description="Prétraitement EEG minimal (filtre + rapport qualité)"
    )
    parser.add_argument("--input",      required=True,
                        help="Fichier EEG brut (.edf, .fif, .set)")
    parser.add_argument("--output",     required=True,
                        help="Fichier EEG traité (.fif)")
    parser.add_argument("--l-freq",     type=float, default=1.0,
                        help="Fréquence de coupure basse en Hz (default: 1.0)")
    parser.add_argument("--h-freq",     type=float, default=40.0,
                        help="Fréquence de coupure haute en Hz (default: 40.0)")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    # ── Validation ──────────────────────────────────────────────────────────
    if not input_path.exists():
        print(f"[ERROR] Fichier introuvable : {input_path}", file=sys.stderr)
        sys.exit(1)

    # ── Chargement ──────────────────────────────────────────────────────────
    print(f"[INFO] Chargement de {input_path.name} ...")
    raw = load_eeg(input_path)

    n_channels = len(raw.ch_names)
    n_samples  = raw.n_times
    sfreq      = raw.info["sfreq"]
    duration_s = n_samples / sfreq

    print(f"[INFO] {n_channels} canaux | {sfreq} Hz | {duration_s:.1f}s")

    # ── Détection canaux mauvais ─────────────────────────────────────────────
    bad_channels = detect_bad_channels(raw)
    if bad_channels:
        raw.info["bads"] = bad_channels
        print(f"[WARN] Canaux détectés mauvais : {bad_channels}")
    else:
        print("[INFO] Aucun canal mauvais détecté")

    # ── Filtre passe-bande ───────────────────────────────────────────────────
    print(f"[INFO] Filtrage passe-bande {args.l_freq}-{args.h_freq} Hz ...")
    raw.filter(
        l_freq=args.l_freq,
        h_freq=args.h_freq,
        method="fir",
        verbose=False,
    )

    # ── Référence moyenne ────────────────────────────────────────────────────
    print("[INFO] Application de la référence moyenne ...")
    raw.set_eeg_reference("average", projection=False, verbose=False)

    # ── Sauvegarde ───────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # MNE exige que le fichier .fif se termine par _raw.fif ou _filtered.fif
    if not str(output_path).endswith(("_raw.fif", "_filtered.fif", "-raw.fif")):
        output_path = output_path.with_name(
            output_path.stem.replace("_filtered", "") + "_filtered.fif"
        )

    raw.save(str(output_path), overwrite=True, verbose=False)
    print(f"[OK] Signal traité → {output_path}")

    # ── Rapport qualité ──────────────────────────────────────────────────────
    data_filtered = raw.get_data()
    report = {
        "input":   str(input_path),
        "output":  str(output_path),
        "status":  "success",
        "metrics": {
            "n_channels":       n_channels,
            "n_samples":        n_samples,
            "sfreq_hz":         sfreq,
            "duration_s":       round(duration_s, 2),
            "bad_channels":     bad_channels,
            "n_bad_channels":   len(bad_channels),
            "filter_l_freq_hz": args.l_freq,
            "filter_h_freq_hz": args.h_freq,
            "amplitude_mean_uv": round(float(np.mean(np.abs(data_filtered)) * 1e6), 4),
            "quality":          "good" if len(bad_channels) < n_channels * 0.2 else "poor",
        },
    }

    report_path = output_path.parent / (
        output_path.name
        .replace("_eeg_filtered.fif", "_report.json")
        .replace("_filtered.fif",     "_report.json")
    )
    report_path.write_text(json.dumps(report, indent=2))
    print(f"[OK] Rapport qualité → {report_path}")
    print(f"[OK] Qualité : {report['metrics']['quality'].upper()} "
          f"({len(bad_channels)} canaux mauvais / {n_channels})")


if __name__ == "__main__":
    main()
