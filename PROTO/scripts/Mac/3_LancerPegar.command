#!/usr/bin/env bash
# HML-LiDAR RevA
# File: 3_LancerPegar.command
#
# Launch the manual multi-segment cave alignment tool on macOS.
#
# Optional environment variable:
#   HML_RESULTS_DIR   Processing directory containing DLIO outputs.
#                     Default: ~/Desktop/Expedition_Data/results

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

HML_RESULTS_DIR="${HML_RESULTS_DIR:-$HOME/Desktop/Expedition_Data/results}"
export HML_RESULTS_DIR

find_conda() {
    local candidates=(
        "$HOME/miniconda3/etc/profile.d/conda.sh"
        "$HOME/opt/anaconda3/etc/profile.d/conda.sh"
        "$HOME/anaconda3/etc/profile.d/conda.sh"
        "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh"
        "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
    )

    local f
    for f in "${candidates[@]}"; do
        if [ -f "$f" ]; then
            # shellcheck disable=SC1090
            source "$f"
            return 0
        fi
    done

    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        return 0
    fi

    echo "ERREUR : Conda/Miniforge est introuvable." >&2
    return 1
}

echo "=== HML-LiDAR RevA : Pegar ==="
echo "Dossier de traitement : $HML_RESULTS_DIR"
echo

find_conda

if ! conda env list | awk '{print $1}' | grep -qx "hml_env"; then
    echo "ERREUR : l'environnement Conda 'hml_env' n'existe pas." >&2
    exit 1
fi

echo "[1/3] Activation de hml_env..."
conda activate hml_env

echo "[2/3] Vérification des dépendances..."
python3 - <<'PY'
import importlib

required = {
    "numpy": "NumPy",
    "scipy": "SciPy",
    "open3d": "Open3D",
    "rosbags": "rosbags",
    "flask": "Flask",
    "PIL": "Pillow",
    "tkinter": "Tkinter",
}

missing = []
for module, label in required.items():
    try:
        importlib.import_module(module)
    except Exception as exc:
        missing.append(f"{label} ({module}): {exc}")

if missing:
    raise SystemExit(
        "Dépendances manquantes dans hml_env:\n  - " + "\n  - ".join(missing)
    )
PY

if [ ! -f "$BASE_DIR/Pegar.py" ]; then
    echo "ERREUR : Pegar.py est introuvable dans $BASE_DIR." >&2
    exit 1
fi

if [ ! -f "$BASE_DIR/serveur_alignement.py" ]; then
    echo "ERREUR : serveur_alignement.py est introuvable dans $BASE_DIR." >&2
    exit 1
fi

mkdir -p "$HML_RESULTS_DIR"

echo "[3/3] Lancement de Pegar..."
set +e
python3 "$BASE_DIR/Pegar.py"
status=$?
set -e

echo
if [ "$status" -eq 0 ]; then
    echo "Pegar terminé."
else
    echo "Pegar s'est terminé avec le code d'erreur $status." >&2
fi

read -r -p "Appuyez sur Entrée pour fermer cette fenêtre..."
exit "$status"
