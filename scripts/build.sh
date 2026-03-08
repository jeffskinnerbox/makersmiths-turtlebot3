#!/usr/bin/env bash
# Build Docker images via docker-compose.
# G1: run as: sg docker -c "bash scripts/build.sh"
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
docker compose -f docker/docker-compose.yaml build "$@"
echo "Build complete."
