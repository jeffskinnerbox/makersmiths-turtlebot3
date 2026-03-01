---
name: ros_devcontainer
description: Create and configure a ROS 2 development Docker container (DevContainer). Use this skill when the user asks to set up a Docker-based ROS 2 development environment, create a DevContainer, write a Dockerfile for ROS 2, configure devcontainer.json for VS Code, set up GUI/display forwarding (X11 or VNC), handle GPU passthrough, run ROS 2 in an isolated containerized workspace, or configure bash helper scripts for container management. Covers three container archetypes: Minimal CLI, Full Desktop, and Custom Project containers. Supports ROS 2 Jazzy, Kilted, and Humble distributions.
---

This skill guides creation and configuration of Docker-based development containers (DevContainers) for ROS 2.
A DevContainer packages the OS, ROS 2 runtime, tools, and workspace into a portable, reproducible environment
— eliminating "it works on my machine" problems across dev machines, robots, and CI systems.

>**Sources:**
> - *RCLPY From Zero to Hero*, Robotics Content Lab (2025), §0.5 "IDE Setup, Containers and Terminal Recap", pages 14–23
> - [The Complete Guide to Docker for ROS 2 Jazzy Projects — Automatic Addison](https://automaticaddison.com/the-complete-guide-to-docker-for-ros-2-jazzy-projects/)
> - [The Complete Beginner's Guide to Using Docker for ROS 2 Deployment (2025) — RobotAir](https://blog.robotair.io/the-complete-beginners-guide-to-using-docker-for-ros-2-deployment-2025-edition-0f259ca8b378)
> - [Introduction to ROS 2 Development with Docker — Docker Official Docs](https://docs.docker.com/guides/ros2/)

---

## 0. Discovery Questions

**Before generating any files, ask the user ALL of the following questions.**
Use the answers to select the correct archetype, base image, GPU flags, display method, and bash scripts to generate.

```
1. Host OS?
   - Linux (Ubuntu 24.04 preferred)
   - macOS (Intel or Apple Silicon)
   - Windows (with WSL2 recommended)

2. ROS 2 distribution?
   - Kilted
   - Jazzy (recommended)
   - Humble

3. GPU type?
   - NVIDIA (needs Container Toolkit)
   - AMD (Linux kernel drivers, no extra install)
   - None / software rendering (LIBGL_ALWAYS_SOFTWARE=1)
   - Unknown

4. GUI tools needed? (RViz, Gazebo, rqt)
   - Yes — full desktop image + X11 or VNC
   - No — headless / CLI only

5. Display method preference? (if GUI = yes)
   - X11 forwarding (Linux native, fastest)
   - VNC browser desktop (Windows, macOS, remote machines)

6. IDE workflow?
   - VS Code DevContainer (.devcontainer/devcontainer.json)
   - Convenience script (run_docker.sh + attach via Docker sidebar)
   - CLI only (manual docker run)

7. Robot / project type?
   - TurtleBot3
   - Custom robot / generic ROS 2 workspace
   - Simulation only (Gazebo / Ignition)
   - CI / deployment (no GUI, minimal image)

8. Hardware device access needed? (real robot, sensors, serial ports)
   - Yes (needs --privileged and /dev mount)
   - No

9. Multi-container setup? (e.g. separate simulator + controller containers)
   - Yes (use docker-compose with YAML anchors)
   - No (single container)
```

### Answer → Archetype Mapping

| Profile | Archetype |
|---------|-----------|
| No GUI, CI / deploy | **A — Minimal CLI** |
| GUI + X11/VNC, no custom packages | **B — Full Desktop** |
| Custom packages, hardware access, multi-container, or named robot project | **C — Custom Project** |

### ROS 2 Distribution → Base Image Prefix

| Distribution | OSRF Image Prefix | Robotics Content Lab Tag |
|---|---|---|
| Jazzy (recommended) | `ros:jazzy-*` / `osrf/ros:jazzy-*` | `jazzy-` |
| Kilted | `ros:kilted-*` / `osrf/ros:kilted-*` | `kilted-` |
| Humble | `ros:humble-*` / `osrf/ros:humble-*` | `humble-` |

> **Note:** Kilted and Humble follow the same Docker patterns as Jazzy.
> Substitute the distro name in all image tags, environment variables (`ROS_DISTRO`), and apt package names (e.g. `ros-humble-*`).

---

## DevContainer Archetypes Overview

| Archetype | Base Image | Use When |
|-----------|-----------|----------|
| **A — Minimal CLI** | `ros:<distro>-ros-base` | Headless deployment, CI, embedded targets |
| **B — Full Desktop** | `osrf/ros:<distro>-desktop-full` | Local dev with RViz, Gazebo, GUI tools |
| **C — Custom Project** | Either + your `Dockerfile` | Adding Nav2, TurtleBot3, hardware, custom packages |

---

## 1. Prerequisites

### Install Docker Engine (Ubuntu 24.04 / Noble)

```bash
# Remove old conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  sudo apt-get remove $pkg
done

# Add Docker's official GPG key and repo
sudo apt-get update && sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Verify
sudo docker run hello-world
docker compose version
```

### Post-install: run Docker as non-root (Linux)

```bash
sudo usermod -aG docker $USER
newgrp docker       # apply immediately without logout
```

> Reference: <https://docs.docker.com/engine/install/linux-postinstall/>

### Install VS Code Extensions

```bash
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-vscode-remote.vscode-remote-extensionpack
```

### Platform Notes

- **macOS / Windows**: Install [Docker Desktop](https://docs.docker.com/get-docker/).
- **Windows**: Enable WSL2 backend — use WSL2 for best performance and GPU support.
- **Intel Mac**: GPU acceleration unsupported in Docker — use `LIBGL_ALWAYS_SOFTWARE=1`.
- **Apple Silicon Mac**: Docker Desktop uses AMD64 emulation for ROS images; performance is adequate for development but not simulation.
- **NVIDIA GPU**: Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
- **AMD GPU**: Drivers are built into the Linux kernel — no extra install required.

---

## 2. Archetype A — Minimal CLI Container

No Dockerfile needed. Pull and run the official base image directly.

```bash
# Replace <distro> with jazzy, kilted, or humble
docker image pull ros:<distro>-ros-base

# Run interactively
docker run -it \
  --name ros2_base \
  --rm \
  ros:<distro>-ros-base

# Attach a second terminal to the running container
docker exec -it ros2_base /bin/bash
```

Inside the container:

```bash
source /opt/ros/<distro>/setup.bash
ros2 --version
```

### When to use Archetype A

- CI / CD pipelines
- Deployment to resource-constrained robots
- Quick testing of individual ROS 2 packages
- No GUI tools required

---

## 3. Archetype B — Full Desktop Container (with GUI)

### X11 Setup (host — run once per login session)

```bash
xhost +local:docker
```

### Standard run (no GPU)

```bash
# Replace <distro> with jazzy, kilted, or humble
docker image pull osrf/ros:<distro>-desktop-full

docker run -it \
  --name ros2_desktop \
  --rm \
  -e DISPLAY=$DISPLAY \
  -e XAUTHORITY=/tmp/.Xauthority \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $HOME/.Xauthority:/tmp/.Xauthority \
  --network host \
  osrf/ros:<distro>-desktop-full
```

### With NVIDIA GPU

```bash
docker run -it \
  --name ros2_desktop_gpu \
  --rm \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -e XAUTHORITY=/tmp/.Xauthority \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $HOME/.Xauthority:/tmp/.Xauthority \
  --network host \
  osrf/ros:<distro>-desktop-full
```

### With AMD GPU

AMD drivers are built into the Linux kernel — no extra install. Use the standard run command above;
DRI/render devices are exposed automatically via the kernel.

### VNC Desktop (browser-based — Windows, macOS, remote)

No X11 socket needed. Access via browser at `http://localhost:6080/`. Default password: **`123456`**.

```bash
# Robotics Content Lab pre-built VNC image
# Tag format: {distro}-{base}-{ui}-{graphics}
docker run -it \
  --name ros2_vnc \
  --rm \
  -p 6080:6080 \
  ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:<distro>-desktop-vnc-standard
```

---

## 4. Archetype C — Custom Project Container (Dockerfile)

### Generated File Layout

When the user chooses Archetype C, generate the following directory structure and all files within it:

```
<project_root>/
├── .devcontainer/
│   ├── devcontainer.json       # VS Code DevContainer spec
│   └── Dockerfile              # Custom image definition
├── config/
│   └── params.yaml             # Robot / node parameters
├── src/                        # colcon workspace source (host-mounted)
├── scripts/
│   ├── build.sh                # Build the Docker image
│   ├── run_docker.sh           # Start the container (with GPU/display auto-detect)
│   ├── attach_terminal.sh      # Attach a new shell to a running container
│   └── workspace.sh            # Inside container: rosdep install + colcon build
├── docker-compose.yml          # Multi-container setup (if answer #9 = Yes)
└── entrypoint.sh               # Container startup: sources ROS before CMD
```

### `.devcontainer/Dockerfile`

```dockerfile
# ── Base ──────────────────────────────────────────────────────────────────────
# For headless/deployment use: ros:<distro>-ros-base
# For local dev with GUI:      osrf/ros:<distro>-desktop-full
ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

# ── System dependencies ───────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
SHELL ["/bin/bash", "-c"]

# Mesa driver update (fixes black-screen RViz on some hosts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
  && add-apt-repository ppa:kisak/kisak-mesa \
  && apt-get update && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/*

# Core tools + project-specific ROS packages
# Adjust ros-${ROS_DISTRO}-* packages to your project needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    build-essential \
    vim \
    tmux \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-turtlebot3* \
  && rm -rf /var/lib/apt/lists/*

# ── Non-root user (match host UID for volume permission alignment) ─────────────
ARG USERNAME=ros_user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

RUN groupadd --gid ${USER_GID} ${USERNAME} \
  && useradd -m --uid ${USER_UID} --gid ${USER_GID} -s /bin/bash ${USERNAME} \
  && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
  && chmod 0440 /etc/sudoers.d/${USERNAME}

# ── Workspace ─────────────────────────────────────────────────────────────────
RUN mkdir -p /home/${USERNAME}/ros2_ws/src \
  && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/ros2_ws

WORKDIR /home/${USERNAME}/ros2_ws

# ── Environment ───────────────────────────────────────────────────────────────
# Adjust ROS_DISTRO, TURTLEBOT3_MODEL, and ROS_DOMAIN_ID to your project
ENV ROS_DISTRO=jazzy
ENV TURTLEBOT3_MODEL=burger
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=0

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/${USERNAME}/.bashrc \
  && echo "source /home/${USERNAME}/ros2_ws/install/setup.bash 2>/dev/null || true" \
     >> /home/${USERNAME}/.bashrc

USER ${USERNAME}

# ── Entrypoint ────────────────────────────────────────────────────────────────
COPY --chown=${USERNAME}:${USERNAME} entrypoint.sh /home/${USERNAME}/entrypoint.sh
RUN chmod +x /home/${USERNAME}/entrypoint.sh
ENTRYPOINT ["/home/ros_user/entrypoint.sh"]
CMD ["bash"]
```

### `entrypoint.sh`

Runs at container startup to source the ROS environment before handing off to the user's command.

```bash
#!/usr/bin/env bash
set -e

source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash

if [ -f /home/ros_user/ros2_ws/install/setup.bash ]; then
  source /home/ros_user/ros2_ws/install/setup.bash
fi

exec "$@"
```

---

## 5. Bash Helper Scripts

Generate these scripts inside `scripts/`. Make all executable with `chmod +x scripts/*.sh`.

### `scripts/build.sh` — Build the Docker image

```bash
#!/usr/bin/env bash
# Usage: ./scripts/build.sh [image_name] [dockerfile_path]
set -e

IMAGE_NAME="${1:-my_robot_image}"
DOCKERFILE="${2:-.devcontainer/Dockerfile}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

echo "Building image: ${IMAGE_NAME} (ROS_DISTRO=${ROS_DISTRO})"
docker build \
  --build-arg ROS_DISTRO="${ROS_DISTRO}" \
  --build-arg USER_UID="$(id -u)" \
  --build-arg USER_GID="$(id -g)" \
  -t "${IMAGE_NAME}" \
  -f "${DOCKERFILE}" \
  .
echo "Done: ${IMAGE_NAME}"
```

### `scripts/run_docker.sh` — Start the container

Supports auto-detection of GPU type, WSL2, and optional hardware device access.

```bash
#!/usr/bin/env bash
# Usage: ./scripts/run_docker.sh [-d <distro>] [-p <profile>] [-t <ui>] [-g <gpu>] [-h]
#   -d  ROS 2 distro (jazzy|kilted|humble)   default: jazzy
#   -p  Base profile  (desktop|base)          default: desktop
#   -t  UI type       (terminal|vnc)          default: terminal
#   -g  GPU platform  (standard|nvidia|amd)   default: auto-detect
#   -h  Show help
set -e

DISTRO="jazzy"
PROFILE="desktop"
UI="terminal"
GPU=""
IMAGE_BASE="ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero"
PRIVILEGED=""

usage() {
  grep '^#' "$0" | grep -v '#!/' | sed 's/^# \?//'
  exit 0
}

while getopts "d:p:t:g:h" opt; do
  case $opt in
    d) DISTRO=$OPTARG ;;
    p) PROFILE=$OPTARG ;;
    t) UI=$OPTARG ;;
    g) GPU=$OPTARG ;;
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

# ── Build docker run args ──────────────────────────────────────────────────────
IMAGE_TAG="${DISTRO}-${PROFILE}-${UI}-${GPU}"
CONTAINER_NAME="ros2_${DISTRO}_${PROFILE}"

GPU_ARGS=""
if [ "$GPU" = "nvidia" ]; then
  GPU_ARGS="--gpus all -e NVIDIA_DRIVER_CAPABILITIES=all"
fi

DISPLAY_ARGS=""
if [ "$UI" = "vnc" ]; then
  DISPLAY_ARGS="-p 6080:6080"
elif [ "$WSL" = true ]; then
  # WSLg uses a different socket path
  DISPLAY_ARGS="-e DISPLAY=${DISPLAY:-:0} -e WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0} -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
else
  xhost +local:docker 2>/dev/null || true
  DISPLAY_ARGS="-e DISPLAY=${DISPLAY} -e XAUTHORITY=/tmp/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v ${HOME}/.Xauthority:/tmp/.Xauthority"
fi

# Uncomment to enable hardware device access (real robot, serial, USB sensors):
# PRIVILEGED="--privileged -v /dev:/dev"

echo "[run_docker] Starting: ${IMAGE_BASE}:${IMAGE_TAG}"
docker run -it --rm \
  --name "${CONTAINER_NAME}" \
  ${GPU_ARGS} \
  ${DISPLAY_ARGS} \
  ${PRIVILEGED} \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}" \
  -e RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}" \
  -v "$(pwd)/src:/home/ros_user/ros2_ws/src" \
  --network host \
  --ipc host \
  "${IMAGE_BASE}:${IMAGE_TAG}"
```

### `scripts/attach_terminal.sh` — Attach a shell to a running container

```bash
#!/usr/bin/env bash
# Usage: ./scripts/attach_terminal.sh [container_name_filter]
set -e

FILTER="${1:-ros2}"
CONTAINER=$(docker ps --filter "name=${FILTER}" --format "{{.Names}}" | head -1)

if [ -z "$CONTAINER" ]; then
  echo "No running container matching filter '${FILTER}' found."
  echo "Running containers:"
  docker ps --format "  {{.Names}}"
  exit 1
fi

echo "Attaching to: ${CONTAINER}"
docker exec -it "${CONTAINER}" bash
```

### `scripts/workspace.sh` — Install deps and build (run inside container)

```bash
#!/usr/bin/env bash
# Run INSIDE the container to install rosdep deps and build the workspace.
# Usage: ./scripts/workspace.sh [--clean]
set -e

WS_ROOT="${HOME}/ros2_ws"
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

---

## 6. VS Code DevContainer (`.devcontainer/devcontainer.json`)

Place in `.devcontainer/` at the project root. VS Code will prompt **"Reopen in Container"** automatically when the folder is opened.

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

  // X11 forwarding (Linux). For VNC: remove these and expose port 6080 instead.
  "runArgs": [
    "-e", "DISPLAY=${localEnv:DISPLAY}",
    "-e", "XAUTHORITY=/tmp/.Xauthority",
    "-v", "/tmp/.X11-unix:/tmp/.X11-unix:rw",
    "-v", "${localEnv:HOME}/.Xauthority:/tmp/.Xauthority",
    "--network", "host",
    "--ipc", "host"
    // Add "--gpus", "all" here for NVIDIA GPU support
    // Add "--privileged" and "-v", "/dev:/dev" for hardware device access
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

### Starting the DevContainer

1. Install the Remote Development Extension:

   ```bash
   code --install-extension ms-vscode-remote.vscode-remote-extensionpack
   ```

2. Open the project folder in VS Code.
3. Open via:
   - **Command Palette** (`F1`) → `Dev Containers: Reopen in Container`
   - **Blue button** bottom-left → `Reopen in Container`

### Adapting `devcontainer.json` (key variables)

| Variable | Options | Default |
|---|---|---|
| `ROS_DISTRO` (build arg) | `jazzy`, `kilted`, `humble` | `jazzy` |
| `ROS_DOMAIN_ID` | `0`–`101` | `0` |
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp`, `rmw_fastrtps_cpp` | `rmw_cyclonedds_cpp` |
| `TURTLEBOT3_MODEL` | `burger`, `waffle`, `waffle_pi` | `burger` |

### Attaching VS Code to a Running Container (convenience script workflow)

When using `run_docker.sh` instead of DevContainer:

1. VS Code → **Docker icon** in sidebar
2. Under **Individual Containers**, right-click your container → **Attach Visual Studio Code**
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

5. `Ctrl+Shift+P` → `Developer: Reload Window`

---

## 7. Docker Compose (Multi-Container)

Use when answer #9 = Yes. YAML anchors (`&anchor` / `<<: *anchor`) share config across services.

```yaml
# docker-compose.yml
x-ros-base: &ros-base
  image: my_robot_image:latest
  ipc: host                   # required for DDS shared-memory transport
  network_mode: host          # required for ROS 2 DDS discovery
  privileged: true            # needed for hardware device access; scope to specific device if possible
  environment:
    - DISPLAY
    - XAUTHORITY=/tmp/.Xauthority
    - ROS_DISTRO=jazzy
    - ROS_DOMAIN_ID=0
    - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    - TURTLEBOT3_MODEL=burger
  volumes:
    - /tmp/.X11-unix:/tmp/.X11-unix:rw
    - $HOME/.Xauthority:/tmp/.Xauthority
    - ./src:/home/ros_user/ros2_ws/src
    - /dev:/dev               # full device access; scope to /dev/ttyUSB0 if possible

services:
  robot:
    <<: *ros-base
    container_name: ros2_robot
    stdin_open: true
    tty: true
    command: bash -c "source /opt/ros/jazzy/setup.bash && bash"

  simulator:
    <<: *ros-base
    container_name: ros2_sim
    command: bash -c "source /opt/ros/jazzy/setup.bash && ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py"

  # Minimal DDS verification pair:
  talker:
    <<: *ros-base
    command: ["ros2", "run", "demo_nodes_cpp", "talker"]

  listener:
    <<: *ros-base
    command: ["ros2", "run", "demo_nodes_cpp", "listener"]
```

```bash
xhost +local:docker
docker compose up -d                    # start all services
docker compose exec robot bash          # attach shell to robot service
docker compose stop                     # stop (preserves state)
docker compose down                     # stop + remove containers
```

---

## 8. Official Image Tags Reference

### OSRF base images

| Image | Contents | Best For |
|-------|----------|----------|
| `ros:<distro>-ros-core` | DDS + ROS graph only | Ultra-minimal deployment |
| `ros:<distro>-ros-base` | Core + comm libs | Headless nodes, CI |
| `ros:<distro>` | Alias for `-ros-base` | General base |
| `osrf/ros:<distro>-desktop` | Base + RViz + tools | Dev with GUI |
| `osrf/ros:<distro>-desktop-full` | Full desktop + demos | Full local dev |

### Robotics Content Lab pre-built images

Tag convention (from §0.5.5 of the book):

```
ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:{ROS2-VERSION}-{ROS-BASE}-{UI}-{GRAPHICS-PLATFORM}
```

| Field | Options |
|---|---|
| `ROS2-VERSION` | `jazzy`, `iron`, `humble` |
| `ROS-BASE` | `desktop`, `base` |
| `UI` | `terminal` (Tmux, lighter) · `vnc` (browser desktop) |
| `GRAPHICS-PLATFORM` | `standard` · `nvidia` · `amd` |

Example: `ghcr.io/robotics-content-lab/rclpy-from-zero-to-hero:jazzy-desktop-terminal-nvidia`

---

## 9. Day-to-Day Workflow

### Starting up

```bash
# Convenience script
bash scripts/run_docker.sh -d jazzy -p desktop -t terminal

# Docker Compose
xhost +local:docker
docker compose up -d

# VS Code: open project → "Reopen in Container" prompt appears automatically
```

### Build workspace (inside container)

```bash
cd ~/ros2_ws
bash /path/to/scripts/workspace.sh        # rosdep install + colcon build
# or manually:
source /opt/ros/jazzy/setup.bash
rosdep update && rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

### Open additional terminals

```bash
bash scripts/attach_terminal.sh           # auto-finds running ros2 container
docker exec -it <container_name> bash     # direct
docker compose exec robot bash            # via compose
```

### Common ROS 2 commands (inside container)

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 run <package> <executable>
ros2 launch <package> <launch_file>.launch.py
ros2 topic list
ros2 topic echo /cmd_vel
ros2 node list
ros2 param list
rviz2
```

### Stopping

```bash
docker compose stop           # stop, preserve state
docker compose down           # stop + remove containers (image remains)
docker stop <container_name>
```

> **Data persistence**: Only the host-mounted `src/` folder survives container removal. All in-container changes (installed packages, build artifacts) are lost on `docker rm`. Always keep source files in `src/`.

---

## 10. Jazzy / Kilted / Humble Gotchas

- **`xhost +local:docker` resets on reboot**: Re-run each session, or add to `~/.bashrc`.
- **`XAUTHORITY` passthrough**: Mount `$HOME/.Xauthority:/tmp/.Xauthority` and set `-e XAUTHORITY=/tmp/.Xauthority` for reliable X11 auth with display managers (GDM/SDDM).
- **Volume ownership**: Container non-root user must match host UID (`1000`). Pass `--build-arg USER_UID=$(id -u)` to `docker build`.
- **`ipc: host`**: Required alongside `network_mode: host` for DDS shared-memory transport.
- **`network_mode: host`**: Required for ROS 2 DDS discovery. Without it, `ros2 topic list` may show nothing.
- **`ROS_DOMAIN_ID`**: All nodes that must communicate must share the same domain ID.
- **`privileged: true`**: Needed for real hardware. Scope to specific devices (`--device /dev/ttyUSB0`) to reduce security surface.
- **`source install/setup.bash`**: Must be sourced after every `colcon build`. `postCreateCommand` handles `rosdep install` — not the build.
- **Gazebo crash on startup**: Add `--gpus all` (NVIDIA) or set `LIBGL_ALWAYS_SOFTWARE=1` (CPU-only, slow but functional).
- **`--symlink-install`**: Python only — edits take effect without rebuilding. C++ always requires a full rebuild.
- **Mesa / black screen RViz**: Add `kisak/kisak-mesa` PPA to Dockerfile and upgrade mesa packages.
- **`devcontainer.json` `runArgs` quoting**: Each flag and value must be a separate string in the array — `"-e", "DISPLAY=..."` not `"-e DISPLAY=..."`.
- **WSL2 display**: Replace X11 socket mount with WSLg display vars. `DISPLAY` is typically `:0`, X socket may be at a different path.
- **`PIP_BREAK_SYSTEM_PACKAGES=1`**: Required in Ubuntu 24.04 (Noble) Dockerfiles; pip refuses to install system packages otherwise without this env var or a venv.
- **Kilted**: Uses Ubuntu 25.04 (Plucky) as its base. Some PPA and apt repo paths differ from Noble. Check `REP 2000` for platform targets.

---

## 11. Troubleshooting Checklist

- **Permission denied running docker**: `sudo usermod -aG docker $USER` then log out/in.
- **Port / name conflict**: `docker ps -a` — another container may already hold the name or port. Use `docker rm <name>` to clear.
- **Container runtime not running**: Linux: `sudo systemctl start docker`; Windows/macOS: open Docker Desktop.
- **GUI apps not rendering (black window)**: Run `xhost +local:docker`; try `LIBGL_ALWAYS_SOFTWARE=1`; try mesa PPA update in Dockerfile.
- **Windows — GUI apps not rendering**: Enable WSLg: <https://docs.microsoft.com/en-us/windows/wsl/tutorials/gui-apps>
- **VNC not accessible**: Confirm `-p 6080:6080` in run args, no firewall blocking port 6080. Default password: `123456`.
- **`ros2 topic list` shows nothing**: Verify `--network host` and `ipc: host`; all containers share same `ROS_DOMAIN_ID`; check `RMW_IMPLEMENTATION` matches.
- **`rosdep install` fails**: Run `rosdep update` first; confirm `src/` is mounted and `package.xml` files are present.
- **`colcon build` fails "package not found"**: Source `/opt/ros/<distro>/setup.bash` before building.
- **C++ rebuild needed after source edit**: `--symlink-install` does not apply to C++. Always `colcon build` after C++ changes.
- **NVIDIA: `--gpus` flag not recognised**: NVIDIA Container Toolkit not installed. See <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html>
- **`entrypoint.sh` permission denied**: File must be executable. Run `chmod +x entrypoint.sh` on the host before building the image.
