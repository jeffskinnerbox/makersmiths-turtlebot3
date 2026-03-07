# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Orientation

ROS 2 Jazzy simulation of a TurtleBot3 Burger in two Docker containers:

| Container | Image base | Role |
|---|---|---|
| `turtlebot3_simulator` | `osrf/ros:jazzy-desktop-full` | Gazebo Harmonic, RViz, test runner |
| `turtlebot3_robot` | `robotis/turtlebot3:jazzy-pc-latest` | Headless robot node (RPi4 in prod) |

Both use `network_mode: host` and `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`. Detailed guidance is in `.claude/CLAUDE.md` (auto-loaded); rules in `.claude/rules/commands.md` and `.claude/rules/gotchas.md`.

**Session-start**: read `development-plan.md`, update phase statuses, then update the status line in `.claude/CLAUDE.md`.

## Essential Commands

```bash
# Build images
sg docker -c "bash scripts/build.sh"

# Start containers
sg docker -c "docker compose up -d"

# Attach interactive shell (needed for TTY-dependent tools like teleop)
bash scripts/attach_terminal.sh turtlebot3_simulator

# Build ROS workspace inside container
docker exec turtlebot3_simulator bash /home/ros_user/ros2_ws/scripts/workspace.sh

# Run full test suite (host-side; manages docker restart + JUnit XML output)
bash scripts/run_tests.sh all                      # headless (CI-safe)
bash scripts/run_tests.sh all --gui                # with Gazebo GUI on host display
bash scripts/run_tests.sh sim|obstacle|slam|nav2   # individual stages
# --gui requires: xhost +local:docker (once per login)

# Markdown lint
markdownlint-cli2 "**/*.md"
markdownlint-cli2 --fix "**/*.md"
```

## Architecture

### ROS Node Graph

```
/scan (LaserScan)  ──►  obstacle_avoidance_node  ──►  /cmd_vel (Twist)
                                                         │
/cmd_vel_raw  ────────────────────────────────────────►  │  (passthrough when clear)
                                                         ▼
                                              gz_ros2_bridge  ──► Gazebo diff-drive
                                                         │
/odom  ◄─────────────────────────────────────────────────
/tf    ◄─────────────────────────────────────────────────
```

Nav2 publishes directly to `/cmd_vel`; do **not** run `obstacle_avoidance.launch.py` alongside Nav2.

### Launch File Stack (in `src/tb3_bringup/launch/`)

| Launch file | What it starts |
|---|---|
| `sim_bringup.launch.py` | Gazebo Harmonic + TB3 world + `robot_state_publisher` + `ros_gz_bridge` |
| `teleop.launch.py` | `teleop_twist_keyboard` (needs TTY; use `i/,/j/l` keys) |
| `obstacle_avoidance.launch.py` | `obstacle_avoidance_node` (sub `/cmd_vel_raw`, pub `/cmd_vel`) |
| `slam.launch.py` | `sim_bringup` + `slam_toolbox` online_async |
| `nav2_bringup.launch.py` | `sim_bringup` + Nav2 stack (map_server + amcl + planners + bt_navigator) |

All test launches require `headless:=true` when run via `docker exec`.

### Key Config Files

| File | Purpose |
|---|---|
| `src/tb3_bringup/config/bridge_params.yaml` | `/cmd_vel` bridged as `Twist` (not `TwistStamped`) |
| `src/tb3_bringup/config/slam_params.yaml` | `slam_toolbox` tuned for TB3 Burger |
| `src/tb3_bringup/config/nav2_params.yaml` | Nav2 tuned for TB3 footprint + speeds |
| `src/tb3_bringup/config/maps/` | Pre-built map (`phase6_map.pgm` + `.yaml`) |
| `src/worlds/tb3_sim.world` | TB3 model embedded directly (no spawner service) |

### Test Suite (Phase 8, `src/tb3_bringup/test/`)

Tests are pytest files run via `scripts/run_tests.sh`. Each stage restarts the container for a clean Gazebo instance. Results: `./test-results/results_<stage>.xml`.

| ID | File | What it verifies |
|----|------|-----------------|
| T1 | `test_t1_container_startup.py` | `which ros2`, `which gz` exit 0 |
| T2 | `test_t2_topic_comms.py` | xfail (Phase 10, needs real hardware) |
| T3 | `test_t3_gazebo_launch.py` | `/clock` published after sim starts |
| T4 | `test_t4_drive_command.py` | `/cmd_vel` pub causes `/odom` change |
| T5 | `test_t5_obstacle_avoidance.py` | Forward blocked; reverse passes |
| T6 | `test_t6_slam.py` | `/map` non-empty after robot moves |
| T7 | `test_t7_nav2.py` | Nav2 goal `(0.15, 0.10)` SUCCEEDED |

## Critical Gotchas (highlights — full list in `.claude/rules/gotchas.md`)

- `sg docker -c "..."` required until fresh login after `usermod` adds jeff to docker group.
- Always source both setups: `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash`
- Save SLAM maps via `slam_toolbox` service, not `map_saver_cli` (QoS mismatch).
- Map save path must be outside `src/` inside the container (save to `~/`, then `cp` to `src/`).
- `docker restart turtlebot3_simulator` before nav2 tests — lingering `gz sim` processes corrupt TF.
- Nav2 map bounds: `phase6_map` is 12×12 cells @ 0.05 m; goal `(0.15, 0.10)` works; `(0.5, 0.0)` is out of bounds.
- `turtlebot3_teleop` v2.3.6 hardcodes `TwistStamped`; bridge expects `Twist` — silent drop. Use `teleop_twist_keyboard` instead (already set in `teleop.launch.py`). Manual: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`.
