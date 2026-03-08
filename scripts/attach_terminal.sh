#!/usr/bin/env bash
# Attach an interactive shell to a running container.
# Usage: bash scripts/attach_terminal.sh [container_name]
# Default container: turtlebot3_simulator
set -euo pipefail

CONTAINER="${1:-turtlebot3_simulator}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "Error: '${CONTAINER}' is not running."
    echo "Running containers:"
    docker ps --format '  {{.Names}}'
    exit 1
fi

echo "Attaching to ${CONTAINER}..."
docker exec -it "${CONTAINER}" bash -l
