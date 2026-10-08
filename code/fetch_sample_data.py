"""
Télécharge un vrai fichier EEG public depuis PhysioNet (EEG Motor Movement/Imagery Dataset)
et le place dans la structure BIDS du projet.

Source : https://physionet.org/content/eegmmidb/1.0.0/
Format : .edf (European Data Format — standard EEG)
Taille  : ~400 Ko par fichier (parfait pour un prototype)

Usage:
    python code/fetch_sample_data.py --subject 01 --session 001 --task motor
"""
import argparse
import urllib.request
import urllib.error
from pathlib import Path
import sys


# URL de base du dataset PhysioNet EEG Motor Movement
PHYSIONET_BASE = "https://physionet.org/files/eegmmidb/1.0.0"

# Correspondance tâche → fichier PhysioNet
# Chaque sujet a des runs numérotés : run 1 = yeux ouverts, run 3 = tâche motrice, etc.
TASK_TO_RUN = {
    "rest":  1,   # yeux ouverts
    "motor": 3,   # tâche motrice imaginée (main gauche/droite)
    "mario": 3,   # on réutilise le run moteur pour simuler le jeu vidéo
    "music": 1,   # on réutilise le repos pour simuler l'écoute musicale
}


def download_file(url: str, dest: Path, verbose: bool = True) -> bool:
    """
    Télécharge un fichier depuis une URL vers dest.
    Retourne True si succès, False sinon.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        print(f"[INFO] Fichier déjà présent, téléchargement ignoré : {dest}")
        return True

    print(f"[INFO] Téléchargement depuis : {url}")
    print(f"[INFO] Destination           : {dest}")

    try:
        def progress_hook(block_count, block_size, total_size):
            if verbose and total_size > 0:
                pct = min(100, block_count * block_size * 100 // total_size)
                print(f"\r  Progression : {pct}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=progress_hook)
        print()  # saut de ligne après la progression
        print(f"[OK] Téléchargé ({dest.stat().st_size // 1024} Ko)")
        return True

    except urllib.error.HTTPError as e:
        print(f"\n[ERROR] HTTP {e.code} : {url}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Connexion impossible : {e.reason}", file=sys.stderr)
        return False


def write_metadata(session_dir: Path, base: str, subject: str, session: str, task: str, run: int):
    """Écrit un fichier de métadonnées JSON décrivant la session."""
    import json
    meta = {
        "subject": subject,
        "session": session,
        "task": task,
        "source": "PhysioNet EEG Motor Movement/Imagery Dataset",
        "source_url": f"{PHYSIONET_BASE}/S{int(subject):03d}/S{int(subject):03d}R{run:02d}.edf",
        "format": "EDF (European Data Format)",
        "sfreq_hz": 160,
        "n_channels": 64,
        "note": "Fichier de prototype — données publiques PhysioNet",
    }
    meta_path = session_dir / f"{base}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"[OK] Métadonnées → {meta_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Télécharge un fichier EEG public depuis PhysioNet"
    )
    parser.add_argument("--subject", default="01",
                        help="Identifiant sujet (01 à 09, default: 01)")
    parser.add_argument("--session", default="001",
                        help="Identifiant session (default: 001)")
    parser.add_argument("--task",    default="motor",
                        choices=list(TASK_TO_RUN.keys()),
                        help="Tâche expérimentale (default: motor)")
    parser.add_argument("--output-dir", default="data/raw",
                        help="Dossier racine de sortie (default: data/raw)")
    args = parser.parse_args()

    # Construction du chemin BIDS
    session_dir = (
        Path(args.output_dir)
        / f"sub-{args.subject}"
        / f"ses-{args.session}"
    )
    base = f"sub-{args.subject}_ses-{args.session}_task-{args.task}"
    eeg_dest = session_dir / f"{base}_eeg.edf"

    # URL PhysioNet correspondante
    run = TASK_TO_RUN[args.task]
    subj_num = int(args.subject)
    url = f"{PHYSIONET_BASE}/S{subj_num:03d}/S{subj_num:03d}R{run:02d}.edf"

    print(f"\n=== Fetch EEG : sub-{args.subject} | ses-{args.session} | task-{args.task} ===")
    success = download_file(url, eeg_dest)

    if not success:
        print("\n[ERROR] Téléchargement échoué.", file=sys.stderr)
        sys.exit(1)

    write_metadata(session_dir, base, args.subject, args.session, args.task, run)

    print(f"\n✅ Prêt. Fichier disponible dans :")
    print(f"   {session_dir}/")
    print(f"\nProchaine étape :")
    print(f"   datalad save -m \"data: EEG sub-{args.subject} ses-{args.session} task-{args.task}\"")


if __name__ == "__main__":
    main()
