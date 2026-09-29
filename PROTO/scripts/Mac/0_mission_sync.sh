#!/bin/bash
cd "$(dirname "$0")"

# --- 🐳 VÉRIFICATION ET LANCEMENT DE DOCKER ---
echo "--- 🛠️ Vérification de l'état de Docker ---"

if ! docker info >/dev/null 2>&1; then
    echo "⚠️ Docker Desktop n'est pas lancé. Démarrage de l'application..."
    open -a Docker
    
    COUNT=0
    while ! docker info >/dev/null 2>&1; do
        echo "   ⏳ En attente du moteur Docker... ($COUNT s)"
        sleep 2
        ((COUNT+=2))
        if [ $COUNT -gt 60 ]; then
            echo "❌ Erreur : Docker prend trop de temps à démarrer."
            exit 1
        fi
    done
    echo "✅ Docker est maintenant opérationnel."
else
    echo "✅ Docker est déjà actif."
fi

# --- 🚀 LANCEMENT DU CONTENEUR ---
# On s'assure que le conteneur est allumé avant de continuer
CONTAINER_NAME="cave_explorer_m4" 

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        echo "📦 Démarrage du conteneur $CONTAINER_NAME..."
        docker start $CONTAINER_NAME
        sleep 2 
    fi
else
    echo "❌ Erreur : Le conteneur $CONTAINER_NAME n'existe pas."
    exit 1
fi

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
echo "1. Exécutez le script 'traiter_bag.command' pour générer les odométries individuelles."
echo "2. Exécutez le script '3_LancerPegar.command' pour assembler les segments traités."
echo "--------------------------------------------------------------------------------"