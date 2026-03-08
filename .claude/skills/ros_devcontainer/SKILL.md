---
name: ros-devcontainer
description: Create and configure a ROS 2 development Docker container (DevContainer) for Minimal CLI, Full Desktop, or Custom Project (TurtleBot3) configurations. Use this skill when the user asks to set up Docker containers for ROS 2 development, create Dockerfiles, docker-compose files, devcontainer.json, or helper scripts for building and running ROS 2 containers. Covers GPU support, X11/VNC display, multi-container setups, and entrypoint configuration.
---

This skill creates and configures ROS 2 development Docker containers. It generates
Dockerfiles, docker-compose.yml, devcontainer.json, entrypoint scripts, build/run
helper scripts, and test scripts tailored to the user's host OS, GPU, display method,
IDE workflow, and robot platform.

## References

- **Primary guide**: "RCLPY From Zero To Hero" (Robotics Content Lab, 2025), Chapter 0.5
  - Container image tagging: `{ROS2-VERSION}-{ROS-BASE}-{UI}-{GRAPHICS-PLATFORM}`
  - DevContainer setup (devcontainer.json with ROS_DISTRO, INSTALL_PACKAGE, TARGET, GRAPHICS_PLATFORM)
  - Convenience script approach (run_docker.sh / run_docker.ps1)
  - Container images hosted on GHCR: `ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero`
  - Companion repo: `github.com/Robotics-Content-Lab/rclpy-from-zero-to-hero-container`
- **Automatic Addison**: "The Complete Guide to Docker for ROS 2 Jazzy Projects"
  - Multi-container docker-compose with YAML anchors
  - `network_mode: host` + `ipc: host` for DDS
  - X11 forwarding (`/tmp/.X11-unix`, `DISPLAY`, `.Xauthority`)
  - Two-script pattern: entrypoint.sh (runtime) + workspace.sh (build-time)
  - `SHELL ["/bin/bash", "-c"]` and `ENV DEBIAN_FRONTEND=noninteractive`
  - rosdep + colcon build in Dockerfile
- **RobotAir**: "The Complete Beginner's Guide to Using Docker for ROS 2 Deployment (2025)"
  - Multi-stage builds for smaller production images
  - Separating build and runtime dependencies
- **Docker Docs**: "Introduction to ROS 2 Development with Docker"
  - Official ROS 2 base images from Docker Hub
  - Turtlesim end-to-end example
  - Development container setup for local development

---

## Pre-Flight: User Questionnaire

**IMPORTANT**: Before generating any files, ask the user the following questions using AskUserQuestion. Use their answers to select the correct base image, Dockerfile features, compose services, and scripts.

### Questions to Ask

1. **ROS 2 distribution** for the Docker container?
   - Kilted
   - **Jazzy** (recommended)
   - Humble

2. **Host OS** where the container will run?
   - **Linux** (Ubuntu 24.04 preferred)
   - macOS (Intel or Apple Silicon)
   - Windows (with WSL2 recommended)

3. **GPU type** on the host?
   - **NVIDIA** (needs NVIDIA Container Toolkit)
   - **AMD** (Linux kernel drivers, no extra install)
   - **None** (no dedicated GPU; uses `LIBGL_ALWAYS_SOFTWARE=1`)
   - **Unknown** (same as None)

4. **ROS GUI tools** needed (RViz, Gazebo, rqt)?
   - **Yes** (full desktop image + X11 or VNC)
   - **No** (headless, terminal only)

5. **GUI display method** (if GUI tools = Yes)?
   - **X11 forwarding** (Linux remote, fastest)
   - **VNC browser desktop** (cross-platform, `http://localhost:6080`)

6. **IDE workflow**?
   - **VS Code DevContainer** (`.devcontainer/devcontainer.json`)
   - **Convenience script** (`scripts/run_docker.sh` + Docker sidebar)
   - **Terminal only** (manual `docker run`)

7. **Robot / project type**?
   - **TurtleBot3 with GUI** (TB3 on desktop image)
   - **TurtleBot3 with Terminal** (TB3 on headless image)
   - **Custom robot** (empty generic ROS 2 workspace)
   - **Simulation only** (RViz, Gazebo/Ignition)
   - **CI / deployment** (no GUI, minimal image)

8. **Hardware device access** (real robot, sensors, serial ports)?
   - **Yes** (`--privileged` and `/dev` mount)
   - **No** (simulation only)

9. **Multi-container setup** (e.g. separate simulator + controller)?
   - **Yes** (docker-compose with YAML anchors)
   - **No** (single container)

---

## Decision Matrix

Use the answers to select configuration parameters:

| Answer | Effect |
|---|---|
| **Distro = Jazzy** | `FROM ros:jazzy-ros-base` (headless) or `FROM osrf/ros:jazzy-desktop-full` (GUI) |
| **Distro = Humble** | `FROM ros:humble-ros-base` or `FROM osrf/ros:humble-desktop-full` |
| **Distro = Kilted** | `FROM ros:kilted-ros-base` or `FROM osrf/ros:kilted-desktop-full` |
| **Host = Linux** | X11 forwarding native; `xhost +local:docker` |
| **Host = macOS** | XQuartz required for X11; VNC recommended instead |
| **Host = Windows** | WSL2 backend; VNC recommended; WSLG for X11 |
| **GPU = NVIDIA** | `runtime: nvidia` in compose; `nvidia-container-toolkit` prereq |
| **GPU = AMD** | `--device /dev/dri` mount; Mesa drivers in image |
| **GPU = None/Unknown** | `ENV LIBGL_ALWAYS_SOFTWARE=1`; Mesa llvmpipe |
| **GUI = Yes** | Install `rviz2`, `rqt*`, Gazebo; X11 or VNC volumes |
| **GUI = No** | Skip all GUI packages; no display volumes |
| **Display = X11** | Mount `/tmp/.X11-unix`; pass `DISPLAY`; `.Xauthority` |
| **Display = VNC** | Install TurboVNC + noVNC; expose port 6080 |
| **IDE = DevContainer** | Generate `.devcontainer/devcontainer.json` |
| **IDE = Script** | Generate `scripts/run_docker.sh` |
| **IDE = Terminal** | Generate `scripts/run_docker.sh` (minimal) |
| **Robot = TB3 GUI** | Add `turtlebot3*`, `nav2*`, `slam_toolbox` to desktop image |
| **Robot = TB3 Terminal** | Add `turtlebot3*`, `nav2*`, `slam_toolbox` to base image |
| **Robot = Custom** | Empty `ros2_ws/src/`; no robot-specific packages |
| **Robot = Sim only** | Desktop image + Gazebo + RViz |
| **Robot = CI** | Multi-stage build; no GUI; minimal final image |
| **Hardware = Yes** | `privileged: true`; `/dev:/dev` volume |
| **Hardware = No** | No device mounts |
| **Multi-container = Yes** | YAML anchors in compose; separate services |
| **Multi-container = No** | Single service in compose |

---

## File Layout

All generated files follow this layout:

```
project_root/
├── .devcontainer/
│   └── devcontainer.json           # only if IDE = DevContainer
├── docker/
│   ├── Dockerfile.desktop          # full desktop image (GUI = Yes)
│   ├── Dockerfile.headless         # minimal CLI image (GUI = No)
│   ├── Dockerfile.turtlebot        # TB3-specific (Robot = TB3)
│   └── docker-compose.yml          # orchestration
├── scripts/
│   ├── build.sh                    # build Docker image(s)
│   ├── run_docker.sh               # start container(s) via convenience script
│   ├── attach_terminal.sh          # attach to running container
│   ├── stop.sh                     # stop and optionally remove container(s)
│   ├── workspace.sh                # build-time: rosdep + colcon build
│   └── test/
│       ├── test_container.sh       # verify container health
│       ├── test_ros_env.py         # verify ROS 2 env inside container
│       └── test_display.sh         # verify GUI/display (if GUI = Yes)
├── entrypoint.sh                   # runtime: source ROS, set domain ID
└── src/                            # ROS 2 workspace source (mounted)
```

---

## 1. Dockerfile Templates

### Common Dockerfile Header

All Dockerfiles share this header pattern:

```dockerfile
# ============================================================
# ROS 2 DevContainer — {VARIANT} image
# Generated by ros_devcontainer skill
# ============================================================
ARG ROS_DISTRO=jazzy
```

### 1.1 Headless / Minimal CLI (`docker/Dockerfile.headless`)

```dockerfile
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    tmux \
    vim \
    && rm -rf /var/lib/apt/lists/*

# rosdep init (idempotent)
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then \
      rosdep init; \
    fi

# Create non-root user
ARG USERNAME=ros_user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN userdel -r ubuntu 2>/dev/null || true && \
    groupadd --gid ${USER_GID} ${USERNAME} 2>/dev/null || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ${USERNAME}
WORKDIR /home/${USERNAME}

# rosdep update as user
RUN rosdep update --rosdistro=${ROS_DISTRO}

# Workspace
RUN mkdir -p ~/ros2_ws/src
WORKDIR /home/${USERNAME}/ros2_ws

# Source ROS in bashrc
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc && \
    echo "[ -f ~/ros2_ws/install/setup.bash ] && source ~/ros2_ws/install/setup.bash" >> ~/.bashrc

# Environment
ENV ROS_DISTRO=${ROS_DISTRO}
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=0

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
```

### 1.2 Full Desktop (`docker/Dockerfile.desktop`)

```dockerfile
ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# System deps + GUI support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    tmux \
    vim \
    mesa-utils \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# rosdep init (idempotent)
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then \
      rosdep init; \
    fi

# Create non-root user (osrf image ships ubuntu at UID 1000)
ARG USERNAME=ros_user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN userdel -r ubuntu 2>/dev/null || true && \
    groupadd --gid ${USER_GID} ${USERNAME} 2>/dev/null || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN rosdep update --rosdistro=${ROS_DISTRO}

RUN mkdir -p ~/ros2_ws/src
WORKDIR /home/${USERNAME}/ros2_ws

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc && \
    echo "[ -f ~/ros2_ws/install/setup.bash ] && source ~/ros2_ws/install/setup.bash" >> ~/.bashrc

ENV ROS_DISTRO=${ROS_DISTRO}
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=0

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
```

### 1.3 TurtleBot3 Project (`docker/Dockerfile.turtlebot`)

Extends the desktop image with TB3, Nav2, and SLAM packages:

```dockerfile
ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV TURTLEBOT3_MODEL=burger

# System deps + GUI + TB3/Nav2/SLAM
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git curl wget \
    python3-pip python3-colcon-common-extensions \
    python3-rosdep python3-vcstool \
    tmux vim \
    mesa-utils libgl1-mesa-dri libgl1-mesa-glx x11-apps \
    ros-${ROS_DISTRO}-turtlebot3* \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-teleop-twist-keyboard \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-rmw-fastrtps-cpp \
    && rm -rf /var/lib/apt/lists/*

RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then \
      rosdep init; \
    fi

ARG USERNAME=ros_user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN userdel -r ubuntu 2>/dev/null || true && \
    groupadd --gid ${USER_GID} ${USERNAME} 2>/dev/null || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN rosdep update --rosdistro=${ROS_DISTRO}

RUN mkdir -p ~/ros2_ws/src
WORKDIR /home/${USERNAME}/ros2_ws

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc && \
    echo "[ -f ~/ros2_ws/install/setup.bash ] && source ~/ros2_ws/install/setup.bash" >> ~/.bashrc && \
    echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc

ENV ROS_DISTRO=${ROS_DISTRO}
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=0
ENV GZ_IP=127.0.0.1
# gz binary not in standard PATH
ENV PATH=/opt/ros/${ROS_DISTRO}/opt/gz_tools_vendor/bin:${PATH}

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
```

---

## 2. GPU-Specific Additions

### NVIDIA

Add to `docker-compose.yml` service:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=all
```

**Prerequisite**: Install NVIDIA Container Toolkit on the host:

```bash
# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# then install nvidia-container-toolkit
```

### AMD

Add to `docker-compose.yml` service:

```yaml
devices:
  - /dev/dri:/dev/dri
```

No extra host install needed; AMD packs GPU drivers in the Linux kernel.

### None / Unknown

Add to Dockerfile:

```dockerfile
ENV LIBGL_ALWAYS_SOFTWARE=1
```

---

## 3. Display Forwarding

### X11 (Linux — fastest)

Host-side one-time setup:

```bash
xhost +local:docker
```

docker-compose.yml additions:

```yaml
environment:
  - DISPLAY=${DISPLAY}
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix:rw
  - ${HOME}/.Xauthority:/home/ros_user/.Xauthority:ro
```

### VNC (cross-platform)

Add to Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    novnc \
    websockify \
    openbox \
    xterm \
    && rm -rf /var/lib/apt/lists/*
```

docker-compose.yml additions:

```yaml
ports:
  - "6080:6080"   # noVNC web client
  - "5900:5900"   # VNC direct
```

Access via browser: `http://localhost:6080`

---

## 4. docker-compose.yml Template (`docker/docker-compose.yml`)

```yaml
# ============================================================
# ROS 2 DevContainer — Docker Compose
# Generated by ros_devcontainer skill
# ============================================================

x-ros-common: &ros-common
  build:
    context: ..
    dockerfile: docker/Dockerfile.desktop
    args:
      ROS_DISTRO: jazzy
  environment:
    - ROS_DOMAIN_ID=0
    - RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    - TURTLEBOT3_MODEL=burger
    - GZ_IP=127.0.0.1
    - DISPLAY=${DISPLAY:-:0}
  volumes:
    - ../src:/home/ros_user/ros2_ws/src
    - ../scripts:/home/ros_user/ros2_ws/scripts
    - /tmp/.X11-unix:/tmp/.X11-unix:rw
  network_mode: host
  ipc: host
  stdin_open: true
  tty: true

services:
  ros2_dev:
    <<: *ros-common
    container_name: ros2_dev
    command: sleep infinity

  # Uncomment for multi-container setup:
  # ros2_sim:
  #   <<: *ros-common
  #   container_name: ros2_sim
  #   build:
  #     context: ..
  #     dockerfile: docker/Dockerfile.turtlebot
  #   command: sleep infinity
```

### Multi-Container Variant (when Multi-container = Yes)

```yaml
services:
  simulator:
    <<: *ros-common
    container_name: ros2_simulator
    build:
      context: ..
      dockerfile: docker/Dockerfile.turtlebot
    command: sleep infinity

  controller:
    <<: *ros-common
    container_name: ros2_controller
    build:
      context: ..
      dockerfile: docker/Dockerfile.headless
    command: sleep infinity
    depends_on:
      - simulator
```

### Hardware Device Access (when Hardware = Yes)

Add to service:

```yaml
privileged: true
volumes:
  - /dev:/dev
```

---

## 5. DevContainer Configuration (`.devcontainer/devcontainer.json`)

Generated only when IDE = VS Code DevContainer:

```jsonc
// See https://aka.ms/vscode-remote/devcontainer.json for format details.
{
  "name": "ROS 2 Jazzy DevContainer",
  "dockerComposeFile": "../docker/docker-compose.yml",
  "service": "ros2_dev",
  "workspaceFolder": "/home/ros_user/ros2_ws",
  "remoteUser": "ros_user",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-iot.vscode-ros",
        "ms-python.python",
        "ms-vscode.cpptools-extension-pack",
        "twxs.cmake",
        "redhat.vscode-yaml",
        "zachflower.uncrustify",
        "smilerobotics.urdf",
        "DotJoshJohnson.xml",
        "yzhang.markdown-all-in-one"
      ],
      "settings": {
        "files.eol": "\n",
        "editor.wordWrap": "on",
        "python.analysis.extraPaths": [
          "/opt/ros/jazzy/lib/python3.12/dist-packages"
        ]
      }
    }
  },
  "forwardPorts": [],
  "postCreateCommand": "sudo rosdep update && cd /home/ros_user/ros2_ws && colcon build --symlink-install",
  "shutdownAction": "stopCompose"
}
```

---

## 6. entrypoint.sh

Place at project root (`entrypoint.sh`):

```bash
#!/usr/bin/env bash
set -e

# Source ROS 2 base
source /opt/ros/${ROS_DISTRO}/setup.bash

# Source workspace overlay if it exists
if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
fi

# Set ROS domain ID (default 0)
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"

# Execute the command passed to the container
exec "$@"
```

---

## 7. Helper Scripts

### 7.1 `scripts/build.sh` — Build Docker Images

```bash
#!/usr/bin/env bash
# Build ROS 2 Docker image(s)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

DOCKERFILE="${1:-docker/Dockerfile.desktop}"
IMAGE_NAME="${2:-ros2_dev:latest}"
ROS_DISTRO="${3:-jazzy}"

echo "Building ${IMAGE_NAME} from ${DOCKERFILE} (ROS_DISTRO=${ROS_DISTRO})..."
docker image build \
  -f "${PROJECT_DIR}/${DOCKERFILE}" \
  --build-arg ROS_DISTRO="${ROS_DISTRO}" \
  -t "${IMAGE_NAME}" \
  "${PROJECT_DIR}"

echo "Build complete: ${IMAGE_NAME}"
```

### 7.2 `scripts/run_docker.sh` — Start Container

```bash
#!/usr/bin/env bash
# Start ROS 2 Docker container via docker-compose or docker run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -d, --distro DISTRO    ROS 2 distribution (jazzy|humble|kilted) [default: jazzy]
  -p, --profile PROFILE  Image profile (desktop|headless|turtlebot) [default: desktop]
  -g, --gpu GPU          GPU type (nvidia|amd|none) [default: auto-detect]
  -c, --compose          Use docker-compose instead of docker run
  -h, --help             Show this help message
EOF
  exit 0
}

ROS_DISTRO="jazzy"
PROFILE="desktop"
GPU="none"
USE_COMPOSE=false

# Auto-detect GPU
if command -v nvidia-smi &>/dev/null; then
  GPU="nvidia"
elif [ -d /dev/dri ]; then
  GPU="amd"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--distro)  ROS_DISTRO="$2"; shift 2 ;;
    -p|--profile) PROFILE="$2"; shift 2 ;;
    -g|--gpu)     GPU="$2"; shift 2 ;;
    -c|--compose) USE_COMPOSE=true; shift ;;
    -h|--help)    usage ;;
    *)            echo "Unknown option: $1"; usage ;;
  esac
done

DOCKERFILE="docker/Dockerfile.${PROFILE}"
IMAGE_NAME="ros2_${PROFILE}:${ROS_DISTRO}"
CONTAINER_NAME="ros2_${PROFILE}"

if $USE_COMPOSE; then
  echo "Starting via docker-compose..."
  docker compose -f "${PROJECT_DIR}/docker/docker-compose.yml" up -d
  echo "Attach with: bash scripts/attach_terminal.sh ${CONTAINER_NAME}"
  exit 0
fi

# Build if image doesn't exist
if ! docker image inspect "${IMAGE_NAME}" &>/dev/null; then
  echo "Image not found. Building..."
  bash "${SCRIPT_DIR}/build.sh" "${DOCKERFILE}" "${IMAGE_NAME}" "${ROS_DISTRO}"
fi

# GPU flags
GPU_FLAGS=""
case "$GPU" in
  nvidia)
    GPU_FLAGS="--runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=all"
    ;;
  amd)
    GPU_FLAGS="--device /dev/dri:/dev/dri"
    ;;
  none)
    GPU_FLAGS="-e LIBGL_ALWAYS_SOFTWARE=1"
    ;;
esac

# X11 display
DISPLAY_FLAGS=""
if [ -n "${DISPLAY:-}" ]; then
  xhost +local:docker 2>/dev/null || true
  DISPLAY_FLAGS="-e DISPLAY=${DISPLAY} -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
fi

echo "Starting container ${CONTAINER_NAME}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --network host \
  --ipc host \
  ${GPU_FLAGS} \
  ${DISPLAY_FLAGS} \
  -e ROS_DOMAIN_ID=0 \
  -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
  -e GZ_IP=127.0.0.1 \
  -v "${PROJECT_DIR}/src:/home/ros_user/ros2_ws/src" \
  -v "${PROJECT_DIR}/scripts:/home/ros_user/ros2_ws/scripts" \
  "${IMAGE_NAME}" \
  sleep infinity

echo "Container started. Attach with: bash scripts/attach_terminal.sh ${CONTAINER_NAME}"
```

### 7.3 `scripts/attach_terminal.sh` — Attach to Running Container

```bash
#!/usr/bin/env bash
# Attach an interactive shell to a running ROS 2 container
set -euo pipefail

CONTAINER="${1:-ros2_dev}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Error: container '${CONTAINER}' is not running."
  echo "Running containers:"
  docker ps --format '  {{.Names}} ({{.Image}})'
  exit 1
fi

echo "Attaching to ${CONTAINER}..."
docker exec -it "${CONTAINER}" bash -l
```

### 7.4 `scripts/stop.sh` — Stop Container(s)

```bash
#!/usr/bin/env bash
# Stop and optionally remove ROS 2 container(s)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ "${1:-}" = "--compose" ]; then
  docker compose -f "${PROJECT_DIR}/docker/docker-compose.yml" down
else
  CONTAINER="${1:-ros2_dev}"
  docker stop "${CONTAINER}" 2>/dev/null && docker rm "${CONTAINER}" 2>/dev/null
  echo "Stopped and removed: ${CONTAINER}"
fi
```

### 7.5 `scripts/workspace.sh` — Build-Time Workspace Setup

Used inside the Dockerfile or as a post-create command:

```bash
#!/usr/bin/env bash
# Build-time: install deps + colcon build inside the container
set -euo pipefail

source /opt/ros/${ROS_DISTRO}/setup.bash

cd ~/ros2_ws

# Install dependencies
if [ -d src ] && [ "$(ls -A src)" ]; then
  rosdep install --from-paths src --ignore-src -r -y
fi

# Build
colcon build --symlink-install

source install/setup.bash
echo "Workspace build complete."
```

---

## 8. Test Scripts

### 8.1 `scripts/test/test_container.sh` — Container Health Check

```bash
#!/usr/bin/env bash
# Verify the ROS 2 container is healthy
set -euo pipefail

CONTAINER="${1:-ros2_dev}"

echo "=== Container Health Check ==="

# Check container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "FAIL: container '${CONTAINER}' is not running"
  exit 1
fi
echo "PASS: container is running"

# Check ROS 2 is installed
docker exec "${CONTAINER}" bash -c "source /opt/ros/\${ROS_DISTRO}/setup.bash && which ros2" >/dev/null 2>&1
echo "PASS: ros2 CLI found"

# Check RMW
RMW=$(docker exec "${CONTAINER}" bash -c "echo \${RMW_IMPLEMENTATION}")
echo "PASS: RMW = ${RMW}"

# Check workspace mount
docker exec "${CONTAINER}" bash -c "test -d ~/ros2_ws/src"
echo "PASS: ~/ros2_ws/src is mounted"

# Check user is not root
USER=$(docker exec "${CONTAINER}" whoami)
if [ "${USER}" != "root" ]; then
  echo "PASS: running as non-root user (${USER})"
else
  echo "WARN: running as root"
fi

echo "=== All checks passed ==="
```

### 8.2 `scripts/test/test_ros_env.py` — Verify ROS 2 Environment

```python
#!/usr/bin/env python3
"""Verify ROS 2 environment inside the container."""
import subprocess
import sys
import os


def check(name, condition, msg=""):
    status = "PASS" if condition else "FAIL"
    detail = f" — {msg}" if msg else ""
    print(f"  {status}: {name}{detail}")
    return condition


def main():
    ok = True
    print("=== ROS 2 Environment Test ===")

    # ROS_DISTRO set
    distro = os.environ.get("ROS_DISTRO", "")
    ok &= check("ROS_DISTRO", bool(distro), distro)

    # rclpy importable
    try:
        import rclpy  # noqa: F401
        ok &= check("rclpy import", True)
    except ImportError as e:
        ok &= check("rclpy import", False, str(e))

    # RMW set
    rmw = os.environ.get("RMW_IMPLEMENTATION", "")
    ok &= check("RMW_IMPLEMENTATION", bool(rmw), rmw)

    # colcon available
    result = subprocess.run(["which", "colcon"], capture_output=True)
    ok &= check("colcon available", result.returncode == 0)

    print("=== Done ===")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

### 8.3 `scripts/test/test_display.sh` — Verify GUI/Display (if GUI = Yes)

```bash
#!/usr/bin/env bash
# Verify X11 or VNC display is working inside the container
set -euo pipefail

CONTAINER="${1:-ros2_dev}"

echo "=== Display Test ==="

# Check DISPLAY is set
DISP=$(docker exec "${CONTAINER}" bash -c "echo \${DISPLAY:-}")
if [ -z "${DISP}" ]; then
  echo "SKIP: DISPLAY not set (headless mode)"
  exit 0
fi
echo "PASS: DISPLAY=${DISP}"

# Try glxinfo
docker exec "${CONTAINER}" bash -c "source /opt/ros/\${ROS_DISTRO}/setup.bash && glxinfo -B 2>/dev/null | head -5" && \
  echo "PASS: glxinfo works" || \
  echo "WARN: glxinfo failed (may need mesa-utils)"

# Try xdpyinfo
docker exec "${CONTAINER}" bash -c "xdpyinfo -display ${DISP} 2>/dev/null | head -3" && \
  echo "PASS: X11 connection works" || \
  echo "WARN: xdpyinfo failed (X11 may not be forwarded)"

echo "=== Done ==="
```

---

## 9. ROS 2 Launch Script for Container Bringup

### `src/<package>/launch/container_bringup.launch.py`

When the user has a ROS 2 package, generate a launch file that brings up core nodes:

```python
"""Launch file for container bringup — starts core nodes."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock'),

        LogInfo(msg='Starting container bringup...'),

        # Add project-specific nodes here
    ])
```

---

## 10. Known Gotchas and Workarounds

| Issue | Fix |
|---|---|
| `docker permission denied` | Add user to `docker` group; use `sg docker -c "..."` until re-login |
| `osrf/ros` image has `ubuntu` at UID 1000 | `userdel -r ubuntu` before `useradd` in Dockerfile |
| `docker run -it` no TTY in subprocess | Start with `sleep infinity`; attach from terminal |
| `ros2 topic list` hangs | DDS multicast; use `which ros2` to verify instead |
| CycloneDDS hangs on many bridge/veth | Switch to `rmw_fastrtps_cpp` |
| gz-transport multicast fails | Set `GZ_IP=127.0.0.1` |
| `ros2` CLI breaks with only workspace sourced | Source both: `/opt/ros/.../setup.bash` AND `install/setup.bash` |
| `gz` binary not in PATH | Add `/opt/ros/${ROS_DISTRO}/opt/gz_tools_vendor/bin` to PATH |
| macOS: no GPU acceleration in Docker | Use `LIBGL_ALWAYS_SOFTWARE=1` or VNC |
| Windows: WSL2 required for Docker | Install WSL2 backend; WSLG for GUI |

---

## Checklist: What Gets Generated

Based on user answers, generate only the applicable files:

- [ ] `docker/Dockerfile.{headless|desktop|turtlebot}` — one or more
- [ ] `docker/docker-compose.yml` — always
- [ ] `entrypoint.sh` — always
- [ ] `.devcontainer/devcontainer.json` — only if IDE = DevContainer
- [ ] `scripts/build.sh` — always
- [ ] `scripts/run_docker.sh` — always
- [ ] `scripts/attach_terminal.sh` — always
- [ ] `scripts/stop.sh` — always
- [ ] `scripts/workspace.sh` — always
- [ ] `scripts/test/test_container.sh` — always
- [ ] `scripts/test/test_ros_env.py` — always
- [ ] `scripts/test/test_display.sh` — only if GUI = Yes

All scripts must be `chmod +x`. Backup any existing file before overwriting.
