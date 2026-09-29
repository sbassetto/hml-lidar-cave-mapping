#!/bin/bash
# Fichier : LancerPegar.command

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/opt/anaconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" ]; then
    source "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh"
else
    eval "$(conda shell.bash hook)"
fi

echo "[1/3] Moteur d'environnement sourcé. Activation de hml_env en cours (Conda)..."
conda activate hml_env

echo "[2/3] Environnement activé. Chargement des modules lourds (Open3D) et exécution..."
python3 Pegar.py

echo "[3/3] Processus terminé."
read -p "Appuyez sur Entrée pour fermer cette fenêtre..."