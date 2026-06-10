#!/bin/bash

# --- CONFIGURATION ---
# Le dossier où se trouvent tes scripts et tes résultats sur ton Mac (si tu as défini un autre chemin pour stocker sur ton ordinateur les données, il faut l'entrer dans BASEA_DIR
BASE_DIR="/Users/${USER}/Desktop/Expedition_Data/ros2_ws"
VTOPO_CONTAINER="vtopo_session"

echo "--- 🚀 Lancement du traitement post-expédition ---"

# 1. Vérifier si le container Visual Topo est lancé, sinon le démarrer
if [ ! "$(docker ps -q -f name=$VTOPO_CONTAINER)" ]; then
    echo "📦 Démarrage du container Visual Topo..."
    docker start $VTOPO_CONTAINER
    sleep 10 # On laisse le temps au serveur X11 de chauffer
fi

# 2. Trouver le dernier Bag enregistré pour l'automatisation
# On cherche le dossier le plus récent qui commence par 'cave_bag_'
LAST_BAG=$(ls -td $BASE_DIR/results/cave_bag_*/ 2>/dev/null | head -1)

if [ -z "$LAST_BAG" ]; then
    echo "❌ Erreur : Aucun dossier de bag trouvé dans $BASE_DIR/results"
else
    BAG_NAME=$(basename "$LAST_BAG")
    echo "🔄 Conversion du bag : $BAG_NAME"
    # Exécution du script Python sur le Mac
    python3 "$BASE_DIR/lidar_to_vtopo.py" "$BAG_NAME"
fi

# 3. Lancer Visual Topo à l'intérieur du Docker
echo "🖥️  Ouverture de Visual Topo dans l'interface NoVNC..."
docker exec -d $VTOPO_CONTAINER bash -c "wine /root/.wine/drive_c/Vtopo/vtopo.exe"

echo "✅ Terminé ! Tu peux ouvrir ton navigateur sur http://localhost:8080"

#==================================================
#Fait à Montréal, par Samuel BASSETTO, V2026-06-08
#==================================================
