#!/usr/bin/env bash
# HML-LiDAR RevA
# Lance l'éditeur temporel ZUPT-like de récupération après divergence DLIO.

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
        "/usr/local/Caskroom/miniforge/base/etc/profile.d/conda.sh"
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

echo "=== HML-LiDAR RevA : RÉCUPÉRATION TEMPORELLE ZUPT-LIKE ==="
echo

find_conda

if ! conda env list | awk '{print $1}' | grep -qx "hml_env"; then
    echo "ERREUR : environnement Conda 'hml_env' introuvable." >&2
    exit 1
fi

conda activate hml_env

python3 - <<'PY'
import importlib
for module in ("numpy", "open3d", "rosbags", "flask"):
    importlib.import_module(module)
PY

if [ ! -f "$BASE_DIR/EditeurTemporel_ZUPT.py" ]; then
    echo "ERREUR : EditeurTemporel_ZUPT.py introuvable." >&2
    exit 1
fi

python3 "$BASE_DIR/EditeurTemporel_ZUPT.py"
status=$?

echo
if [ "$status" -eq 0 ]; then
    echo "Session ZUPT-like terminée."
else
    echo "L'éditeur s'est terminé avec le code $status." >&2
fi

read -r -p "Appuyez sur Entrée pour fermer..."
exit "$status"
