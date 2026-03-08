#!/usr/bin/env bash
# Container entrypoint: source ROS + workspace, then exec command.
# G17: always source both — ros base AND workspace overlay.
set -e

source /opt/ros/${ROS_DISTRO}/setup.bash

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
    source "$HOME/ros2_ws/install/setup.bash"
fi

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"

exec "$@"
