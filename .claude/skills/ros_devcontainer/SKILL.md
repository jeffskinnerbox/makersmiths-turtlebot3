---
name: ros_devcontainer
description: Create and configure a ROS 2 development Docker container (DevContainer). Use this skill
  when the user asks to set up Docker for ROS 2, write a Dockerfile, configure devcontainer.json,
  handle GUI/display forwarding (X11 or VNC), GPU passthrough, bash helper scripts, or docker-compose
  for ROS 2. Covers three archetypes: Minimal CLI, Full Desktop, Custom Project. Supports Jazzy,
  Kilted, and Humble. Produces Dockerfile, devcontainer.json, entrypoint.sh, scripts/, docker-compose.yml,
  and config/params.yaml.
---

This skill guides creation and configuration of Docker-based development containers (DevContainers) for ROS 2.
A DevContainer packages the OS, ROS 2 runtime, tools, and workspace into a portable, reproducible environment
— eliminating "it works on my machine" problems across dev machines, robots, and CI systems.

> **Sources:**
> - *RCLPY From Zero to Hero*, Robotics Content Lab (2025), §0.5 pp. 14–23
> - Automatic Addison: The Complete Guide to Docker for ROS 2 Jazzy Projects
> - RobotAir: The Complete Beginner's Guide to Using Docker for ROS 2 Deployment (2025)
> - Docker Official Docs: Introduction to ROS 2 Development with Docker

---

## 0. Discovery Questions

**Before generating any files, ask the user ALL of the following questions.**
Use the answers to select the correct archetype, base image, GPU flags, display method, and files to generate.

```text
1. ROS 2 distribution?
   - Kilted
   - Jazzy (recommended)
   - Humble

2. Host OS?
   - Linux (Ubuntu 24.04 preferred)
   - macOS (Intel or Apple Silicon)
   - Windows (WSL2 required)

3. GPU type?
   - NVIDIA (needs Container Toolkit)
   - AMD (Linux kernel drivers, no extra install)
   - None / Unknown (software rendering — LIBGL_ALWAYS_SOFTWARE=1)

4. ROS GUI tools needed? (RViz, Gazebo, rqt)
   - Yes — full desktop image + X11 or VNC
   - No — headless / CLI only

5. GUI display method? (if answer #4 = Yes)
   - X11 forwarding (Linux native, fastest)
   - VNC browser desktop (Windows, macOS, remote machines)

6. IDE workflow?
   - VS Code DevContainer (.devcontainer/devcontainer.json)
   - Convenience script (run_docker.sh + attach via Docker sidebar)
   - Terminal only (manual docker run)

7. Robot / project type?
   - TurtleBot3 GUI (Archetype C — desktop + TB3 packages + sim)
   - TurtleBot3 Terminal (Archetype C — headless + TB3 packages)
   - Custom robot / generic ROS 2 workspace (Archetype C)
   - Simulation only — Gazebo / Ignition (Archetype B)
   - CI / deployment — no GUI, minimal image (Archetype A)

8. Hardware device access needed? (real robot, sensors, serial ports)
   - Yes (needs --privileged and /dev mount)
   - No

9. Multi-container setup? (e.g. separate simulator + controller containers)
   - Yes (use docker-compose with YAML anchors)
   - No (single container)

10. docker-compose for Minimal CLI? (only asked if answer #7 = CI / deployment)
    - Yes (include docker-compose.yml)
    - No, single container only (recommended)

11. ROS 2 launch files for TurtleBot3? (only asked if answer #7 = TurtleBot3 GUI or Terminal)
    - Defer to ros_launch skill (recommended)
    - Include basic bringup.launch.py stub

12. VNC image strategy? (only asked if answer #5 = VNC and answer #2 = macOS or Windows)
    - Auto-switch to tiryoh/ros2-desktop-vnc image (recommended)
    - Document manual steps only
```

### Answer → Archetype Mapping

| Answers Profile | Archetype |
|---|---|
| GUI=No, robot=CI-deploy or Custom (headless) | **A — Minimal CLI** (`ros:<distro>-ros-base`) |
| GUI=Yes, IDE=DevContainer or Script, no custom packages | **B — Full Desktop** (`osrf/ros:<distro>-desktop-full`) |
| robot=TurtleBot3 GUI, TurtleBot3 Terminal, or Custom with packages | **C — Custom Project** (`osrf/ros:<distro>-desktop-full` + extras) |

---

## 1. Container Archetypes

| Archetype | Base Image | Use Case |
|---|---|---|
| **A — Minimal CLI** | `ros:<distro>-ros-base` | Headless, CI, production robot deployment |
| **B — Full Desktop** | `osrf/ros:<distro>-desktop-full` | Dev + sim (RViz, Gazebo, rqt) |
| **C — Custom Project** | `osrf/ros:<distro>-desktop-full` + custom pkgs | TurtleBot3 dev + navigation, custom robots |

Book reference — image tag convention from pp. 16–17:

```text
ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:{ROS2-VERSION}-{ROS-BASE}-{UI}-{GRAPHICS-PLATFORM}
```

| Field | Options |
|---|---|
| `ROS2-VERSION` | `jazzy`, `kilted`, `humble` |
| `ROS-BASE` | `desktop`, `base` |
| `UI` | `terminal` (Tmux, lighter) · `vnc` (browser desktop) |
| `GRAPHICS-PLATFORM` | `standard` · `nvidia` · `amd` |

Example: `ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:jazzy-desktop-terminal-nvidia`

> **Note:** Kilted and Humble follow the same Docker patterns as Jazzy.
> Substitute the distro name in all image tags, env vars (`ROS_DISTRO`), and apt package names (e.g. `ros-humble-*`).

---

## 2. Prerequisites

### Docker

- **Linux**: Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) then run post-install non-root steps.
- **macOS / Windows**: Install [Docker Desktop](https://docs.docker.com/get-docker/).
- **Windows**: Enable WSL2 backend — required for ROS 2 containers and GPU support.

Post-install (non-root Linux):

```bash
sudo usermod -aG docker $USER
newgrp docker       # apply immediately; or log out/in for persistent effect
```

> Reference: <https://docs.docker.com/engine/install/linux-postinstall/>

### VS Code Extensions

```bash
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-vscode-remote.vscode-remote-extensionpack
```

### NVIDIA Container Toolkit (GPU=NVIDIA only)

```bash
# Install
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor \
  -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# Full guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### AMD GPU

AMD drivers are built into the Linux kernel — no extra install required. DRI render devices
are exposed automatically.

---

## 3. Generated File Layout

When the user chooses Archetype C (or Archetype A/B with scripts), generate this structure:

```text
<project_root>/
├── .devcontainer/
│   ├── devcontainer.json       # VS Code DevContainer spec
│   └── Dockerfile              # Custom image definition
├── config/
│   └── params.yaml             # Robot / node parameters
├── src/                        # colcon workspace source (host-mounted)
├── scripts/
│   ├── build.sh                # Build the Docker image
│   ├── run_docker.sh           # Start container (GPU/display auto-detect)
│   ├── attach_terminal.sh      # Attach shell to running container
│   └── workspace.sh            # Inside container: rosdep + colcon build
├── docker-compose.yml          # Multi-container (if answer #9 = Yes)
└── entrypoint.sh               # Container startup: sources ROS before CMD
```

---

## 4. Dockerfile

Generate the Dockerfile at `.devcontainer/Dockerfile`. Choose the variant matching the archetype.

### Archetype A — Minimal CLI

```dockerfile
# ── Archetype A: Minimal CLI (headless / CI / deployment) ────────────────────
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
  && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────────────────────
# osrf images ship an 'ubuntu' user at UID 1000; remove it first to avoid conflict
RUN userdel -r ubuntu 2>/dev/null || true \
  && useradd -m -u 1000 -s /bin/bash ros_user \
  && echo "ros_user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/ros_user \
  && chmod 0440 /etc/sudoers.d/ros_user

RUN mkdir -p /home/ros_user/ros2_ws/src \
  && chown -R ros_user:ros_user /home/ros_user/ros2_ws

ENV ROS_DISTRO=${ROS_DISTRO}
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=0

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/ros_user/.bashrc \
  && echo "source /home/ros_user/ros2_ws/install/setup.bash 2>/dev/null || true" \
     >> /home/ros_user/.bashrc

USER ros_user
WORKDIR /home/ros_user/ros2_ws

COPY --chown=ros_user:ros_user entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
```

### Archetype B — Full Desktop (GUI)

```dockerfile
# ── Archetype B: Full Desktop (RViz, Gazebo, rqt) ───────────────────────────
ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
SHELL ["/bin/bash", "-c"]

# Mesa driver update (fixes black-screen RViz on some hosts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
  && add-apt-repository ppa:kisak/kisak-mesa \
  && apt-get update && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    build-essential \
    vim \
    tmux \
    x11-apps \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
  && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────────────────────
RUN userdel -r ubuntu 2>/dev/null || true \
  && useradd -m -u 1000 -s /bin/bash ros_user \
  && echo "ros_user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/ros_user \
  && chmod 0440 /etc/sudoers.d/ros_user

RUN mkdir -p /home/ros_user/ros2_ws/src \
  && chown -R ros_user:ros_user /home/ros_user/ros2_ws

ENV ROS_DISTRO=${ROS_DISTRO}
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=0
ENV QT_X11_NO_MITSHM=1

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/ros_user/.bashrc \
  && echo "source /home/ros_user/ros2_ws/install/setup.bash 2>/dev/null || true" \
     >> /home/ros_user/.bashrc

USER ros_user
WORKDIR /home/ros_user/ros2_ws

COPY --chown=ros_user:ros_user entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
```

### Archetype C — Custom Project (TurtleBot3 / Custom Robot)

```dockerfile
# ── Archetype C: Custom Project (TurtleBot3 + Navigation) ───────────────────
ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
SHELL ["/bin/bash", "-c"]

# Mesa driver update (fixes black-screen RViz on some hosts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
  && add-apt-repository ppa:kisak/kisak-mesa \
  && apt-get update && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/*

# Core tools + TurtleBot3 / Navigation packages
# Adjust ros-${ROS_DISTRO}-* packages to your project needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    build-essential \
    vim \
    tmux \
    x11-apps \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-turtlebot3 \
    ros-${ROS_DISTRO}-turtlebot3-simulations \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-cartographer-ros \
  && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────────────────────
# osrf/ros:jazzy-desktop-full ships 'ubuntu' at UID 1000 — remove before adding ros_user
RUN userdel -r ubuntu 2>/dev/null || true \
  && useradd -m -u 1000 -s /bin/bash ros_user \
  && echo "ros_user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/ros_user \
  && chmod 0440 /etc/sudoers.d/ros_user

RUN mkdir -p /home/ros_user/ros2_ws/src \
  && chown -R ros_user:ros_user /home/ros_user/ros2_ws

ENV ROS_DISTRO=${ROS_DISTRO}
ENV TURTLEBOT3_MODEL=burger
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=0
ENV QT_X11_NO_MITSHM=1

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/ros_user/.bashrc \
  && echo "source /home/ros_user/ros2_ws/install/setup.bash 2>/dev/null || true" \
     >> /home/ros_user/.bashrc \
  && echo "export TURTLEBOT3_MODEL=burger" >> /home/ros_user/.bashrc

USER ros_user
WORKDIR /home/ros_user/ros2_ws

COPY --chown=ros_user:ros_user entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
```

---

## 5. devcontainer.json

VS Code DevContainer config — place at `.devcontainer/devcontainer.json` (from book p. 22 pattern).

```jsonc
// .devcontainer/devcontainer.json
// See https://aka.ms/vscode-remote/devcontainer.json for format details
{
  "name": "ROS 2 Dev",
  "dockerFile": "Dockerfile",
  "context": "..",

  // Build args — override ROS_DISTRO here if needed
  "build": {
    "args": {
      "ROS_DISTRO": "jazzy"
    }
  },

  // Mount host src/ into the container workspace
  "mounts": [
    "source=${localWorkspaceFolder}/src,target=/home/ros_user/ros2_ws/src,type=bind,consistency=cached"
  ],

  // X11 forwarding (Linux). For VNC: remove X11 entries and expose port 6080 instead.
  // For NVIDIA GPU: add "--gpus", "all" to runArgs.
  // For hardware access: add "--privileged", "-v", "/dev:/dev" to runArgs.
  "runArgs": [
    "-e", "DISPLAY=${localEnv:DISPLAY}",
    "-e", "XAUTHORITY=/tmp/.Xauthority",
    "-v", "/tmp/.X11-unix:/tmp/.X11-unix:rw",
    "-v", "${localEnv:HOME}/.Xauthority:/tmp/.Xauthority",
    "--network", "host",
    "--ipc", "host"
  ],

  "containerEnv": {
    "ROS_DISTRO": "jazzy",
    "ROS_DOMAIN_ID": "0",
    "RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp",
    "TURTLEBOT3_MODEL": "burger"
  },

  // Install rosdep deps automatically after container creation
  "postCreateCommand": "cd /home/ros_user/ros2_ws && rosdep update && rosdep install --from-paths src --ignore-src -r -y",

  "remoteUser": "ros_user",

  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-iot.vscode-ros",
        "twxs.cmake",
        "ms-vscode.cmake-tools",
        "ms-vscode.cpptools",
        "ms-vscode.cpptools-extension-pack",
        "redhat.vscode-yaml",
        "smilerobotics.urdf",
        "DotJoshJohnson.xml",
        "eamodio.gitlens",
        "yzhang.markdown-all-in-one"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/bin/python3",
        "editor.formatOnSave": true,
        "files.eol": "\n",
        "editor.wordWrap": "on"
      }
    }
  }
}
```

### Adapting `devcontainer.json` (key variables)

| Variable | Options | Default |
|---|---|---|
| `ROS_DISTRO` (build arg) | `jazzy`, `kilted`, `humble` | `jazzy` |
| `ROS_DOMAIN_ID` | `0`–`101` | `0` |
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp`, `rmw_fastrtps_cpp` | `rmw_cyclonedds_cpp` |
| `TURTLEBOT3_MODEL` | `burger`, `waffle`, `waffle_pi` | `burger` |

> **Note on `runArgs` quoting**: each flag and value must be a separate string in the array —
> `"-e", "DISPLAY=..."` not `"-e DISPLAY=..."`.

---

## 6. entrypoint.sh

Place at `entrypoint.sh` (project root). Sources ROS environment at container startup before
handing off to the user's command.

```bash
#!/usr/bin/env bash
set -e

source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash

if [ -f /home/ros_user/ros2_ws/install/setup.bash ]; then
  source /home/ros_user/ros2_ws/install/setup.bash
fi

exec "$@"
```

Make executable on host before building:

```bash
chmod +x entrypoint.sh
```

---

## 7. scripts/build.sh

Build the Docker image. Run from project root.

```bash
#!/usr/bin/env bash
# Usage: ./scripts/build.sh [image_name]
set -e

IMAGE_NAME="${1:-turtlebot3_dev}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

echo "Building image: ${IMAGE_NAME} (ROS_DISTRO=${ROS_DISTRO})"
docker build \
  --build-arg ROS_DISTRO="${ROS_DISTRO}" \
  -t "${IMAGE_NAME}" \
  -f .devcontainer/Dockerfile \
  .
echo "Done: ${IMAGE_NAME}"
```

> **Tip**: If `jeff` was recently added to the `docker` group, prefix with `sg docker -c "..."` until re-login.

---

## 8. scripts/run_docker.sh

Start the container. Key features (from book pp. 20–21):

- CLI flags: `-d <distro>`, `-p <profile>`, `-t <terminal|vnc>`, `-g <gpu>`, `-h`
- Auto-detect GPU: checks `nvidia-smi` → nvidia; checks `/dev/dri` → amd; else standard
- WSL2 detection: adjusts paths for Windows WSL2
- Workspace mount: `./src:/home/ros_user/ros2_ws/src`
- X11: mounts socket, passes `DISPLAY` and `XAUTHORITY`
- VNC: exposes port 6080 (noVNC), password 123456
- NVIDIA: `--gpus all --env NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute`
- **Detached start** (`sleep infinity`) — no `-it` in script (Claude Code subprocess has no TTY)

```bash
#!/usr/bin/env bash
# Usage: ./scripts/run_docker.sh [-d <distro>] [-p <profile>] [-t <ui>] [-g <gpu>] [-n <name>] [-h]
#   -d  ROS 2 distro   (jazzy|kilted|humble)   default: jazzy
#   -p  Base profile   (desktop|base)           default: desktop
#   -t  UI type        (terminal|vnc)           default: terminal
#   -g  GPU platform   (standard|nvidia|amd)    default: auto-detect
#   -n  Container name                          default: turtlebot3_dev
#   -h  Show help
set -e

DISTRO="jazzy"
PROFILE="desktop"
UI="terminal"
GPU=""
CONTAINER_NAME="turtlebot3_dev"
IMAGE_NAME="turtlebot3_dev"

usage() {
  grep '^#' "$0" | grep -v '#!/' | sed 's/^# \?//'
  exit 0
}

while getopts "d:p:t:g:n:h" opt; do
  case $opt in
    d) DISTRO=$OPTARG ;;
    p) PROFILE=$OPTARG ;;
    t) UI=$OPTARG ;;
    g) GPU=$OPTARG ;;
    n) CONTAINER_NAME=$OPTARG ;;
    h) usage ;;
    *) echo "Unknown option: -$OPTARG"; usage ;;
  esac
done

# ── Auto-detect GPU ────────────────────────────────────────────────────────────
if [ -z "$GPU" ]; then
  if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    GPU="nvidia"
    echo "[run_docker] Auto-detected: NVIDIA GPU"
  elif ls /dev/dri/renderD* &>/dev/null 2>&1; then
    GPU="amd"
    echo "[run_docker] Auto-detected: AMD GPU (DRI render node)"
  else
    GPU="standard"
    echo "[run_docker] No dedicated GPU detected — using software rendering"
  fi
fi

# ── Detect WSL2 ───────────────────────────────────────────────────────────────
WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
  WSL=true
  echo "[run_docker] WSL2 detected — adjusting display config"
fi

# ── GPU args ───────────────────────────────────────────────────────────────────
GPU_ARGS=""
if [ "$GPU" = "nvidia" ]; then
  GPU_ARGS="--gpus all -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute -e NVIDIA_VISIBLE_DEVICES=all"
elif [ "$GPU" = "standard" ]; then
  GPU_ARGS="-e LIBGL_ALWAYS_SOFTWARE=1"
fi

# ── Display args ───────────────────────────────────────────────────────────────
DISPLAY_ARGS=""
if [ "$UI" = "vnc" ]; then
  DISPLAY_ARGS="-p 6080:6080"
elif [ "$WSL" = true ]; then
  DISPLAY_ARGS="-e DISPLAY=${DISPLAY:-:0} -e WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0} -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
else
  xhost +local:docker 2>/dev/null || true
  DISPLAY_ARGS="-e DISPLAY=${DISPLAY} -e XAUTHORITY=/tmp/.Xauthority -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v ${HOME}/.Xauthority:/tmp/.Xauthority"
fi

# Hardware device access — uncomment to enable:
# PRIVILEGED="--privileged -v /dev/ttyUSB0:/dev/ttyUSB0 -v /dev/bus/usb:/dev/bus/usb"
PRIVILEGED=""

# ── Remove stale container if it exists ────────────────────────────────────────
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

echo "[run_docker] Starting detached container: ${CONTAINER_NAME}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  ${GPU_ARGS} \
  ${DISPLAY_ARGS} \
  ${PRIVILEGED} \
  -e ROS_DISTRO="${DISTRO}" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}" \
  -e RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}" \
  -e TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}" \
  -v "$(pwd)/src:/home/ros_user/ros2_ws/src" \
  --network host \
  --ipc host \
  "${IMAGE_NAME}" \
  sleep infinity

echo "[run_docker] Container running. Attach with:"
echo "  docker exec -it ${CONTAINER_NAME} bash"
echo "  # or: bash scripts/attach_terminal.sh"
```

---

## 9. scripts/attach_terminal.sh

Attach an interactive shell to the running container.

```bash
#!/usr/bin/env bash
# Usage: ./scripts/attach_terminal.sh [container_name]
set -e

CONTAINER_NAME="${1:-turtlebot3_dev}"

if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
  echo "Container '${CONTAINER_NAME}' is not running."
  echo "Running containers:"
  docker ps --format "  {{.Names}}"
  exit 1
fi

echo "Attaching to: ${CONTAINER_NAME}"
docker exec -it "${CONTAINER_NAME}" bash
```

---

## 10. scripts/workspace.sh

Run **inside the container** to install rosdep deps and build the colcon workspace.

```bash
#!/usr/bin/env bash
# Run INSIDE the container to install rosdep deps and build the workspace.
# Usage: ./scripts/workspace.sh [--clean]
set -e

WS_ROOT="/home/ros_user/ros2_ws"
DISTRO="${ROS_DISTRO:-jazzy}"

source /opt/ros/${DISTRO}/setup.bash

cd "${WS_ROOT}"

if [ "$1" = "--clean" ]; then
  echo "[workspace] Cleaning build/, install/, log/..."
  rm -rf build/ install/ log/
fi

echo "[workspace] Running rosdep update..."
rosdep update

echo "[workspace] Installing dependencies from src/..."
rosdep install --from-paths src --ignore-src -r -y

echo "[workspace] Building workspace (--symlink-install)..."
colcon build --symlink-install

echo "[workspace] Done. Source with:"
echo "  source ${WS_ROOT}/install/setup.bash"
```

Execute from host via:

```bash
docker exec turtlebot3_dev bash /path/to/scripts/workspace.sh
```

---

## 11. docker-compose.yml

Generate when answer #9 = Yes. Uses YAML anchors (`&anchor` / `<<: *anchor`) to share config.

```yaml
# docker-compose.yml
x-ros-base: &ros-base
  image: turtlebot3_dev:latest
  ipc: host                   # required for DDS shared-memory transport
  network_mode: host          # required for ROS 2 DDS discovery
  environment:
    - DISPLAY
    - XAUTHORITY=/tmp/.Xauthority
    - QT_X11_NO_MITSHM=1
    - ROS_DISTRO=jazzy
    - ROS_DOMAIN_ID=0
    - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    - TURTLEBOT3_MODEL=burger
  volumes:
    - /tmp/.X11-unix:/tmp/.X11-unix:rw
    - $HOME/.Xauthority:/tmp/.Xauthority
    - ./src:/home/ros_user/ros2_ws/src

services:
  dev:
    <<: *ros-base
    container_name: turtlebot3_dev
    stdin_open: true
    tty: true
    command: sleep infinity

  sim:
    <<: *ros-base
    container_name: turtlebot3_sim
    # Archetype B/C only — Gazebo simulator
    command: bash -c "source /opt/ros/jazzy/setup.bash && ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py"
    depends_on:
      - dev

  robot:
    <<: *ros-base
    container_name: turtlebot3_robot
    # Archetype C only — real hardware container
    privileged: true
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - $HOME/.Xauthority:/tmp/.Xauthority
      - ./src:/home/ros_user/ros2_ws/src
      - /dev/ttyUSB0:/dev/ttyUSB0
      - /dev/bus/usb:/dev/bus/usb
    command: bash -c "source /opt/ros/jazzy/setup.bash && bash"
```

```bash
xhost +local:docker
docker compose up -d                    # start all services
docker compose exec dev bash            # attach shell to dev service
docker compose stop                     # stop (preserves state)
docker compose down                     # stop + remove containers
```

---

## 12. config/params.yaml

Robot and node parameters. Load via `ros2 launch` or `ros2 run` with `--ros-args --params-file`.

```yaml
turtlebot3:
  model: burger
  ros_domain_id: 0
  rmw_implementation: rmw_cyclonedds_cpp

/turtlebot3_node:
  ros__parameters:
    opencr:
      id: 200
      baud_rate: 1000000
      protocol_version: 2.0
    sensor:
      imu_frequency: 200
      range_threshold: 0.01
```

---

## 13. Environment Variables Reference

| Variable | Purpose | Typical Value |
|---|---|---|
| `ROS_DISTRO` | Active ROS 2 distribution | `jazzy` |
| `ROS_DOMAIN_ID` | DDS network isolation (0–101) | `0` |
| `RMW_IMPLEMENTATION` | DDS middleware selection | `rmw_cyclonedds_cpp` |
| `TURTLEBOT3_MODEL` | Robot model for TurtleBot3 | `burger` |
| `DISPLAY` | X11 display server address | `:0` (Linux) |
| `XAUTHORITY` | X11 auth cookie path | `/tmp/.Xauthority` |
| `QT_X11_NO_MITSHM` | Fixes Qt shared memory crash in containers | `1` |
| `NVIDIA_DRIVER_CAPABILITIES` | NVIDIA GPU capability flags | `graphics,utility,compute` |
| `NVIDIA_VISIBLE_DEVICES` | GPU device selection | `all` |
| `LIBGL_ALWAYS_SOFTWARE` | Force software OpenGL rendering | `1` (no GPU) |
| `DEBIAN_FRONTEND` | Suppress apt interactive prompts | `noninteractive` |
| `PIP_BREAK_SYSTEM_PACKAGES` | Allow pip to install system packages (Ubuntu 24.04) | `1` |

---

## 14. GPU Configuration

### NVIDIA

```bash
# Install NVIDIA Container Toolkit first:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

docker run -d \
  --gpus all \
  -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute \
  -e NVIDIA_VISIBLE_DEVICES=all \
  turtlebot3_dev sleep infinity
```

`devcontainer.json` runArgs addition:

```jsonc
"--gpus", "all",
"-e", "NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute"
```

### AMD

No extra install — kernel drivers are built-in. DRI devices exposed automatically. Standard
run command works as-is; optionally add `--device /dev/dri` for explicit mapping:

```bash
docker run -d --device /dev/dri turtlebot3_dev sleep infinity
```

### None / Unknown (Software Rendering)

```bash
docker run -d -e LIBGL_ALWAYS_SOFTWARE=1 turtlebot3_dev sleep infinity
```

Software rendering is functional but slow — expect low frame rates in Gazebo/RViz.

---

## 15. Display / GUI Setup

### X11 (Linux — fastest)

```bash
# Allow docker to connect to X server (run once per login session)
xhost +local:docker

# Verify X11 works inside container
docker exec turtlebot3_dev bash -c "DISPLAY=$DISPLAY xeyes"
```

Required run args:

```bash
-e DISPLAY=$DISPLAY
-e XAUTHORITY=/tmp/.Xauthority
-e QT_X11_NO_MITSHM=1
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
-v $HOME/.Xauthority:/tmp/.Xauthority
```

> **Note**: `xhost +local:docker` resets on reboot. Add to `~/.bashrc` or re-run each session.

### VNC Browser Desktop (Windows, macOS, remote)

No X11 socket needed. Access via browser — no client install required.

```bash
# Robotics Content Lab pre-built VNC image (macOS/Windows — answer #12 = Auto-switch)
docker run -d \
  --name ros2_vnc \
  -p 6080:6080 \
  ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:jazzy-desktop-vnc-standard

# Alternative: tiryoh/ros2-desktop-vnc (recommended for macOS/Windows)
docker run -d \
  --name ros2_vnc \
  -p 6080:6080 \
  tiryoh/ros2-desktop-vnc:jazzy
```

Open browser: `http://localhost:6080/` — default password: **`123456`**

### Verification (non-blocking)

> **WARNING**: Do NOT use `ros2 topic list` to verify — DDS peer discovery blocks indefinitely in containerized environments.

```bash
# Verify ROS 2 is installed (non-blocking)
docker exec turtlebot3_dev which ros2
docker exec turtlebot3_dev python3 -c "import rclpy; print('rclpy OK')"

# Verify workspace sourced
docker exec turtlebot3_dev bash -c "source /opt/ros/jazzy/setup.bash && ros2 --version"
```

---

## 16. VS Code DevContainer Workflow

From book pp. 18–22:

### DevContainer (`.devcontainer/devcontainer.json`)

1. Install the Remote Development extension pack:

   ```bash
   code --install-extension ms-vscode-remote.vscode-remote-extensionpack
   ```

2. Open the project folder in VS Code.
3. Press `F1` → `Dev Containers: Reopen in Container` (or click the blue `><` button bottom-left).
4. To adapt configuration: edit `.devcontainer/devcontainer.json`.
5. Apply changes: `Ctrl+Shift+P` → `Developer: Reload Window`.

### Convenience Script → VS Code Attach

When using `run_docker.sh` instead of DevContainer:

1. VS Code **Docker icon** in sidebar
2. **Individual Containers** → right-click your container → **Attach Visual Studio Code**
3. `Ctrl+Shift+P` → `Dev Containers: Open attached container configuration file`
4. Paste a minimal config and save:

```jsonc
{
  "remoteUser": "ros_user",
  "workspaceFolder": "/home/ros_user/ros2_ws",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-iot.vscode-ros",
        "ms-python.python",
        "twxs.cmake",
        "ms-vscode.cpptools",
        "ms-vscode.cpptools-extension-pack",
        "redhat.vscode-yaml",
        "smilerobotics.urdf",
        "DotJoshJohnson.xml",
        "yzhang.markdown-all-in-one"
      ],
      "settings": {
        "files.eol": "\n",
        "editor.wordWrap": "on"
      }
    }
  }
}
```

1. `Ctrl+Shift+P` → `Developer: Reload Window`

---

## 17. TurtleBot3 Packages (Archetype C)

Install in Dockerfile (already included in Archetype C template above):

```dockerfile
RUN apt-get install -y \
  ros-${ROS_DISTRO}-turtlebot3 \
  ros-${ROS_DISTRO}-turtlebot3-simulations \
  ros-${ROS_DISTRO}-navigation2 \
  ros-${ROS_DISTRO}-nav2-bringup \
  ros-${ROS_DISTRO}-cartographer-ros
```

Required environment variables for TurtleBot3:

```bash
export TURTLEBOT3_MODEL=burger   # burger | waffle | waffle_pi
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Device mounts for real hardware (answer #8 = Yes):

```bash
# Serial port (OpenCR board)
-v /dev/ttyUSB0:/dev/ttyUSB0

# USB bus (camera, LIDAR)
-v /dev/bus/usb:/dev/bus/usb

# Or use --privileged for full device access (less secure)
--privileged -v /dev:/dev
```

Simulation verification (inside container):

```bash
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

> **Launch files**: For structured bringup, use the `ros_launch` skill to generate
> Python launch files for TurtleBot3 nodes and navigation.

---

## 18. Troubleshooting

From book p. 23:

- **Docker permission denied**: Add user to docker group.
  Reference: <https://docs.docker.com/engine/install/linux-postinstall/>
  Workaround until re-login: `sg docker -c "bash scripts/build.sh"`
- **Duplicate container name**: `docker rm turtlebot3_dev` (or use `docker rm -f`)
- **Container runtime not running**: Linux: `sudo systemctl start docker`; macOS/Windows: open Docker Desktop
- **GUI apps not rendering (black window)**: Run `xhost +local:docker`; try `LIBGL_ALWAYS_SOFTWARE=1`; try mesa PPA update in Dockerfile
- **Windows — GUI not rendering**: Enable WSLg: <https://docs.microsoft.com/en-us/windows/wsl/tutorials/gui-apps>
- **VNC not accessible**: Confirm `-p 6080:6080` in run args; check firewall; default password is `123456`
- **`ros2 topic list` hangs**: Use `which ros2` or `python3 -c "import rclpy"` instead — DDS discovery blocks in containers
- **`ros2 topic list` shows nothing**: Verify `--network host` and `--ipc host`; all containers share same `ROS_DOMAIN_ID`; check `RMW_IMPLEMENTATION` matches
- **`rosdep install` fails**: Run `rosdep update` first; confirm `src/` is mounted and `package.xml` files are present
- **`colcon build` fails "package not found"**: Source `/opt/ros/<distro>/setup.bash` before building
- **NVIDIA: `--gpus` flag not recognised**: NVIDIA Container Toolkit not installed
- **`entrypoint.sh` permission denied**: Run `chmod +x entrypoint.sh` on host before building image

---

## 19. Jazzy / Kilted / Humble Gotchas

- **`ubuntu` user UID conflict**: `osrf/ros:jazzy-desktop-full` ships `ubuntu` at UID 1000.
  Dockerfile must run `userdel -r ubuntu 2>/dev/null || true` before `useradd ros_user`.
- **`docker run -it` in scripts**: No TTY in Claude Code subprocess. Start detached with
  `sleep infinity`, then attach from user's terminal with `docker exec -it <name> bash`.
- **`xhost +local:docker` resets on reboot**: Add to `~/.bashrc` or re-run each session.
- **`XAUTHORITY` passthrough**: Mount `$HOME/.Xauthority:/tmp/.Xauthority` and set
  `-e XAUTHORITY=/tmp/.Xauthority` for reliable X11 auth with display managers (GDM/SDDM).
- **`sg docker` workaround**: `sg docker -c "bash scripts/build.sh"` until re-login after `usermod`.
- **`ipc: host`**: Required alongside `network_mode: host` for DDS shared-memory transport.
- **`source install/setup.bash`**: Must be sourced after every `colcon build`.
  `postCreateCommand` handles `rosdep install` — not the build itself.
- **`--symlink-install`**: Python only — edits take effect without rebuilding. C++ always requires a full `colcon build`.
- **`PIP_BREAK_SYSTEM_PACKAGES=1`**: Required in Ubuntu 24.04 (Noble) Dockerfiles; pip refuses
  to install system packages without this env var or a venv.
- **macOS**: Docker Desktop required; no GPU acceleration — use `LIBGL_ALWAYS_SOFTWARE=1`.
  Apple Silicon runs AMD64 emulation; adequate for dev, not for heavy simulation.
- **Windows**: WSL2 backend required; GPU via WSL2 GPU compute (WSLG for GUI).
- **Kilted**: Uses Ubuntu 25.04 (Plucky) as base. Some PPA and apt repo paths differ from Noble.
  Check REP 2000 for platform targets.
- **Mesa / black screen RViz**: Add `kisak/kisak-mesa` PPA to Dockerfile and upgrade mesa packages.
- **`devcontainer.json` `runArgs` quoting**: Each flag and value must be a separate string in the
  array — `"-e", "DISPLAY=..."` not `"-e DISPLAY=..."`.
- **WSL2 display**: Replace X11 socket mount with WSLg display vars. `DISPLAY` is typically `:0`;
  X socket path may differ.
- **Gazebo crash on startup**: Add `--gpus all` (NVIDIA) or set `LIBGL_ALWAYS_SOFTWARE=1` (CPU-only).
