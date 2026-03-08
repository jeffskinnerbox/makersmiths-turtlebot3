#!/usr/bin/env bash
# Start containers detached via docker-compose.
# G1: run as: sg docker -c "bash scripts/run_docker.sh"
# G3: containers start with sleep infinity; use attach_terminal.sh to get a shell.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Allow X11 connections from local Docker containers (required for Gazebo GUI)
xhost +local:docker 2>/dev/null || true

cd "$PROJECT_DIR"
docker compose -f docker/docker-compose.yaml up -d "$@"

echo "Containers started."
echo "  Simulator: bash scripts/attach_terminal.sh turtlebot3_simulator"
echo "  Robot:     bash scripts/attach_terminal.sh turtlebot3_robot"
