#!/usr/bin/env bash
# HML-LiDAR RevA
# Safe transfer of raw ROS 2 acquisition data from the Raspberry Pi to macOS.
#
# This script intentionally does NOT start Docker and does NOT delete source
# data by default. Acquisition transfer and post-processing are separate steps.
#
# Optional environment variables:
#   HML_RP_USER        Remote Raspberry Pi user
#   HML_RP_HOST        Remote Raspberry Pi host
#   HML_RP_PATH        Remote acquisition directory
#   HML_LOCAL_BASE     Local HML-LiDAR data directory
#   HML_RSYNC_SUDO     1 to run rsync through sudo on the Raspberry Pi
#
# Optional argument:
#   --delete-remote    Offer to delete the transferred remote files after a
#                      successful rsync. A second explicit confirmation is
#                      required.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

RP_USER="${HML_RP_USER:-samuel}"
RP_HOST="${HML_RP_HOST:-chinook.local}"
RP_PATH="${HML_RP_PATH:-/home/samuel/Cave_explorer/data/cave_data/}"
LOCAL_BASE="${HML_LOCAL_BASE:-$HOME/Desktop/Expedition_Data}"
RAW_DIR="${LOCAL_BASE}/raw"
LOG_DIR="${LOCAL_BASE}/logs"

HML_RSYNC_SUDO="${HML_RSYNC_SUDO:-1}"
DELETE_REMOTE=0

usage() {
    cat <<EOF
Usage:
  ${SCRIPT_NAME}
  ${SCRIPT_NAME} --delete-remote

Environment overrides:
  HML_RP_USER
  HML_RP_HOST
  HML_RP_PATH
  HML_LOCAL_BASE
  HML_RSYNC_SUDO
EOF
}

for arg in "$@"; do
    case "$arg" in
        --delete-remote)
            DELETE_REMOTE=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            usage
            exit 2
            ;;
    esac
done

command -v ssh >/dev/null 2>&1 || {
    echo "ERROR: ssh is not available." >&2
    exit 1
}

command -v rsync >/dev/null 2>&1 || {
    echo "ERROR: rsync is not available." >&2
    exit 1
}

mkdir -p "$RAW_DIR" "$LOG_DIR"

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
LOG_FILE="${LOG_DIR}/transfer_${TIMESTAMP}.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "HML-LiDAR RevA — Raw data transfer"
echo "============================================================"
echo "Remote source : ${RP_USER}@${RP_HOST}:${RP_PATH}"
echo "Local target  : ${RAW_DIR}/"
echo "Transfer log  : ${LOG_FILE}"
echo

echo "[1/4] Checking SSH connection..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "${RP_USER}@${RP_HOST}" "printf 'SSH_OK\n'" 2>/dev/null | grep -q "SSH_OK"; then
    echo "ERROR: Unable to establish non-interactive SSH access to ${RP_USER}@${RP_HOST}."
    echo "Verify the host name, network connection, and SSH public-key configuration."
    exit 1
fi
echo "SSH connection OK."

echo
echo "[2/4] Checking remote acquisition directory..."
if ! ssh "${RP_USER}@${RP_HOST}" "test -d '${RP_PATH}'"; then
    echo "ERROR: Remote directory does not exist: ${RP_PATH}"
    exit 1
fi

REMOTE_FILE_COUNT="$(
    ssh "${RP_USER}@${RP_HOST}" \
        "find '${RP_PATH}' -type f 2>/dev/null | wc -l | tr -d ' '"
)"
echo "Remote files detected: ${REMOTE_FILE_COUNT}"

if [ "${REMOTE_FILE_COUNT}" = "0" ]; then
    echo "No files to transfer."
    exit 0
fi

echo
echo "[3/4] Transferring data with rsync..."

RSYNC_ARGS=(-avz --progress --partial)

if [ "${HML_RSYNC_SUDO}" = "1" ]; then
    RSYNC_ARGS+=(--rsync-path="sudo rsync")
fi

rsync "${RSYNC_ARGS[@]}" \
    "${RP_USER}@${RP_HOST}:${RP_PATH}" \
    "${RAW_DIR}/"

echo
echo "[4/4] Transfer completed successfully."
echo "Raw data retained on Raspberry Pi."
echo "Local archive: ${RAW_DIR}"

if [ "${DELETE_REMOTE}" = "1" ]; then
    echo
    echo "WARNING: --delete-remote was requested."
    echo "The remote acquisition data will be permanently deleted from:"
    echo "  ${RP_USER}@${RP_HOST}:${RP_PATH}"
    echo
    read -r -p "Type DELETE to confirm remote cleanup: " CONFIRMATION

    if [ "${CONFIRMATION}" = "DELETE" ]; then
        echo "Deleting transferred remote files..."
        ssh "${RP_USER}@${RP_HOST}" \
            "sudo find '${RP_PATH}' -mindepth 1 -depth -delete"
        echo "Remote acquisition directory cleaned."
    else
        echo "Remote cleanup cancelled. Source data were preserved."
    fi
fi

echo
echo "============================================================"
echo "NEXT STEP"
echo "Process the transferred ROS 2 bags with 2_traiter_bag.command."
echo "============================================================"
