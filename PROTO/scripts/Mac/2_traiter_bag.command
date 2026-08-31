#!/usr/bin/env bash
# HML-LiDAR RevA
# File: 2_traiter_bag.command
#
# Reprocess one or more raw ROS 2 bags with the RevA DLIO container.
# The script:
#   1) starts Docker Desktop if necessary;
#   2) starts/reconfigures the RevA Compose service;
#   3) launches DLIO + rosbridge + ros2 bag record inside the container;
#   4) replays the selected raw bag;
#   5) closes the recorder cleanly and validates the generated ROS 2 bag.
#
# Optional environment variables:
#   HML_RAW_DIR       Host directory containing raw ROS 2 bags
#   HML_RESULTS_DIR   Host directory receiving processed ROS 2 bags
#
# Defaults intentionally match the field workstation layout:
#   ~/Desktop/Expedition_Data/raw
#   ~/Desktop/Expedition_Data/results

set -euo pipefail

CONTAINER_NAME="hml_lidar_reva"
HML_WS="/opt/hml_ws"
PARAMS_FILE="/root/hml/config/params.yaml"

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

HML_RAW_DIR="${HML_RAW_DIR:-$HOME/Desktop/Expedition_Data/raw}"
HML_RESULTS_DIR="${HML_RESULTS_DIR:-$HOME/Desktop/Expedition_Data/results}"
export HML_RAW_DIR HML_RESULTS_DIR

mkdir -p "$HML_RAW_DIR" "$HML_RESULTS_DIR"

docker_ready() {
    docker info >/dev/null 2>&1
}

ensure_docker() {
    echo "=== HML-LiDAR RevA : traitement DLIO ==="
    echo "Raw host     : $HML_RAW_DIR"
    echo "Results host : $HML_RESULTS_DIR"
    echo

    if ! docker_ready; then
        echo "Docker Desktop n'est pas actif. Démarrage..."
        open -a Docker

        local waited=0
        until docker_ready; do
            sleep 2
            waited=$((waited + 2))
            printf "En attente du moteur Docker... %ss\n" "$waited"
            if [ "$waited" -ge 90 ]; then
                echo "ERREUR : Docker Desktop ne répond pas après 90 secondes." >&2
                exit 1
            fi
        done
    fi

    echo "Docker opérationnel."

    # Remove a stale container created by an older Compose project if it
    # occupies the fixed RevA container name. This can happen after changing
    # the Compose project name (for example, from "mac" to "hml-lidar-reva").
    EXISTING_CONTAINER="$(docker ps -aq -f "name=^/${CONTAINER_NAME}$" | head -n 1 || true)"
    CURRENT_COMPOSE_CONTAINER="$(docker compose ps -aq ros2_processing 2>/dev/null | head -n 1 || true)"

    if [ -n "$EXISTING_CONTAINER" ] && [ "$EXISTING_CONTAINER" != "$CURRENT_COMPOSE_CONTAINER" ]; then
        echo "Ancien conteneur RevA détecté hors du projet Compose courant."
        echo "Suppression du conteneur obsolète (les images et les données hôte sont conservées)..."
        docker rm -f "$EXISTING_CONTAINER" >/dev/null
    fi

    # Compose uses HML_RAW_DIR/HML_RESULTS_DIR to mount the real expedition data.
    docker compose up -d

    if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        echo "ERREUR : le conteneur $CONTAINER_NAME n'est pas actif." >&2
        exit 1
    fi

    # Verify the frozen RevA software/configuration before processing data.
    docker exec "$CONTAINER_NAME" bash -lc "
        test -f '$PARAMS_FILE' &&
        source /opt/ros/humble/setup.bash &&
        source '$HML_WS/install/setup.bash' &&
        ros2 pkg executables direct_lidar_inertial_odometry | grep -q dlio_odom_node
    "

    echo "Environnement RevA validé."
}

cleanup_ros() {
    # Target only the processes used by this workflow.
    docker exec "$CONTAINER_NAME" bash -lc '
        pkill -INT -f "ros2 bag record" 2>/dev/null || true
        pkill -INT -f "ros2 bag play" 2>/dev/null || true
        pkill -INT -f "dlio_odom_node" 2>/dev/null || true
        pkill -INT -f "rosbridge_websocket" 2>/dev/null || true
        pkill -INT -f "rosbridge_server" 2>/dev/null || true
    ' >/dev/null 2>&1 || true
}

on_interrupt() {
    echo
    echo "Interruption demandée. Fermeture propre des processus ROS 2..."
    cleanup_ros
    exit 130
}
trap on_interrupt INT TERM

host_to_container_path() {
    local host_path="${1%/}"

    case "$host_path" in
        "$HML_RAW_DIR")
            printf '%s\n' "/root/data"
            ;;
        "$HML_RAW_DIR"/*)
            printf '/root/data/%s\n' "${host_path#"$HML_RAW_DIR"/}"
            ;;
        "$HML_RESULTS_DIR")
            printf '%s\n' "/root/ros2_ws/results"
            ;;
        "$HML_RESULTS_DIR"/*)
            printf '/root/ros2_ws/results/%s\n' "${host_path#"$HML_RESULTS_DIR"/}"
            ;;
        *)
            echo "ERREUR : l'archive sélectionnée n'est pas située sous :" >&2
            echo "  $HML_RAW_DIR" >&2
            echo "ou :" >&2
            echo "  $HML_RESULTS_DIR" >&2
            return 1
            ;;
    esac
}

validate_rosbag_host() {
    local bag_dir="$1"

    if [ ! -d "$bag_dir" ]; then
        echo "ERREUR : dossier introuvable : $bag_dir" >&2
        return 1
    fi

    if [ ! -f "$bag_dir/metadata.yaml" ]; then
        echo "ERREUR : metadata.yaml absent : $bag_dir" >&2
        return 1
    fi

    if ! find "$bag_dir" -maxdepth 1 -type f -name '*.db3' -print -quit | grep -q .; then
        echo "ERREUR : aucun fichier .db3 dans : $bag_dir" >&2
        return 1
    fi
}

make_output_name() {
    local bag_name="$1"
    local base="${bag_name}_result"
    local candidate="$base"

    if [ -e "$HML_RESULTS_DIR/$candidate" ]; then
        candidate="${base}_$(date '+%Y%m%d_%H%M%S')"
    fi

    printf '%s\n' "$candidate"
}

start_dlio() {
    local log_file="$1"

    docker exec -d "$CONTAINER_NAME" bash -lc "
        source /opt/ros/humble/setup.bash
        source '$HML_WS/install/setup.bash'
        exec ros2 run direct_lidar_inertial_odometry dlio_odom_node \
          --ros-args \
          --params-file '$PARAMS_FILE' \
          -p use_sim_time:=true \
          --remap pointcloud:=/livox/lidar \
          --remap imu:=/livox/imu \
          > '$log_file' 2>&1
    "
}

start_rosbridge() {
    local log_file="$1"

    docker exec -d "$CONTAINER_NAME" bash -lc "
        source /opt/ros/humble/setup.bash
        source '$HML_WS/install/setup.bash'
        exec ros2 launch rosbridge_server rosbridge_websocket_launch.xml \
          > '$log_file' 2>&1
    "
}

start_recording() {
    local output_name="$1"
    local log_file="$2"

    docker exec -d "$CONTAINER_NAME" bash -lc "
        source /opt/ros/humble/setup.bash
        source '$HML_WS/install/setup.bash'
        cd /root/ros2_ws/results
        exec ros2 bag record -a -o '$output_name' --storage sqlite3 \
          > '$log_file' 2>&1
    "
}

stop_recording_cleanly() {
    docker exec "$CONTAINER_NAME" bash -lc '
        pkill -INT -f "ros2 bag record" 2>/dev/null || true
    ' >/dev/null 2>&1 || true

    # Give rosbag2 time to close SQLite and write metadata.yaml.
    sleep 4
}

traiter_un_bag() {
    local mac_path="${1%/}"
    validate_rosbag_host "$mac_path"

    local bag_name
    bag_name="$(basename "$mac_path")"

    local docker_bag_path
    docker_bag_path="$(host_to_container_path "$mac_path")"

    local output_name
    output_name="$(make_output_name "$bag_name")"

    local output_host="$HML_RESULTS_DIR/$output_name"
    local output_container="/root/ros2_ws/results/$output_name"

    local log_dir_container="/root/ros2_ws/results/_logs"
    local timestamp
    timestamp="$(date '+%Y%m%d_%H%M%S')"

    echo
    echo "============================================================"
    echo "Traitement DLIO : $bag_name"
    echo "Entrée host     : $mac_path"
    echo "Entrée Docker   : $docker_bag_path"
    echo "Sortie host     : $output_host"
    echo "============================================================"

    docker exec "$CONTAINER_NAME" mkdir -p "$log_dir_container"

    cleanup_ros
    sleep 2

    echo "[1/5] Démarrage DLIO..."
    start_dlio "$log_dir_container/${bag_name}_${timestamp}_dlio.log"

    echo "[2/5] Démarrage rosbridge (port 9090)..."
    start_rosbridge "$log_dir_container/${bag_name}_${timestamp}_rosbridge.log"

    echo "[3/5] Démarrage de l'enregistrement ROS 2..."
    start_recording "$output_name" "$log_dir_container/${bag_name}_${timestamp}_record.log"

    # Allow nodes, publishers/subscribers and rosbag recorder to initialize.
    sleep 5

    echo "[4/5] Lecture de l'archive brute à 0.1x..."
    set +e
    docker exec "$CONTAINER_NAME" bash -lc "
        source /opt/ros/humble/setup.bash
        source '$HML_WS/install/setup.bash'
        exec ros2 bag play '$docker_bag_path' --clock -r 0.1 --delay 5
    "
    play_status=$?
    set -e

    echo
    echo "Lecture terminée (code=$play_status). Fermeture de l'enregistrement..."
    stop_recording_cleanly

    docker exec "$CONTAINER_NAME" bash -lc '
        pkill -INT -f "dlio_odom_node" 2>/dev/null || true
        pkill -INT -f "rosbridge_websocket" 2>/dev/null || true
        pkill -INT -f "rosbridge_server" 2>/dev/null || true
    ' >/dev/null 2>&1 || true

    if [ "$play_status" -ne 0 ]; then
        echo "ERREUR : ros2 bag play s'est terminé avec le code $play_status." >&2
        echo "Les journaux sont dans : $HML_RESULTS_DIR/_logs" >&2
        return "$play_status"
    fi

    echo "[5/5] Validation de l'archive traitée..."

    if [ ! -f "$output_host/metadata.yaml" ]; then
        echo "ERREUR : metadata.yaml n'a pas été créé dans $output_host." >&2
        echo "Consultez : $HML_RESULTS_DIR/_logs" >&2
        return 1
    fi

    if ! find "$output_host" -maxdepth 1 -type f -name '*.db3' -print -quit | grep -q .; then
        echo "ERREUR : aucun fichier .db3 généré dans $output_host." >&2
        return 1
    fi

    # Preserve the exact processing configuration used for this result.
    # The configuration directory is mounted read-only from PROTO/configuration.
    docker exec "$CONTAINER_NAME" bash -lc "
        cp -f '$PARAMS_FILE' '$output_container/params_used.yaml'
        PARAMS_SHA256=\$(sha256sum '$PARAMS_FILE' | awk '{print \$1}')
        {
          echo 'HML-LiDAR processing provenance'
          echo 'software_revision=RevA'
          echo 'source_bag=$bag_name'
          echo 'output_bag=$output_name'
          echo 'params_file=$PARAMS_FILE'
          echo \"params_sha256=\$PARAMS_SHA256\"
          echo 'dlio_commit=c8acc37100e349d70a9d8432d656cbce7e5072cd'
          echo \"processed_utc=\$(date -u '+%Y-%m-%dT%H:%M:%SZ')\"
        } > '$output_container/processing_info.txt'
    "

    if [ ! -f "$output_host/params_used.yaml" ] || [ ! -f "$output_host/processing_info.txt" ]; then
        echo "ERREUR : les informations de provenance n'ont pas été archivées." >&2
        return 1
    fi


    echo
    docker exec "$CONTAINER_NAME" bash -lc "
        source /opt/ros/humble/setup.bash
        ros2 bag info '$output_container'
    " || true

    echo
    echo "SUCCÈS : archive DLIO générée :"
    echo "  $output_host"
    echo
}

choose_one_bag_gui() {
    osascript -e '
        tell application "System Events"
            activate
            try
                set leDossier to choose folder with prompt "Sélectionnez l archive ROS 2 brute à traiter :"
                return POSIX path of leDossier
            on error
                return ""
            end try
        end tell
    '
}

choose_mode_gui() {
    osascript -e '
        tell application "System Events"
            activate
            try
                set r to display dialog "Sélectionnez le mode de traitement DLIO :" buttons {"Quitter", "Traiter toutes les archives raw", "Sélectionner une archive"} default button "Sélectionner une archive" cancel button "Quitter" with title "HML-LiDAR RevA"
                return button returned of r
            on error
                return "Quitter"
            end try
        end tell
    '
}

process_all_raw_bags() {
    local found=0

    while IFS= read -r -d '' metadata; do
        found=1
        traiter_un_bag "$(dirname "$metadata")"
    done < <(find "$HML_RAW_DIR" -type f -name metadata.yaml -print0 | sort -z)

    if [ "$found" -eq 0 ]; then
        echo "Aucune archive ROS 2 valide détectée sous $HML_RAW_DIR."
        return 1
    fi
}

ensure_docker

if [ "$#" -gt 0 ]; then
    traiter_un_bag "${1%/}"
else
    choix="$(choose_mode_gui)"

    case "$choix" in
        "Traiter toutes les archives raw")
            process_all_raw_bags
            ;;
        "Sélectionner une archive")
            dossier_cible="$(choose_one_bag_gui)"
            dossier_cible="${dossier_cible%/}"

            if [ -z "$dossier_cible" ]; then
                echo "Opération annulée."
                exit 0
            fi

            traiter_un_bag "$dossier_cible"
            ;;
        *)
            echo "Interruption demandée."
            exit 0
            ;;
    esac
fi

echo
echo "============================================================"
echo "Traitement terminé."
echo "Étape suivante : contrôler les segments, puis lancer Pegar."
echo "============================================================"
