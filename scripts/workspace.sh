#!/usr/bin/env bash
# Run INSIDE the container to install rosdep deps and build the colcon workspace.
# Usage: bash /home/ros_user/ros2_ws/scripts/workspace.sh [--clean]
#
# From host:
#   docker exec turtlebot3_simulator bash /home/ros_user/ros2_ws/scripts/workspace.sh
set -e

WS_ROOT="/home/ros_user/ros2_ws"
DISTRO="${ROS_DISTRO:-jazzy}"

source /opt/ros/${DISTRO}/setup.bash

cd "${WS_ROOT}"

if [ "${1}" = "--clean" ]; then
  echo "[workspace] Cleaning build/, install/, log/..."
  rm -rf build/ install/ log/
fi

echo "[workspace] Running rosdep update..."
rosdep update

echo "[workspace] Installing dependencies from src/..."
rosdep install --from-paths src --ignore-src -r -y

echo "[workspace] Building workspace (--symlink-install)..."
colcon build --symlink-install

echo "[workspace] Done."
echo "  Source with: source ${WS_ROOT}/install/setup.bash"
