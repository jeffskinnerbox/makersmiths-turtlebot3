# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TurtleBot3 Burger autonomous robot workshop for [Makersmiths](https://makersmiths.org/) makerspace. The goal is to revive a physical TurtleBot3 Burger (RPi 4) by first building a full simulation environment, then deploying to hardware.

**Target stack**: ROS 2 Jazzy, Gazebo Harmonic, Docker, Ubuntu 24.04.

**Two-container architecture**:
- `turtlebot3_simulator` — `osrf/ros:jazzy-desktop-full` + Nav2 + SLAM + Gazebo Harmonic
- `turtlebot3_robot` — `robotis/turtlebot3:jazzy-pc-latest` (amd64) / `jazzy-sbc-latest` (RPi4 arm64)

Both containers use `network_mode: host`, Fast-DDS (`rmw_fastrtps_cpp`), and `GZ_IP=127.0.0.1`.

## Current Project State

**Milestone 1 complete** (2026-03-08). Simulation environment is fully operational.

**What exists**:
- `docker/` — Dockerfile.simulator, Dockerfile.turtlebot, docker-compose.yaml
- `scripts/` — build.sh, run_docker.sh, attach_terminal.sh, workspace.sh, run_tests.sh
- `entrypoint.sh`, `.colcon/defaults.yaml`
- `src/tb3_bringup/` — ament_python package with worlds, config, launch files, tests
- `docs/` — specification, development plan, user-guide-milestone-1
- `.claude/skills/` — ROS 2 domain skills
- `.claude/rules/` — `gotchas.md` (21 known pitfalls) and `git-commit.md`

**Next step**: Milestone 2 — Phase 2.1 gamepad investigation (connect F310, resolve D4/D5).

## Development Methodology

Document-driven, phased approach with test-gates (see `input/README.md` for diagram):
1. Create skills (`SKILL.md`) → domain expertise
2. Vision (`input/my-vision.md`) → specification (`docs/specification.md`) → development plan
3. Execute plan phase by phase; 2-8 test-gates validate each phase before moving on

## Milestones (from `input/my-vision.md`)

1. Docker simulation environment (two containers, Gazebo GUI via X11, turtlebot3_world + turtlebot3_house — AWS warehouse unavailable in apt, R7 materialised)
2. Gamepad control (Logitech F310, e-stop/restart/reboot buttons)
3. Autonomous capabilities (wanderer, patrol, LiDAR monitor, Nav2, SLAM)
4. TMUX monitoring dashboard
5. RPi 4 hardware deployment (RPi ↔ NucBoxM6 via WiFi)

## Key Technical Decisions

- **DDS**: Fast-DDS, not CycloneDDS (hangs on hosts with many bridge/veth interfaces)
- **Bridge**: `ros_gz_bridge` with `geometry_msgs/msg/Twist` on `/cmd_vel` (not `TwistStamped`)
- **Teleop**: `teleop_twist_keyboard` (not `turtlebot3_teleop` which hardcodes `TwistStamped`)
- **SLAM**: `slam_toolbox` online_async; save maps via service call, not `map_saver_cli`
- **Gazebo**: `gz sim` (not `gazebo`); no spawner in gz-sim 8.10 — embed model in world SDF
- **Headless testing**: `headless:=true` on `sim_bringup.launch.py`

## Docker Commands (when containers exist)

```bash
# Build (sg needed until fresh login after docker group add)
sg docker -c "bash scripts/build.sh"

# Start / stop
sg docker -c "bash scripts/run_docker.sh"
docker compose -f docker/docker-compose.yaml down

# Attach interactive terminal (required for teleop, ROS CLI)
bash scripts/attach_terminal.sh turtlebot3_simulator

# Inside container — always source both before ros2 CLI
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash

# Build ROS workspace inside container
cd ~/ros2_ws && colcon build

# Launch simulation (two worlds available)
ros2 launch tb3_bringup sim_bringup.launch.py             # turtlebot3_world (obstacle course)
ros2 launch tb3_bringup sim_house.launch.py               # turtlebot3_house (indoor rooms)
ros2 launch tb3_bringup sim_bringup.launch.py headless:=true  # headless (no GUI)

# Run tests
bash scripts/run_tests.sh all            # headless
bash scripts/run_tests.sh all --gui      # with Gazebo GUI (needs xhost +local:docker)
```

## Actual Repository Layout

```
turtlebot3/
├── docker/
│   ├── Dockerfile.simulator        # osrf/ros:jazzy-desktop-full + deps
│   ├── Dockerfile.turtlebot        # robotis/turtlebot3:jazzy-pc-latest + deps
│   └── docker-compose.yaml         # network_mode: host, both containers
├── scripts/                        # build, run_docker, attach_terminal, workspace, run_tests
├── entrypoint.sh                   # sources ROS + workspace (G17)
├── .colcon/defaults.yaml           # symlink-install, RelWithDebInfo
├── src/
│   ├── tb3_bringup/                # Launch files, worlds, config (ament_python)
│   │   ├── config/bridge_params.yaml
│   │   ├── worlds/tb3_warehouse.world   # turtlebot3_world env + TB3 embedded
│   │   ├── worlds/tb3_house.world       # turtlebot3_house env + TB3 embedded
│   │   └── launch/sim_bringup.launch.py, sim_house.launch.py, teleop.launch.py
│   ├── tb3_controller/             # Wanderer, patrol, gamepad (ament_python) — M2/M3
│   └── tb3_monitor/                # LiDAR monitor, health (ament_python) — M3
├── docs/                           # spec, dev plan, user guides
└── input/                          # vision, prompts, methodology
```

## Critical Gotchas (subset — full list in `.claude/rules/gotchas.md`)

- **No TTY in Claude Code**: never `docker run -it` or interactive `docker exec`. Start detached, user attaches.
- **`ros2 topic list` hangs**: DDS discovery blocks. Verify ROS with `which ros2` or `python3 -c "import rclpy"`.
- **`gz` binary**: at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`, added to PATH in Dockerfiles.
- **`/map` is 0x0 until robot moves**: slam_toolbox publishes empty map initially.
- **Always source both**: `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash` before any `ros2` CLI.

## Key Reference Documents

- **Requirements**: `input/my-vision.md`
- **Specification**: `docs/specification.md` — full system architecture, ROS interfaces table, tf2 frame tree, gotcha cross-references (G1-G21), package specs, and all 5 milestone definitions
- **Gotchas**: `.claude/rules/gotchas.md` — 21 proven pitfalls with workarounds
- **Methodology**: `input/README.md` — document-driven workflow diagram
