# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reviving a **TurtleBot3 Burger** (Raspberry Pi 4, 4 GB) at Makersmiths using **ROS 2 Jazzy Jalisco** in Docker DevContainers.
See `input/my-vision.md` for full context.

**Current status**: Planning phase — no DevContainer files, workspace, or ROS 2 packages exist yet.
Next step: invoke `ros_devcontainer` skill to scaffold the Docker environment.

### Target Stack

- ROS 2 Jazzy Jalisco
- Docker DevContainers (VS Code Remote Containers)
- Base image: `osrf/ros:jazzy-desktop-full` (GUI/sim dev), `ros:jazzy-ros-base` (headless/CI)
- Primary reference: `docs/RCLPY-From-Zero-To-Hero-1-kwlngi.pdf` pp. 14–23

### Development Phases

1. **ROS2 Base Headless** — `ros:jazzy-ros-base` DevContainer; follow book pp. 14–23
2. **TurtleBot3 DevContainer** — `osrf/ros:jazzy-desktop-full`; full sim + test tooling (Gazebo, RViz, pytest)
3. **Hardware load** — deploy validated packages to physical Burger

### Planned File Layout (post-DevContainer scaffold)

```
turtlebot3/
├── .devcontainer/
│   ├── Dockerfile          # osrf:jazzy-desktop-full + TB3 pkgs + ros_user
│   └── devcontainer.json
├── scripts/
│   ├── build.sh            # docker build
│   ├── run_docker.sh       # start container (GPU auto-detect)
│   ├── attach_terminal.sh
│   └── workspace.sh        # rosdep + colcon build (run inside container)
├── docker-compose.yml      # services: dev, sim, robot
├── entrypoint.sh           # sources ROS on container startup
├── config/params.yaml      # TurtleBot3 node params
└── src/                    # colcon workspace (host-mounted into container)
```

### Container Environment (when running)

- User: `ros_user` (UID 1000; base image `ubuntu` user must be removed first)
- Workspace: `/home/ros_user/ros2_ws`; host `src/` mounted to `ros2_ws/src`
- `TURTLEBOT3_MODEL=burger`, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=0`
- Build image: `sg docker -c "bash scripts/build.sh"` (until re-login after `usermod`)
- Start detached: `sg docker -c "docker run -d --name turtlebot3_dev ... turtlebot3_dev sleep infinity"`
- Attach: `docker exec -it turtlebot3_dev bash`

## Key Documents

| Path | Purpose |
|---|---|
| `input/my-vision.md` | Project goals and phase definitions |
| `docs/RCLPY-From-Zero-To-Hero-1-kwlngi.pdf` | Primary ROS 2 reference (pp. 14–23 for DevContainer setup) |

**Directory conventions**: `input/` = raw author inputs; `docs/` = generated/reference documents.

## Skill Library (`.claude/skills/`)

Invoke these skills via the `Skill` tool or `/<skill-name>` for their respective domains:

| Skill | Use When |
|---|---|
| `ros_devcontainer` | Docker/DevContainer setup, Dockerfile, docker-compose, GUI/VNC, GPU — **invoke first** |
| `ros_workspace` | Scaffold `ros2_ws/`, package layering, vcstool, rosdep, colcon config |
| `ros_architect` | Node graph design, topic/service/action selection, tf2 frames, QoS, lifecycle |
| `ros_package_node` | Create packages, Python (`rclpy`) or C++ (`rclcpp`) nodes, `package.xml`, build files |
| `ros_topics_services_actions` | Implement pub/sub, services, actions, custom msg/srv/action definitions |
| `ros_launch` | Python launch files, parameter loading, multi-node bringup, conditionals |
| `ros_testing` | Unit tests (pytest/GTest), node integration tests, launch system tests |

## Markdown Linting

Config: `.markdownlint-cli2.jsonc` (max line length 300, disabled: MD012 MD022 MD024 MD041 MD045).

```bash
# lint
markdownlint-cli2 "**/*.md"

# lint + auto-fix
markdownlint-cli2 --fix "**/*.md"
```

Run before committing any `.md` files.

## Known Gotchas

- **Docker permission denied**: `jeff` added to `docker` group but session predates `usermod`.
  Prefix commands with `sg docker -c "..."` until a fresh login.
- **`ubuntu` user conflict**: `osrf/ros:jazzy-desktop-full` ships `ubuntu` at UID 1000.
  Dockerfile must `userdel -r ubuntu` before `useradd ros_user`.
- **`docker run -it` in Claude Code**: no TTY in subprocess — start detached with `sleep infinity`, then attach from user's terminal.
- **`ros2 topic list` hangs**: DDS peer discovery blocks. Use `which ros2` or `python3 -c "import rclpy"` to verify ROS without blocking.
