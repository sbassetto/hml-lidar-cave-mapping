#!/usr/bin/env bash
# HML-LiDAR RevA
# Lance l'éditeur MANUEL permettant de réviser les jonctions créées par Pegar.
#
# Optional:
#   HML_RESULTS_DIR
# Default:
#   ~/Desktop/Expedition_Data/results

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

echo "=== HML-LiDAR RevA : RÉVISION MANUELLE DU RÉSEAU PEGAR ==="
echo "Dossier de traitement : $HML_RESULTS_DIR"
echo

find_conda

if ! conda env list | awk '{print $1}' | grep -qx "hml_env"; then
    echo "ERREUR : l'environnement Conda 'hml_env' n'existe pas." >&2
    exit 1
fi

conda activate hml_env

python3 - <<'PY'
import importlib
for module in ("numpy", "scipy", "open3d", "rosbags", "flask"):
    importlib.import_module(module)
PY

test -f "$BASE_DIR/EditeurReseau.py" || {
    echo "ERREUR : EditeurReseau.py introuvable." >&2
    exit 1
}

test -f "$BASE_DIR/serveur_edition.py" || {
    echo "ERREUR : serveur_edition.py introuvable." >&2
    exit 1
}

python3 "$BASE_DIR/EditeurReseau.py"
status=$?

echo
if [ "$status" -eq 0 ]; then
    echo "Session de révision manuelle terminée."
else
    echo "L'éditeur s'est terminé avec le code $status." >&2
fi

read -r -p "Appuyez sur Entrée pour fermer cette fenêtre..."
exit "$status"
