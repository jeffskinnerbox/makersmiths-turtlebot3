#!/usr/bin/env bash
# Build the ROS 2 workspace inside the container.
# G17: source both setup files before any ros2 CLI or colcon.
# Usage (inside container): bash ~/ros2_ws/scripts/workspace.sh
set -euo pipefail

source /opt/ros/${ROS_DISTRO}/setup.bash

cd ~/ros2_ws

if [ -d src ] && [ "$(ls -A src 2>/dev/null)" ]; then
    rosdep install --from-paths src --ignore-src -r -y
fi

colcon build

if [ -f install/setup.bash ]; then
    source install/setup.bash
fi

echo "Workspace build complete."
