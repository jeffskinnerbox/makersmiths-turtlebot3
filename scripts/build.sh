#!/usr/bin/env bash
# Build both Docker images (simulator + turtlebot).
# Run from project root.
# Usage: bash scripts/build.sh
#
# Docker group note: if jeff was recently added to the docker group,
# prefix with: sg docker -c "bash scripts/build.sh"
set -e

cd "$(dirname "$0")/.."

echo "[build] Building simulator image (turtlebot3_simulator)..."
docker build \
  --build-arg ROS_DISTRO=jazzy \
  -t turtlebot3_simulator \
  -f .devcontainer/Dockerfile.simulator \
  .

echo "[build] Building turtlebot image (turtlebot3_robot)..."
docker build \
  --build-arg ROS_DISTRO=jazzy \
  -t turtlebot3_robot \
  -f .devcontainer/Dockerfile.turtlebot \
  .

echo "[build] Done."
echo "  turtlebot3_simulator — desktop + Gazebo + Nav2"
echo "  turtlebot3_robot     — headless TB3 controller"
