#!/usr/bin/env bash
# Attach an interactive shell to a running container.
# Usage: bash scripts/attach_terminal.sh [container_name]
#   Default container: turtlebot3_simulator
set -e

CONTAINER_NAME="${1:-turtlebot3_simulator}"

if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
  echo "Container '${CONTAINER_NAME}' is not running."
  echo "Running containers:"
  docker ps --format "  {{.Names}}"
  exit 1
fi

echo "Attaching to: ${CONTAINER_NAME}"
docker exec -it "${CONTAINER_NAME}" bash
