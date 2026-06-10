#!/usr/bin/env bash
set -euo pipefail

# Repo URLs and where to clone them
declare -A repos=(
  [ros2_ws/src/livox_ros_driver2]="https://github.com/Livox-SDK/livox_ros_driver2.git"
  [Livox-SDK2]="https://github.com/Livox-SDK/Livox-SDK2.git"
  [ros2_ws/src/rviz_2d_overlay_plugins]="https://github.com/teamspatzenhirn/rviz_2d_overlay_plugins.git"
  [ros2_ws/src/SuperOdom]="https://github.com/superxslam/SuperOdom.git"
  [Sophus]="http://github.com/strasdat/Sophus.git"
  [gtsam]="https://github.com/borglab/gtsam.git"
  [ros2_ws/src/ego-planner-swarm]="https://github.com/ZJU-FAST-Lab/ego-planner-swarm.git"
)

for target in "${!repos[@]}"; do
  url=${repos[$target]}
  if [ -d "$target" ]; then
    echo "✔ $target already exists; skipping."
  else
    echo "⏳ Cloning $url → $target"
    mkdir -p "$(dirname "$target")"
    if [[ "$target" == "ros2_ws/src/ego-planner-swarm" ]]; then
    git clone --branch ros2_version --single-branch "$url" "$target"
    else
    git clone "$url" "$target"
    fi
  fi
done

TARGET_DIR="ros2_ws/src/livox_ros_driver2"
OLD_FILE="$TARGET_DIR/package_ROS2.xml"
NEW_FILE="$TARGET_DIR/package.xml"

if [ -f "$OLD_FILE" ]; then
  if [ -e "$NEW_FILE" ]; then
    echo "⚠️  Le fichier cible existe déjà : $NEW_FILE" >&2
  fi

  echo "Copie de $OLD_FILE → $NEW_FILE"
  cp "$OLD_FILE" "$NEW_FILE"
  echo "Terminé. $OLD_FILE est toujours là."
else
  echo "⚠️  Fichier introuvable : $OLD_FILE" >&2
fi

config_src="MID360_config.json"
config_dst="ros2_ws/src/livox_ros_driver2/config/MID360_config.json"

if [ -f "$config_src" ]; then
  echo "Copying config $config_src → $config_dst"
  mkdir -p "$(dirname "$config_dst")"
  cp "$config_src" "$config_dst"
  echo "Configuration updated."
else
  echo "⚠️  Config file not found: $config_src" >&2
fi

launch_src="single_run_real.launch.py"
launch_dst="ros2_ws/src/ego-planner-swarm/src/planner/plan_manage/launch"

if [ ! -f "$launch_src" ]; then
  echo "⚠️  Launch file not found: $launch_src" >&2
fi

echo "Copying $launch_src → $launch_dst/"
mkdir -p "$launch_dst"
cp "$launch_src" "$launch_dst/"
echo "✅  Copied."

chmod +x docker-entrypoint.sh
