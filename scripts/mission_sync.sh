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
CONTAINER_NAME="cave_explorer_m4" # Vérifie que c'est bien le bon nom

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        echo "📦 Démarrage du conteneur $CONTAINER_NAME..."
        docker start $CONTAINER_NAME
        sleep 2 # Petit délai pour laisser les services internes démarrer
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

# --- CONFIGURATION DOCKER (Mis à jour pour cave_explorer_m4) ---
DOCKER_PATH="/root/data" 
ROS_WS="/root/ros2_ws"

mkdir -p "$RAW_DIR" "$RESULTS_DIR"

echo "--- 🛰️ Connexion à Chinook ($RP_HOST) ---"

# 1. Transfert (Rsync vers ton Mac)
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
# 🛠️ DÉTECTION DU DERNIER ENREGISTREMENT
# ==========================================

echo "--- 🚀 Analyse des dossiers téléchargés ---"

# On force le rafraîchissement du cache disque du Mac
sync

# On cherche spécifiquement un SOUS-DOSSIER dans RAW_DIR
# Cette commande exclut le dossier parent et prend le plus récent
LAST_BAG_NAME=$(ls -dt "$RAW_DIR"/*/ 2>/dev/null | head -1 | xargs basename)

# DEBUG VISUEL : Si c'est vide ici, ça ne marchera jamais dans le Terminal
echo "🔍 Debug variable LAST_BAG_NAME : [$LAST_BAG_NAME]"

if [ -z "$LAST_BAG_NAME" ] || [ "$LAST_BAG_NAME" == "raw" ]; then
    echo "❌ ERREUR : Aucun dossier de bag trouvé dans $RAW_DIR"
    exit 1
fi

DOCKER_BAG_PATH="/root/data/$LAST_BAG_NAME"
echo "🔥 Bag prêt pour lecture : $DOCKER_BAG_PATH"

# Création d'un nom de sortie basé sur le nom d'entrée
OUTPUT_BAG_NAME="${LAST_BAG_NAME}_result"
    
echo "🔥 Lancement AUTO pour le dernier enregistrement importé: $LAST_BAG_NAME"
echo "💾 Sauvegarde prévue dans : /root/ros2_ws/results/$OUTPUT_BAG_NAME"


# --- 🚀 LANCEMENT DES TERMINAUX DE TRAITEMENT T1 À T5 ---
echo "--- 🖥️ Ouverture et configuration des terminaux ---"

# T1 : DLIO (Odométrie) - Correction du deadlock via export manuel
osascript -e "tell application \"Terminal\"
    set t1 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T1\\\\a\\\\e]2;T1 : DLIO ODOM\\\\a\\\"; sleep 3 && source /opt/ros/humble/setup.bash && export AMENT_PREFIX_PATH=$ROS_WS/install/direct_lidar_inertial_odometry:\$AMENT_PREFIX_PATH && ros2 run direct_lidar_inertial_odometry dlio_odom_node --ros-args --params-file $ROS_WS/src/direct_lidar_inertial_odometry/cfg/params.yaml -p use_sim_time:=true --remap pointcloud:=/livox/lidar --remap imu:=/livox/imu'\"
    set custom title of t1 to \"T1 : DLIO ODOM\"
end tell"

# --- 🚀 LANCEMENT DES TERMINAUX ---
# T2 Corrigé avec la variable vérifiée
osascript -e "tell application \"Terminal\"
    set t2 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T2\\\\a\\\\e]2;T2 : PLAY\\\\a\\\"; source /opt/ros/humble/setup.bash && ros2 bag play $DOCKER_BAG_PATH --clock -r 0.1'\"
    set custom title of t2 to \"T2 : PLAY\"
end tell"

# T3 : ROSBRIDGE (Lien vers la visualisation)
osascript -e "tell application \"Terminal\"
    set t3 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T3\\\\a\\\\e]2;T3 : BRIDGE\\\\a\\\"; source /opt/ros/humble/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml'\"
    set custom title of t3 to \"T3 : BRIDGE\"
end tell"

# T4 : DEBUG (Terminal libre pour maintenance)
osascript -e "tell application \"Terminal\"
    set t4 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T4\\\\a\\\\e]2;T4 : DEBUG\\\\a\\\"; cd $ROS_WS; bash'\"
    set custom title of t4 to \"T4 : DEBUG\"
end tell"

# T5 : RECORD & VTOPO (On passe l'argument au script Python)
osascript -e "tell application \"Terminal\"
    set t5 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T5\\\\a\\\\e]2;T5 : RECORD\\\\a\\\"; source /opt/ros/humble/setup.bash && cd $ROS_WS/results && echo 🔴 ENREGISTREMENT EN COURS... && ros2 bag record -a -o ${LAST_BAG_NAME}_result --storage sqlite3; echo --- 🏁 Fin de l enregistrement, lancement de lidar_to_vtopo.py ---; python3 lidar_to_vtopo.py ${LAST_BAG_NAME}_result'\"
    set custom title of t5 to \"T5 : RECORD & VTOPO\"
end tell"

echo "✅ Tout est lancé. Surveille T2 pour la lecture et T5 pour la fin du traitement."


    echo "--- ✅ Tout est lancé. ---"
    echo "💡 Le nuage nettoyé par DLIO est enregistré sur le topic /kf_cloud."
fi

echo "------------------------------------------"
echo "on vient de lancer les scripts pour le dernier téléchargement. Pour les autres éventuels, ouvrir le fichier readme.md pour les commandes a appliquer, sinon, prendre connaissance des commandes du mémento ci dessous. 
echo "------------------------------------------"

# ==========================================
# 📚 RÉCAPITULATIF & COMMANDES DE DIAGNOSTIC
# ==========================================
    
echo "-----------------------------------------------------"
echo "---          📋 MÉMENTO DES COMMANDES             ---"
echo "-----------------------------------------------------"   
echo ""
echo "🛰️  CONNEXION CHINOOK :"
echo "   ssh $RP_USER@$RP_HOST Password: chinook"
echo ""
echo "🐳 DOCKER :"
echo "   Statut : docker ps -a | grep $CONTAINER_NAME"
echo "   Espace : docker exec -it $CONTAINER_NAME df -h /root"
echo ""
echo "🤖 VÉRIFICATION ROS 2 (Directement depuis le Mac) :"
echo "   Topics actifs : docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic list'"
echo "   Fréquence LiDAR: docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic hz /livox/lidar'"
echo "   Fréquence Odom : docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic hz /odom'"
echo ""
echo "📍 ÉTAT DLIO :"
echo "   Position (XYZ): docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 topic echo /odom --once'"
echo "   Tuer ROS      : docker exec -it $CONTAINER_NAME pkill -9 -f ros"
echo ""
echo "📍 DIAGNOSTIC CAVE EXPLORER :"
echo "   Vérifier inclinaison : ros2 topic echo /odom --once"
echo "   (Si Z bouge alors que le casque est au sol, la gravité est mal calibrée)"
echo "-----------------------------------------------------"
echo ""
echo "🧹 NETTOYAGE CHINOOK :"
echo "   Vider les données : ssh $RP_USER@$RP_HOST 'sudo rm -rf ${RP_PATH}*'"
echo ""
echo "------------------------------------------------"
echo "📂 REJOUER UN AUTRE ENREGISTREMENT :"
for folder in "$RAW_DIR"/*/; do
    [ -e "$folder" ] || continue
    BN=$(basename "$folder")
    if [ "$BN" != "$LAST_BAG_NAME" ]; then  
        echo "   -> $BN :"
        echo "      docker exec -it $CONTAINER_NAME bash -ic 'source /opt/ros/humble/setup.bash && ros2 bag play $DOCKER_PATH/$BN --clock -r 0.05 --loop'"
    fi
done
echo "------------------------------------------------"
