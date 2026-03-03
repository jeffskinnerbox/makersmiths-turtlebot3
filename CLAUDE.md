# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reviving a **TurtleBot3 Burger** (Raspberry Pi 4, 4 GB) at Makersmiths using **ROS 2 Jazzy Jalisco** in Docker DevContainers.
See `input/my-vision.md` for full context.

**Current status**: Phase 1 (DevContainer) files created — images need to be built and test gate run. Phase 2 scaffold created. Next: `bash scripts/build.sh` then run Phase 1 test gate.
See [`development-plan.md`](development-plan.md) for full phase plan and living decisions log.

> **Session-start protocol**: At the start of each work session, read `development-plan.md` and update
> phase statuses, D6 (image decision), and the Risk Register per Section 7 of that document.

### Target Architecture: Two-Container System

| Container | Image | Role |
|---|---|---|
| `turtlebot` | `robotis/turtlebot3` | Headless robot controller |
| `simulator` | `osrf/ros:jazzy-desktop-full` | Gazebo, RViz, rqt, full desktop |

Containers communicate over a shared Docker network. The `turtlebot` container runs on the physical Raspberry Pi 4 in production.

### Development Phases

0. **Prerequisites** ⚠️ — D6/R1 resolved; R2 (Gazebo Harmonic compat) + R3 (arm64) still open
1. **DevContainer** ⚠️ — Files created; images not yet built/tested
2. **Workspace scaffold** ❌ — `src/` packages, rosdep, colcon config
3. **Architecture design** ❌ — Node graph, topic contracts, tf2 frame tree
4. **Teleoperation in sim** ❌ — Gazebo Harmonic + keyboard teleop; tests T3, T4
5. **Obstacle avoidance** ❌ — Reactive node using `/scan`
6. **SLAM + map building** ❌ — `slam_toolbox` online async; save map
7. **Autonomous navigation** ❌ — Nav2; test T2
8. **Automated tests** ❌ — T1–T4 pytest suite; JUnit XML
9. **Operational documentation** ❌ — `docs/operations.md` for sim environment
10. **Hardware load** ❌ — Ubuntu 24.04 + Docker on Raspberry Pi 4; arm64 image

### Container Environment

- User: `ros_user` (UID 1000; `ubuntu` user removed in Dockerfile)
- Workspace: `/home/ros_user/ros2_ws`; host `src/` mounted to `ros2_ws/src`
- `TURTLEBOT3_MODEL=burger`, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=0`

### Key Commands

```bash
# Build both images (sg needed until fresh login after docker group usermod)
sg docker -c "bash scripts/build.sh"

# Start both containers (GPU auto-detected)
sg docker -c "bash scripts/run_docker.sh"
# OR: sg docker -c "docker compose up -d"

# Attach shell to simulator
bash scripts/attach_terminal.sh turtlebot3_simulator
# OR: docker exec -it turtlebot3_simulator bash

# Phase 1 test gate
docker exec turtlebot3_turtlebot which ros2   # exits 0
docker exec turtlebot3_simulator which ros2   # exits 0
docker exec turtlebot3_simulator which gz     # exits 0 (Gazebo Harmonic)

# Inside simulator container: build workspace
docker exec turtlebot3_simulator bash /home/ros_user/ros2_ws/scripts/workspace.sh

# Markdown lint (run before committing .md files)
markdownlint-cli2 "**/*.md"
markdownlint-cli2 --fix "**/*.md"
```

## File Layout

```
turtlebot3/
├── .devcontainer/
│   ├── Dockerfile.simulator  # osrf:jazzy-desktop-full + TB3/Nav2/SLAM + ros_user
│   ├── Dockerfile.turtlebot  # robotis/turtlebot3:jazzy + CycloneDDS + ros_user
│   └── devcontainer.json     # VS Code entry (simulator container)
├── .colcon/defaults.yaml     # colcon build defaults (mounted into both containers)
├── scripts/
│   ├── build.sh              # build both images
│   ├── run_docker.sh         # start both containers (GPU auto-detect)
│   ├── attach_terminal.sh    # attach shell to named container
│   └── workspace.sh          # rosdep + colcon build (run inside container)
├── docker-compose.yml        # services: simulator, turtlebot (network_mode: host)
├── entrypoint.sh             # sources ROS + workspace on container startup
├── config/params.yaml        # TurtleBot3 node params
├── input/                    # raw author inputs (vision, prompts)
├── docs/                     # reference documents
├── specification.md          # full project spec: architecture, phases, test criteria
├── development-plan.md       # living dev plan: phases, decisions log, risk register
└── src/                      # colcon workspace (host-mounted into both containers)
    ├── tb3_bringup/          # launch files, configs, RViz (phase 4+)
    └── tb3_controller/       # velocity controller, obstacle avoidance node (phase 5+)
```

## Skill Library (`.claude/skills/`)

Invoke via the `Skill` tool or `/<skill-name>`:

| Skill | Use When |
|---|---|
| `ros_devcontainer` | Docker/DevContainer setup, Dockerfile, docker-compose, GUI/VNC, GPU |
| `ros_workspace` | Scaffold `ros2_ws/`, package layering, vcstool, rosdep, colcon config |
| `ros_architect` | Node graph design, topic/service/action selection, tf2 frames, QoS, lifecycle |
| `ros_package_node` | Create packages, Python (`rclpy`) or C++ (`rclcpp`) nodes, `package.xml`, build files |
| `ros_topics_services_actions` | Implement pub/sub, services, actions, custom msg/srv/action definitions |
| `ros_launch` | Python launch files, parameter loading, multi-node bringup, conditionals |
| `ros_testing` | Unit tests (pytest/GTest), node integration tests, launch system tests |

## Markdown Linting

Config: `.markdownlint-cli2.jsonc` (max line length 300, disabled: MD012 MD022 MD024 MD041 MD045).

## Test Requirements (from `specification.md`)

Non-interactive; run via `docker exec`. pytest + JUnit XML output.

| ID | Test | Pass Criteria |
|----|------|---------------|
| T1 | Container startup | Both containers start; `which ros2` exits 0 |
| T2 | Topic comms | `/scan` published by turtlebot, received by simulator |
| T3 | Gazebo launch | TB3 world loads; `/clock` active |
| T4 | Drive command | Publish `Twist` to `/cmd_vel`; `/odom` changes |

## Known Gotchas

- **Docker permission denied**: `jeff` in `docker` group but session predates `usermod`. Prefix with `sg docker -c "..."` until fresh login.
- **`ubuntu` user conflict**: `osrf/ros:jazzy-desktop-full` ships `ubuntu` at UID 1000. Dockerfile must `userdel -r ubuntu` before `useradd ros_user`.
- **`docker run -it` in Claude Code**: no TTY in subprocess — start detached with `sleep infinity`, then attach from user's terminal.
- **`ros2 topic list` hangs**: DDS peer discovery blocks. Use `which ros2` or `python3 -c "import rclpy"` to verify ROS without blocking.
- **Production networking**: turtlebot container on RPi 4 uses `--network host` (required for DDS multicast across machines on same LAN); simulator stays on desktop.
- **`robotis/turtlebot3` Jazzy tag**: unverified — see D6 in `development-plan.md`. Fallback: `FROM osrf/ros:jazzy-ros-base` + `ros-jazzy-turtlebot3*` apt packages.
- **Gazebo Harmonic**: use `gz sim` (not `gazebo`); `gz_ros2_control` bridge; `ros-jazzy-turtlebot3-gazebo` must have Harmonic-compatible worlds (risk R2).
