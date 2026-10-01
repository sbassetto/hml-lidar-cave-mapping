#!/bin/bash
# Fichier : 2_traiter_bag.command
# Commande terminal pour le lancer et traiter un seul bag ou lancer l'interface graphique

echo "=== DÉMARRAGE DU SCRIPT DE TRAITEMENT ==="

# RevA reference container.
# The legacy field container can still be selected with:
# HML_CONTAINER_NAME=cave_explorer_m4 ./1_traiter_bag.command
CONTAINER_NAME="${HML_CONTAINER_NAME:-hml_lidar_reva}"

# Host-side acquisition directory
HML_DATA_ROOT="${HML_DATA_ROOT:-$HOME/Desktop/Expedition_Data}"
RAW_DIR="${HML_RAW_DIR:-$HML_DATA_ROOT/raw}"

# Runtime paths are selected after the container is started.
ROS_RESULTS_DIR="/root/ros2_ws/results"
SOFTWARE_SETUP=""
PARAMS_FILE=""

# --- DETECTION OF THE CONTAINER SOFTWARE LAYOUT ---
# RevA stores the compiled software stack inside /opt/hml_ws and mounts the
# published configuration read-only under /root/hml/config.
#
# The legacy field container mounts the complete ROS 2 workspace under
# /root/ros2_ws.

if docker exec "$CONTAINER_NAME" test -f /opt/hml_ws/install/setup.bash \
   && docker exec "$CONTAINER_NAME" test -f /root/hml/config/params.yaml; then

    SOFTWARE_SETUP="/opt/hml_ws/install/setup.bash"
    PARAMS_FILE="/root/hml/config/params.yaml"

    echo "RevA processing environment detected."
    echo "Software: $SOFTWARE_SETUP"
    echo "Parameters: $PARAMS_FILE"

elif docker exec "$CONTAINER_NAME" test -f /root/ros2_ws/install/setup.bash \
     && docker exec "$CONTAINER_NAME" test -f /root/ros2_ws/src/direct_lidar_inertial_odometry/cfg/params.yaml; then

    SOFTWARE_SETUP="/root/ros2_ws/install/setup.bash"
    PARAMS_FILE="/root/ros2_ws/src/direct_lidar_inertial_odometry/cfg/params.yaml"

    echo "Legacy field-processing environment detected."
    echo "Software: $SOFTWARE_SETUP"
    echo "Parameters: $PARAMS_FILE"

else
    echo "ERROR: Unable to identify a valid HML-LiDAR DLIO environment"
    echo "inside container: $CONTAINER_NAME"
    exit 1
fi

# Fonction d'orchestration isolée pour un segment unique avec blindage de fermeture
traiter_un_bag() {
    # Récupération du chemin absolu macOS soumis par l'interface ou la boucle
    local MAC_PATH="$1"
    local BAG_NAME=$(basename "$MAC_PATH")
    local DOCKER_BAG_PATH=""

    # Routage dynamique du chemin matériel vers le point de montage Docker
    if [[ "$MAC_PATH" == *"/raw/"* ]]; then
        local RELATIVE_PATH="${MAC_PATH##*/raw/}"
        DOCKER_BAG_PATH="/root/data/$RELATIVE_PATH"
    elif [[ "$MAC_PATH" == *"/ros2_ws/"* ]]; then
        local RELATIVE_PATH="${MAC_PATH##*/ros2_ws/}"
        DOCKER_BAG_PATH="/root/ros2_ws/$RELATIVE_PATH"
    else
        # Forçage de la racine de montage par défaut si l'arborescence est inconnue
        DOCKER_BAG_PATH="/root/data/$BAG_NAME"
    fi

    local OUTPUT_BAG_NAME="${BAG_NAME}_result"

    echo "--- Initialisation du traitement odométrique : $BAG_NAME ---"
    echo "Chemin Docker calculé : $DOCKER_BAG_PATH"

    # Purge systématique des processus ROS fantômes
    echo "Nettoyage des processus réseau résiduels dans le conteneur..."
    docker exec -it $CONTAINER_NAME pkill -9 -f ros > /dev/null 2>&1
    sleep 2

    # T1 : DLIO (Odométrie)
    osascript -e "tell application \"Terminal\"
        set t1 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T1\\\\a\\\\e]2;T1 : DLIO ODOM\\\\a\\\"; source /opt/ros/humble/setup.bash && source $ROS_WS/install/setup.bash && ros2 run direct_lidar_inertial_odometry dlio_odom_node --ros-args --params-file $ROS_WS/src/direct_lidar_inertial_odometry/cfg/params.yaml -p use_sim_time:=true --remap pointcloud:=/livox/lidar --remap imu:=/livox/imu'\"
        set custom title of t1 to \"T1 : DLIO ODOM\"
    end tell"

    # T3 : ROSBRIDGE (Serveur WebSocket)
    osascript -e "tell application \"Terminal\"
        set t3 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T3\\\\a\\\\e]2;T3 : BRIDGE\\\\a\\\"; source /opt/ros/humble/setup.bash && source $ROS_WS/install/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml'\"
        set custom title of t3 to \"T3 : BRIDGE\"
    end tell"

    # T5 : RECORD (Enregistrement pur des topics)
    osascript -e "tell application \"Terminal\"
        set t5 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T5\\\\a\\\\e]2;T5 : RECORD\\\\a\\\"; source /opt/ros/humble/setup.bash && source $ROS_WS/install/setup.bash && cd $ROS_WS/results && rm -rf $OUTPUT_BAG_NAME && echo 🔴 ENREGISTREMENT EN COURS... && ros2 bag record -a -o $OUTPUT_BAG_NAME --storage sqlite3'\"
        set custom title of t5 to \"T5 : RECORD\"
    end tell"

    # T2 : PLAY (Lecture de l'archive via le chemin interne calculé)
    osascript -e "tell application \"Terminal\"
        set t2 to do script \"docker exec -it $CONTAINER_NAME bash -ic 'printf \\\"\\\\e]1;T2\\\\a\\\\e]2;T2 : PLAY\\\\a\\\"; sleep 3 && source /opt/ros/humble/setup.bash && source $ROS_WS/install/setup.bash && ros2 bag play $DOCKER_BAG_PATH --clock -r 0.1 --delay 5'\"
        set custom title of t2 to \"T2 : PLAY\"
    end tell"

    echo ""
    echo "------------------------------------------------------------------"
    echo "⚠️  NE FERMEZ AUCUNE FENÊTRE MANUELLEMENT AVEC LA CROIX ROUGE."
    read -p "Appuyez sur Entrée ICI uniquement lorsque T2 a terminé sa lecture..."
    echo "------------------------------------------------------------------"
    
    echo "Clôture de la base de données et écriture des métadonnées en cours..."
    
    docker exec -it $CONTAINER_NAME pkill -INT -f "ros2 bag record"
    sleep 4
    docker exec -it $CONTAINER_NAME pkill -9 -f ros > /dev/null 2>&1
    osascript -e 'tell application "Terminal" to close (every window whose name contains "T1 :" or name contains "T2 :" or name contains "T3 :" or name contains "T5 :")' > /dev/null 2>&1
    
    echo "✅ Traitement achevé et sécurisé pour : $BAG_NAME."
}

# --- INTERFACE GRAPHIQUE ET BRANCHEMENT LOGIQUE ---
if [ -z "$1" ]; then
    CHOIX_GUI=$(osascript -e '
        tell application "System Events"
            activate
            try
                set dialogResult to display dialog "Sélectionnez le mode de traitement odométrique :" buttons {"Quitter", "Traiter dossier /raw", "Sélectionner une archive"} default button "Sélectionner une archive" cancel button "Quitter" with title "FALAISE-LiDAR : Interface de Traitement"
                return button returned of dialogResult
            on error
                return "Quitter"
            end try
        end tell
    ')

    if [ "$CHOIX_GUI" = "Traiter dossier /raw" ]; then
        echo "Mode lot sélectionné. Recherche automatique dans $RAW_DIR..."
        
        if [ ! -d "$RAW_DIR" ]; then
            echo "Erreur critique : Le sous-dossier /raw/ est introuvable dans $BASE_DIR."
            exit 1
        fi
        
        LISTE_BAGS=()
        for dossier in "$RAW_DIR"/*/; do
            if [ -d "$dossier" ]; then
                # Passage du chemin absolu intégral à la fonction
                LISTE_BAGS+=("$dossier")
            fi
        done
        
        if [ ${#LISTE_BAGS[@]} -eq 0 ]; then
            echo "Aucun sous-dossier détecté dans $RAW_DIR."
            exit 1
        fi
        
        echo "Nombre de segments détectés : ${#LISTE_BAGS[@]}"
        
        for chemin_bag in "${LISTE_BAGS[@]}"; do
            traiter_un_bag "$chemin_bag"
            echo ""
        done
        
        echo "Traitement par lot terminé pour l'ensemble des segments."

    elif [ "$CHOIX_GUI" = "Sélectionner une archive" ]; then
        DOSSIER_CIBLE=$(osascript -e '
            tell application "System Events"
                activate
                try
                    set leDossier to choose folder with prompt "Sélectionnez le dossier de votre archive ROS 2 à traiter :"
                    return POSIX path of leDossier
                on error
                    return ""
                end try
            end tell
        ')

        if [ -z "$DOSSIER_CIBLE" ]; then
            echo "Opération annulée par l'opérateur. Fermeture du script."
            exit 0
        fi
        
        # Nettoyage d'un éventuel slash terminal ajouté par AppleScript
        DOSSIER_CIBLE=${DOSSIER_CIBLE%/}
        echo "Archive sélectionnée via l'interface : $DOSSIER_CIBLE"
        traiter_un_bag "$DOSSIER_CIBLE"
    else
        echo "Interruption manuelle du script."
        exit 0
    fi
else
    # Nettoyage d'un éventuel slash terminal passé en argument
    ARGUMENT_NETTOYE=${1%/}
    traiter_un_bag "$ARGUMENT_NETTOYE"
fi