#!/usr/bin/env bash
# Start the two-container ROS 2 stack (simulator + turtlebot) detached.
# Run from project root.
# Usage: bash scripts/run_docker.sh [-g <gpu>]
#   -g  GPU platform: nvidia | amd | standard (default: auto-detect)
#   -h  Show help
#
# Docker group note: prefix with sg docker -c "..." until re-login after usermod.
set -e

cd "$(dirname "$0")/.."

GPU=""

usage() {
  echo "Usage: bash scripts/run_docker.sh [-g nvidia|amd|standard] [-h]"
  exit 0
}

while getopts "g:h" opt; do
  case $opt in
    g) GPU=$OPTARG ;;
    h) usage ;;
    *) echo "Unknown option: -$OPTARG"; usage ;;
  esac
done

# ── Auto-detect GPU ────────────────────────────────────────────────────────────
if [ -z "$GPU" ]; then
  if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
    GPU="nvidia"
    echo "[run_docker] Auto-detected: NVIDIA GPU"
  elif ls /dev/dri/renderD* &>/dev/null 2>&1; then
    GPU="amd"
    echo "[run_docker] Auto-detected: AMD GPU (DRI render node)"
  else
    GPU="standard"
    echo "[run_docker] No dedicated GPU detected — using software rendering (LIBGL_ALWAYS_SOFTWARE=1)"
  fi
fi

# ── GPU-specific docker run args ───────────────────────────────────────────────
GPU_ARGS=""
if [ "$GPU" = "nvidia" ]; then
  GPU_ARGS="--gpus all -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute -e NVIDIA_VISIBLE_DEVICES=all"
elif [ "$GPU" = "amd" ]; then
  GPU_ARGS="--device /dev/dri"
elif [ "$GPU" = "standard" ]; then
  GPU_ARGS="-e LIBGL_ALWAYS_SOFTWARE=1"
fi

# ── Allow X11 access ───────────────────────────────────────────────────────────
xhost +local:docker 2>/dev/null || true

# ── Common run args ────────────────────────────────────────────────────────────
COMMON_ARGS="
  --network host
  --ipc host
  -e DISPLAY=${DISPLAY}
  -e XAUTHORITY=/tmp/.Xauthority
  -e QT_X11_NO_MITSHM=1
  -e ROS_DISTRO=jazzy
  -e ROS_DOMAIN_ID=0
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  -e TURTLEBOT3_MODEL=burger
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw
  -v ${HOME}/.Xauthority:/tmp/.Xauthority:ro
  -v $(pwd)/src:/home/ros_user/ros2_ws/src:cached
  -v $(pwd)/.colcon:/home/ros_user/ros2_ws/.colcon:ro
"

# ── Start simulator container ──────────────────────────────────────────────────
docker rm -f turtlebot3_simulator 2>/dev/null || true
echo "[run_docker] Starting turtlebot3_simulator..."
docker run -d \
  --name turtlebot3_simulator \
  ${GPU_ARGS} \
  ${COMMON_ARGS} \
  turtlebot3_simulator \
  sleep infinity

# ── Start turtlebot container ──────────────────────────────────────────────────
docker rm -f turtlebot3_turtlebot 2>/dev/null || true
echo "[run_docker] Starting turtlebot3_turtlebot..."
docker run -d \
  --name turtlebot3_turtlebot \
  ${GPU_ARGS} \
  ${COMMON_ARGS} \
  turtlebot3_robot \
  sleep infinity

echo ""
echo "[run_docker] Both containers running. Attach with:"
echo "  bash scripts/attach_terminal.sh turtlebot3_simulator"
echo "  bash scripts/attach_terminal.sh turtlebot3_turtlebot"
