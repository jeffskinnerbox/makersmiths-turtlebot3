# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reviving a **TurtleBot3 Burger** (Raspberry Pi 4, 4 GB) at Makersmiths using **ROS 2 Jazzy Jalisco** in Docker DevContainers.
See `input/my-vision.md` for full context.

**Current status**: Phase 0 ✅, Phase 1 ✅, Phase 2 ✅, Phase 3 ✅, Phase 4 ✅ (T3+T4 passed 2026-03-05). Next: Phase 5 — obstacle avoidance.
See [`development-plan.md`](development-plan.md) for full phase plan and living decisions log.

**Session-start protocol** — at the start of each work session:
1. Read `development-plan.md`.
2. Update phase statuses, D6 (image decision), and the Risk Register per Section 7 of that document.

### Target Architecture: Two-Container System

| Container | Image | Role |
|---|---|---|
| `turtlebot` | `robotis/turtlebot3` | Headless robot controller |
| `simulator` | `osrf/ros:jazzy-desktop-full` | Gazebo, RViz, rqt, full desktop |

Containers communicate over a shared Docker network. The `turtlebot` container runs on the physical Raspberry Pi 4 in production.

### Development Phases

0. **Prerequisites** ✅ — D6/R1/R2 resolved; R3 (arm64) deferred to Phase 10
1. **DevContainer** ✅ — T1 passed 2026-03-03; gz at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`
2. **Workspace scaffold** ✅ — `src/` packages, rosdep, colcon config (2026-03-03)
3. **Architecture design** ✅ — Node graph, topic contracts, tf2 frame tree (`docs/architecture.md`)
4. **Teleoperation in sim** ✅ — T3+T4 passed 2026-03-05; GZ_IP+Fast-DDS fixes required
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

# Phase 4: launch sim headless (no display; required for docker exec testing)
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup sim_bringup.launch.py headless:=true &"

# Phase 4: launch sim with GUI (interactive; from attached terminal)
# ros2 launch tb3_bringup sim_bringup.launch.py use_rviz:=true

# T3 test gate: Gazebo world loads; /clock active
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup sim_bringup.launch.py headless:=true &
  sleep 15 && ros2 topic list | grep /clock"

# T4 test gate: publish /cmd_vel; verify /odom changes
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  python3 ~/ros2_ws/scripts/test_t4.py"

# Phase 4: keyboard teleop (MUST be from attached terminal — needs TTY)
bash scripts/attach_terminal.sh turtlebot3_simulator
# then inside: ros2 launch tb3_bringup teleop.launch.py

# Phase 5+: teleop remapped so obstacle_avoidance_node can intercept
# ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw

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
│   ├── workspace.sh          # rosdep + colcon build (run inside container)
│   └── test_t4.py            # T4 test: publish /cmd_vel, verify /odom changes (run inside container)
├── docker-compose.yml        # services: simulator, turtlebot (network_mode: host)
├── entrypoint.sh             # sources ROS + workspace on container startup
├── config/params.yaml        # TurtleBot3 node params
├── input/                    # raw author inputs (vision, prompts)
├── specification.md          # full project spec: architecture, phases, test criteria
├── development-plan.md       # living dev plan: phases, decisions log, risk register
├── docs/
│   └── architecture.md       # Phase 3 deliverable: node graph, topic contracts, tf2 frames
└── src/                      # colcon workspace (host-mounted into both containers)
    ├── tb3_bringup/
    │   ├── launch/
    │   │   ├── sim_bringup.launch.py   # Gazebo Harmonic + TB3 + robot_state_publisher; headless:=true for tests
    │   │   └── teleop.launch.py        # turtlebot3_teleop_keyboard; cmd_vel_topic arg for Ph5 remap
    │   ├── config/
    │   │   ├── gazebo_params.yaml      # use_sim_time: true (wildcard for all nodes)
    │   │   └── bridge_params.yaml      # gz_ros2_bridge: /cmd_vel as Twist (not TwistStamped)
    │   ├── rviz/teleop.rviz
    │   └── worlds/tb3_sim.world        # embeds TB3 burger model directly (no spawner service needed)
    └── tb3_controller/       # velocity controller, obstacle avoidance node (phase 5+)
```

## Skill Library (`.claude/skills/`)

Invoke via the `Skill` tool or `/<skill-name>`:

| Skill | Use When |
|---|---|
| `ros_workspace` | Scaffold `ros2_ws/`, package layering, vcstool, rosdep, colcon config |
| `ros_architect` | Node graph design, topic/service/action selection, tf2 frames, QoS, lifecycle |
| `ros_package_node` | Create packages, Python (`rclpy`) or C++ (`rclcpp`) nodes, `package.xml`, build files |
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
- **`robotis/turtlebot3` tag**: `jazzy` tag does NOT exist. Use `jazzy-pc-latest` (dev/amd64) or `jazzy-sbc-latest` (RPi4/arm64).
- **`gz` binary path**: not in standard PATH — at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`. Both Dockerfiles add it via `ENV PATH`.
- **Gazebo Harmonic**: use `gz sim` (not `gazebo`); `gz_ros2_control` bridge; `ros-jazzy-turtlebot3-gazebo` must have Harmonic-compatible worlds (risk R2).
- **gz-sim 8.10 spawner removed**: `/world/default/create` service no longer exists in gz-sim 8.10. Embed the TB3 model directly in the world SDF (`worlds/tb3_sim.world`) instead of using `ros_gz_sim` spawner.
- **`/cmd_vel` bridge type**: upstream `turtlebot3_gazebo` bridge uses `TwistStamped`; our `bridge_params.yaml` overrides to `geometry_msgs/msg/Twist` — required for `teleop_keyboard`, `obstacle_avoidance_node`, and Nav2.
- **`teleop_keyboard` needs TTY**: `turtlebot3_teleop_keyboard` is interactive. Never launch via non-interactive `docker exec`. Use `bash scripts/attach_terminal.sh turtlebot3_simulator`, then run `ros2 launch tb3_bringup teleop.launch.py` from within that session.
- **headless sim for testing**: pass `headless:=true` to `sim_bringup.launch.py` when launching via `docker exec` (no display). The gz sim server still runs and publishes `/clock`; only the GUI client is skipped.
- **CycloneDDS hangs on hosts with many bridge/veth interfaces**: `rclpy.init()` blocks joining multicast groups. Switched to `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (Fast-DDS). Both packages are installed in the image.
- **gz-transport also uses multicast for discovery**: `GZ_IP=127.0.0.1` forces gz-transport to use loopback, fixing the bridge connection between Gazebo and `ros_gz_bridge`. Set in docker-compose.yml.
- **`scripts/` is mounted into the container**: `./scripts` → `~/ros2_ws/scripts`. Run `test_t4.py` as `python3 ~/ros2_ws/scripts/test_t4.py` inside the container.
