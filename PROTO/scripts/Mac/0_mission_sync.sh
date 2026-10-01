#!/bin/bash
cd "$(dirname "$0")"

# --- CONFIGURATION LOCALE (Mac) ---
RP_USER="samuel"
RP_HOST="chinook.local" 
RP_PATH="/home/samuel/Cave_explorer/data/cave_data/" 
LOCAL_BASE="/Users/samuel/desktop/Expedition_Data"
RAW_DIR="$LOCAL_BASE/raw"
RESULTS_DIR="$LOCAL_BASE/results"

mkdir -p "$RAW_DIR" "$RESULTS_DIR"

echo "--- 🛰️ Connexion à Chinook ($RP_HOST) ---"

# Transfert (Rsync vers le Mac)
rsync -avz --progress --rsync-path="sudo rsync" --remove-source-files "$RP_USER@$RP_HOST:$RP_PATH" "$RAW_DIR"

if [ $? -eq 0 ]; then
    echo "--- 🔓 Assurance des permissions Mac ---"
    sudo chown -R $(whoami) "$LOCAL_BASE"
    sudo chmod -R 755 "$LOCAL_BASE"
    find "$LOCAL_BASE" -type f -exec touch {} +

    echo "--- 🧹 Nettoyage des répertoires sur Chinook ($RP_HOST) ---"
    ssh "$RP_USER@$RP_HOST" "sudo rm -rf ${RP_PATH}*"
    echo "--- ✅ Transfert terminé. ---"
else
    echo "--- ⚠️ Rien à transférer. ---"
fi

# ==========================================
# 🏁 FIN DU PROCESSUS DE SYNCHRONISATION
# ==========================================

echo "--------------------------------------------------------------------------------"
echo "La synchronisation avec la plateforme Chinook est achevée."
echo "Les archives brutes (.db3) sont stockées dans : $RAW_DIR"
echo ""
echo "PROCÉDURE DE POST-TRAITEMENT MANUEL :"
echo "1. Exécutez le script '1_traiter_bag.command' pour générer les odométries individuelles."
echo "2. Exécutez le script '3_LancerPegar.command' pour assembler les segments traités."
echo "--------------------------------------------------------------------------------"