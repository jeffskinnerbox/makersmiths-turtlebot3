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

**Next step**: see `docs/development-plan.md` for current phase and status.

**Package build order**: `tb3_monitor` → `tb3_controller` → `tb3_bringup` (tb3_monitor has no in-project deps; tb3_bringup launch files reference both).

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
- **Gamepad**: `ros-jazzy-joy` uses SDL2 — needs `/dev/input` bind-mount + `device_cgroup_rules: ["c 13:* rmw"]` + `group_add: ["102"]`; `joy_node` must have `use_sim_time: False`
- **E-stop**: teleop → `/cmd_vel_raw` → `gamepad_manager` → `/cmd_vel`; B=stop, A=clear, Y=shutdown
- **F310 (D-mode) mapping**: axis[0]=Left-X(yaw), axis[4]=Right-Y(linear); btn[0]=A(clear), btn[1]=B(estop), btn[3]=Y(shutdown); RB (btn[5]) is deadman hold
- **Nav2 with slam_toolbox**: use `navigation_launch.py` (not `bringup_launch.py`) — no AMCL/map_server needed; slam_toolbox provides map→odom TF and `/map`
- **Wanderer e-stop**: subscribes `/estop` with `RELIABLE+TRANSIENT_LOCAL`; defaults `_estop=False` so robot wanders without gamepad running

## Session Start Convention

At the start of each work session, Claude Code should:
1. Read `docs/development-plan.md` to determine current phase and status
2. Read the Decisions Log within that doc for prior decisions
3. Execute the current phase's deliverables and test-gates
4. Update status markers and logs before ending the session

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

# Run a single pytest test file (no ROS running needed for unit tests)
# NOTE: run these inside the container (docker exec), not on the host
python3 -m pytest src/tb3_controller/test/test_wanderer_logic.py -q --tb=short

# Run a single named test (test files live at src/<pkg>/test/test_*.py)
python3 -m pytest src/tb3_monitor/test/ -q -k 'test_min_distance'

# colcon uses symlink-install (.colcon/defaults.yaml): Python *.py node files are
# symlinked from install/ → src/, so edits take effect immediately without rebuild.
# Exception: entry-point wrapper scripts (ros2 run ...) ARE generated files and
# require a rebuild when adding/removing console_scripts in setup.py.

# ros2 run entry points (after colcon build):
#   ros2 run tb3_monitor lidar_monitor
#   ros2 run tb3_monitor health_monitor
#   ros2 run tb3_monitor mock_battery
#   ros2 run tb3_monitor tf2_verifier
#   ros2 run tb3_controller gamepad_manager
#   ros2 run tb3_controller wanderer
#   ros2 run tb3_controller patrol
#   ros2 run tb3_controller scan_action_server

# Launch simulation (two worlds available)
ros2 launch tb3_bringup sim_bringup.launch.py             # turtlebot3_world (obstacle course)
ros2 launch tb3_bringup sim_house.launch.py               # turtlebot3_house (indoor rooms)
ros2 launch tb3_bringup sim_bringup.launch.py headless:=true  # headless (no GUI)

# M3 autonomous launches (run alongside sim_bringup):
ros2 launch tb3_bringup wanderer.launch.py    # lidar_monitor + wanderer
ros2 launch tb3_bringup slam.launch.py        # slam_toolbox online_async → /map
ros2 launch tb3_bringup nav2.launch.py        # Nav2 stack (needs slam for map→odom TF)
ros2 launch tb3_bringup capability_demo.launch.py            # patrol mode (default)
ros2 launch tb3_bringup capability_demo.launch.py mode:=wanderer  # wanderer mode

# Run tests — subcommands: m1, m2, m3, all (headless by default)
bash scripts/run_tests.sh all            # all milestones, headless
bash scripts/run_tests.sh m2 --gui      # M2 only, with Gazebo GUI (needs xhost +local:docker)

# Run a single pytest test (inside container)
docker exec turtlebot3_simulator bash -c \
  "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && \
   python3 -m pytest src/tb3_bringup/test/ -q -k 'test_name'"
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
│   │   ├── config/teleop_twist_joy.yaml # Joystick axis/button mapping
│   │   ├── config/slam_params.yaml      # slam_toolbox online_async (M3)
│   │   ├── config/nav2_params.yaml      # Nav2 tuned for TB3 Burger (M3)
│   │   ├── worlds/tb3_warehouse.world   # turtlebot3_world env + TB3 embedded
│   │   ├── worlds/tb3_house.world       # turtlebot3_house env + TB3 embedded
│   │   └── launch/sim_bringup.launch.py, sim_house.launch.py, teleop.launch.py,
│   │           gamepad.launch.py, wanderer.launch.py, slam.launch.py, nav2.launch.py,
│   │           capability_demo.launch.py
│   ├── tb3_controller/             # Gamepad manager + autonomous behaviors (ament_python)
│   │                               # M2: gamepad_manager_node
│   │                               # M3: wanderer_node, patrol_node, scan_action_server
│   └── tb3_monitor/                # Monitoring nodes (ament_python)
│                                   # M3: lidar_monitor_node, health_monitor_node,
│                                   #     mock_battery (simulates /battery_state),
│                                   #     tf2_verifier (debug/test tool — verifies TF2
│                                   #       frame connectivity, not a production node)
├── docs/                           # spec, dev plan, user guides
└── input/                          # vision, prompts, methodology
```

## Critical Gotchas (subset — full list in `.claude/rules/gotchas.md`)

- **No TTY in Claude Code**: never `docker run -it` or interactive `docker exec`. Start detached, user attaches.
- **`ros2 topic list` hangs**: DDS discovery blocks. Verify ROS with `which ros2` or `python3 -c "import rclpy"`.
- **`gz` binary**: at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`, added to PATH in Dockerfiles.
- **`/map` is 0x0 until robot moves**: slam_toolbox publishes empty map initially.
- **Always source both**: `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash` before any `ros2` CLI.
- **`async_slam_toolbox_node` is a lifecycle node**: spawning it with `Node()` leaves it unconfigured (no `/scan` sub, no `/map` pub). Use slam_toolbox's `online_async_launch.py` which handles CONFIGURE→ACTIVATE automatically.
- **`ros2 service call` without `timeout` hangs**: if the service is unavailable, call blocks forever. Always prefix with `timeout 20 ros2 service call ...` in scripts.

## Key Reference Documents

- **Requirements**: `input/my-vision.md`
- **Specification**: `docs/specification.md` — full system architecture, ROS interfaces table, tf2 frame tree, gotcha cross-references (G1–G29), package specs, and all 5 milestone definitions
- **Development Plan**: `docs/development-plan.md` — living document; phase status, decisions log, change log
- **Gotchas**: `.claude/rules/gotchas.md` — 29 proven pitfalls with workarounds (G29: stale FastRTPS SHM)
- **Methodology**: `input/README.md` — document-driven workflow diagram
- **M3 User Guide**: `docs/user-guide-milestone-3.md` — launch commands, topic reference, troubleshooting for wanderer/patrol/SLAM/Nav2/health monitoring
