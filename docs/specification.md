# TurtleBot3 Autonomous Robot Workshop — System Specification

* **Version**: 1.0
* **Date**: 2026-03-07
* **Author**: Jeff (vision & requirements) + Claude Code (specification)
* **Status**: Draft

> This specification was generated from the project vision (`input/my-vision.md`)
> through a structured clarification process. The original prompt, all questions asked,
> and user responses are recorded in [Appendix A](#appendix-a-original-prompt-and-clarification-qa).

---

## 1. Introduction

This document translates the project vision into an actionable specification for the
TurtleBot3 Autonomous Robot Workshop at Makersmiths makerspace. It serves as the
authoritative requirements reference from which a detailed development plan will be derived.

**Audience**: Claude Code (primary developer), Jeff (reviewer and operator).

**Scope**: Five milestones covering Docker-based simulation, gamepad control,
autonomous capabilities, monitoring, and hardware deployment of a TurtleBot3 Burger.

**Constraints approach**: This specification carries forward known technical gotchas
from prior development sessions (catalogued in Section 4 and [Appendix B](#appendix-b-known-gotchas-reference))
as proven constraints. All other design decisions are made fresh.

---

## 2. Project Overview

### 2.1 Mission Statement

Revive a TurtleBot3 Burger (RPi 4, 4GB) at Makersmiths makerspace with a Docker-based,
simulation-first development approach using ROS 2 Jazzy and Gazebo Harmonic, culminating
in a visitor-friendly demonstration system operable by non-technical Makersmiths members.

### 2.2 Stakeholders

| Stakeholder | Role |
|---|---|
| Jeff | Developer, operator, project owner |
| Makersmiths members | Demo operators (non-technical) |
| Guest visitors | Observers of demonstrations |

### 2.3 Target Platform

| Component | Specification |
|---|---|
| Host OS (development) | Ubuntu 24.04 LTS |
| ROS distribution | Jazzy Jalisco |
| Simulator | Gazebo Harmonic (`gz sim`) |
| Gazebo world | `turtlebot3_world` (obstacle course) + `turtlebot3_house` (indoor) — AWS warehouse unavailable in apt (R7 materialised) |
| DDS middleware | Fast-DDS (`rmw_fastrtps_cpp`) |
| Container runtime | Docker + docker-compose |
| Robot hardware | TurtleBot3 Burger, Raspberry Pi 4 (4GB RAM) |
| Gamepad | [Logitech F310][f310] |
| Network (deployment) | [GL.iNet GL-AXT1800][glinet] travel router, SSID "JeffTravelRouter-2.4" |
| Development machine | NucBoxM6 (Ubuntu 24.04) |

[f310]: https://www.logitechg.com/en-us/shop/p/f310-gamepad
[glinet]: https://store-us.gl-inet.com/products/slate-ax-gl-axt1800-gigabit-wireless-router

### 2.4 Development Methodology

The project follows a phased build approach with **test-gates** — two to eight tests
performed at the end of each phase. A phase cannot be considered complete until all
test-gates pass. Each milestone produces a user guide enabling manual test repetition.

---

## 3. System Architecture

### 3.1 Two-Container Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Host: Ubuntu 24.04                          │
│                                                                    │
│  ┌──────────────────────────┐    ┌──────────────────────────────┐  │
│  │   turtlebot3_simulator   │    │      turtlebot3_robot        │  │
│  │                          │    │                              │  │
│  │  FROM osrf/ros:jazzy-    │    │  FROM robotis/turtlebot3:    │  │
│  │    desktop-full          │    │    jazzy-pc-latest (amd64)   │  │
│  │                          │    │    jazzy-sbc-latest (arm64)  │  │
│  │  • Gazebo Harmonic       │    │                              │  │
│  │  • Nav2                  │    │  • TurtleBot3 packages       │  │
│  │  • slam_toolbox          │    │  • Motor drivers             │  │
│  │  • ros_gz_bridge         │    │  • Sensor drivers            │  │
│  │  • teleop / joy          │    │  • OpenCR firmware interface │  │
│  │  • RViz2                 │    │                              │  │
│  │                          │    │                              │  │
│  └──────────────────────────┘    └──────────────────────────────┘  │
│           │                                   │                    │
│           └────────── network_mode: host ─────┘                    │
│                    ipc: host                                       │
│                    RMW: rmw_fastrtps_cpp                           │
│                    GZ_IP: 127.0.0.1                                │
│                    ROS_DOMAIN_ID: 0                                │
└────────────────────────────────────────────────────────────────────┘
```

In simulation (Milestones 1-4), both containers run on the same host.
In deployment (Milestone 5), `turtlebot3_robot` runs on the RPi 4 and
`turtlebot3_simulator` runs on the NucBoxM6, connected via WiFi.

### 3.2 Key ROS 2 Interfaces

| Interface | Type | Message/Srv/Action | Publisher(s) | Subscriber(s) | QoS | Notes |
|---|---|---|---|---|---|---|
| `/cmd_vel` | Topic | `geometry_msgs/msg/Twist` | teleop_twist_joy, wanderer, Nav2 controller | ros_gz_bridge → Gazebo / motor driver | RELIABLE | Must be Twist, NOT TwistStamped (G10) |
| `/scan` | Topic | `sensor_msgs/msg/LaserScan` | ros_gz_bridge ← Gazebo / LiDAR driver | slam_toolbox, wanderer, Nav2 costmap | BEST_EFFORT | 360° LDS, ~5-10 Hz |
| `/map` | Topic | `nav_msgs/msg/OccupancyGrid` | slam_toolbox | Nav2 map_server, RViz | TRANSIENT_LOCAL | 0x0 until robot moves (G19) |
| `/odom` | Topic | `nav_msgs/msg/Odometry` | ros_gz_bridge / diff_drive | Nav2, EKF | BEST_EFFORT | |
| `/imu` | Topic | `sensor_msgs/msg/Imu` | ros_gz_bridge / IMU driver | health_monitor (optional) | BEST_EFFORT | |
| `/joy` | Topic | `sensor_msgs/msg/Joy` | joy_node | teleop_twist_joy, gamepad_manager | BEST_EFFORT | F310 gamepad |
| `/battery_state` | Topic | `sensor_msgs/msg/BatteryState` | battery driver (RPi) / mock (sim) | health_monitor (optional) | BEST_EFFORT | |
| `/estop` | Topic | `std_msgs/msg/Bool` | gamepad_manager | all velocity publishers | RELIABLE + TRANSIENT_LOCAL | Latched; true = stopped |
| `/closest_obstacle` | Topic | `std_msgs/msg/Float32` | lidar_monitor | logging, health_monitor | BEST_EFFORT | Custom topic |
| `/navigate_to_pose` | Action | `nav2_msgs/action/NavigateToPose` | patrol_node (client) | bt_navigator (server) | — | Goal + feedback |
| `/clock` | Topic | `rosgraph_msgs/msg/Clock` | Gazebo (sim) | all nodes (use_sim_time) | RELIABLE | Bridged via ros_gz_bridge |

### 3.3 tf2 Frame Tree

Standard TurtleBot3 Burger frame tree:

```
map                              ← slam_toolbox (dynamic)
└── odom                         ← diff_drive / ros_gz_bridge (dynamic)
    └── base_footprint
        └── base_link            ← robot_state_publisher (static, from URDF)
            ├── base_scan        (LiDAR)
            ├── imu_link         (IMU)
            ├── wheel_left_link
            └── wheel_right_link
```

| Transform | Published By | Type |
|---|---|---|
| `map → odom` | `slam_toolbox` | Dynamic |
| `odom → base_footprint` | `diff_drive_controller` / `ros_gz_bridge` | Dynamic |
| `base_link → sensor frames` | `robot_state_publisher` | Static (from URDF) |

### 3.4 Target Repository Layout

```
turtlebot3/
├── .colcon/
│   └── defaults.yaml               # colcon build defaults
├── docker/
│   ├── Dockerfile.simulator        # osrf/ros:jazzy-desktop-full + deps
│   ├── Dockerfile.turtlebot        # robotis/turtlebot3 + deps
│   └── docker-compose.yaml         # network_mode: host, both containers
├── entrypoint.sh
├── scripts/
│   ├── build.sh                    # Docker image build
│   ├── run_docker.sh               # docker compose up wrapper
│   ├── attach_terminal.sh          # Interactive attach
│   ├── workspace.sh                # Workspace setup helper
│   ├── run_tests.sh                # Test runner (--gui flag)
│   └── tmux_dashboard.sh           # TMUX monitoring (M4)
├── src/
│   ├── tb3_bringup/                # Launch files, configs, worlds (ament_python)
│   │   ├── config/
│   │   │   ├── bridge_params.yaml          # ros_gz_bridge topic config
│   │   │   ├── teleop_twist_joy.yaml       # Joystick axis/button mapping
│   │   │   ├── nav2_params.yaml            # Nav2 tuned for TB3 Burger (M3)
│   │   │   └── slam_params.yaml            # slam_toolbox online_async (M3)
│   │   ├── worlds/
│   │   │   ├── tb3_warehouse.world         # turtlebot3_world + TB3 embedded
│   │   │   └── tb3_house.world             # turtlebot3_house + TB3 embedded
│   │   └── launch/
│   ├── tb3_controller/             # Wanderer, patrol, gamepad (ament_python)
│   └── tb3_monitor/                # LiDAR monitor, health (ament_python)
├── docs/
│   ├── specification.md            # This document
│   ├── development-plan.md
│   └── user-guide-milestone-{1..5}.md
└── input/
    ├── my-vision.md
    └── my-claude-prompts.md
```

---

## 4. Known Constraints and Gotchas

These constraints are carried forward from prior development sessions and documented
in `.claude/rules/gotchas.md`. Each is assigned a G-ID for cross-referencing in
milestone sections. Full text is in [Appendix B](#appendix-b-known-gotchas-reference).

| G-ID | Category | Constraint Summary |
|---|---|---|
| G1 | Docker | `sg docker -c "..."` needed until fresh login after `usermod` |
| G2 | Docker | `osrf/ros:jazzy-desktop-full` ships `ubuntu` user at UID 1000; must `userdel` before `useradd` |
| G3 | Docker | No TTY in Claude Code subprocess; start containers detached, user attaches |
| G4 | DDS | `ros2 topic list` hangs due to DDS discovery; verify ROS with `which ros2` |
| G5 | Network | RPi 4 requires `--network host` for DDS multicast across LAN |
| G6 | Image | `robotis/turtlebot3:jazzy` tag does NOT exist; use `jazzy-pc-latest` or `jazzy-sbc-latest` |
| G7 | Gazebo | `gz` binary at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`; add to PATH in Dockerfile |
| G8 | Gazebo | Use `gz sim`, not `gazebo` |
| G9 | Gazebo | gz-sim 8.10 removed spawner service; embed TB3 model directly in world SDF |
| G10 | Bridge | `/cmd_vel` must use `geometry_msgs/msg/Twist`, not `TwistStamped` |
| G11 | Teleop | `turtlebot3_teleop` hardcodes `TwistStamped`; use `teleop_twist_keyboard` instead |
| G12 | Teleop | `teleop_keyboard` needs TTY; never launch via non-interactive `docker exec` |
| G13 | Gazebo | Headless sim: pass `headless:=true` to `sim_bringup.launch.py` |
| G14 | DDS | CycloneDDS hangs on hosts with many bridge/veth interfaces; use Fast-DDS |
| G15 | Gazebo | gz-transport needs `GZ_IP=127.0.0.1` for bridge connection |
| G16 | Volume | `scripts/` mounted into container at `~/ros2_ws/scripts` |
| G17 | ROS CLI | Must source both `/opt/ros/jazzy/setup.bash` AND workspace `install/setup.bash` |
| G18 | SLAM | `map_saver_cli` fails; use `slam_toolbox/srv/SaveMap` service instead |
| G19 | SLAM | `/map` is 0x0 until robot drives and LiDAR scans accumulate |
| G20 | Teleop | `teleop_twist_keyboard` keys: `i`=fwd, `,`=back, `j`/`l`=turn, `k`=stop |
| G21 | Display | Gazebo GUI needs `xhost +local:docker` on host |
| G22 | Docker | `libgl1-mesa-glx` removed in Ubuntu 24.04; use `libgl1-mesa-dri` |
| G23 | Docker | `/opt/ros/jazzy/bin` not in `ENV PATH` in base images; add explicitly in Dockerfile |
| G24 | Docker | `docker compose restart` does NOT re-read compose file; use `up --force-recreate` |
| G25 | Gamepad | `ros-jazzy-joy` uses SDL2 — needs `/dev/input/eventX` + `device_cgroup_rules: ["c 13:* rmw"]` + `group_add: ["102"]` |
| G26 | Docker | YAML `<<:` anchor merge does NOT concat lists; per-service `volumes:` override replaces anchor volumes entirely |
| G27 | SLAM | `async_slam_toolbox_node` is a lifecycle node; use `online_async_launch.py` with `autostart:=true`, not `Node()` directly |
| G28 | ROS CLI | `ros2 service call` blocks indefinitely if server not up; always wrap with `timeout 20 ros2 service call ...` |

---

## 5. Milestone Specifications

### 5.1 Milestone 1: Docker Simulation Environment

**Objective**: Create two Docker containers — simulator and turtlebot — running TurtleBot3
Burger in the AWS RoboMaker Small Warehouse world with Gazebo Harmonic GUI visible via
X11 on the host.

#### Functional Requirements

| ID | Requirement |
|---|---|
| FR-1.1 | Simulator container built from `osrf/ros:jazzy-desktop-full` with TurtleBot3, Nav2, SLAM, Gazebo Harmonic, ros_gz_bridge, teleop_twist_keyboard packages installed |
| FR-1.2 | Turtlebot container built from `robotis/turtlebot3:jazzy-pc-latest` (amd64) |
| FR-1.3 | `docker-compose.yml` orchestrates both containers with `network_mode: host`, `ipc: host`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `GZ_IP=127.0.0.1`, `ROS_DOMAIN_ID=0` |
| FR-1.4 | AWS RoboMaker Small Warehouse world SDF file with TB3 Burger model embedded directly (no spawner service per G9) |
| FR-1.5 | Gazebo Harmonic GUI renders on host via X11 (`DISPLAY` env + X11 socket mount) |
| FR-1.6 | `ros_gz_bridge` bridges topics: `/cmd_vel` (Twist, bidirectional), `/scan` (GZ→ROS), `/odom` (GZ→ROS), `/imu` (GZ→ROS), `/clock` (GZ→ROS) |
| FR-1.7 | Helper scripts: `build.sh`, `run_docker.sh`, `attach_terminal.sh` |
| FR-1.8 | `entrypoint.sh` sources ROS setup and workspace setup |
| FR-1.9 | `colcon build` succeeds for `tb3_bringup` package with sim launch files |
| FR-1.10 | `sim_bringup.launch.py` starts Gazebo + bridge + robot_state_publisher; supports `headless:=true` argument (G13) |

#### Applicable Gotchas

G1, G2, G3, G4, G6, G7, G8, G9, G10, G13, G14, G15, G16, G17, G21

#### Deliverables

* `docker/Dockerfile.simulator`
* `docker/Dockerfile.turtlebot`
* `docker/docker-compose.yml`
* `entrypoint.sh`
* `scripts/build.sh`, `scripts/run_docker.sh`, `scripts/attach_terminal.sh`
* `config/bridge_params.yaml`
* `worlds/tb3_warehouse.world`
* `src/tb3_bringup/` package with `sim_bringup.launch.py`
* `docs/user-guide-milestone-1.md`

#### Test-Gate Categories

| Category | Example Test |
|---|---|
| Container health | `docker exec turtlebot3_simulator which ros2` returns a valid path |
| Workspace build | `colcon build` inside container exits 0 with 1+ packages |
| Gazebo simulation | `gz topic -l` inside container returns `/world/...` topics |
| ROS bridge | `ros2 topic list` (with timeout) includes `/scan`, `/cmd_vel`, `/odom` |
| GUI rendering | Human observer confirms Gazebo window shows warehouse with TB3 Burger |
| Keyboard teleop | `teleop_twist_keyboard` in attached terminal moves robot in Gazebo |

---

### 5.2 Milestone 2: Gamepad Control (Logitech F310)

**Objective**: Manual control of TurtleBot3 via F310 gamepad with e-stop, restart,
and reboot buttons. All control runs in the simulator container.

#### Functional Requirements

| ID | Requirement |
|---|---|
| FR-2.1 | `joy_node` reads F310 gamepad via `/dev/input/js0` (device passed through to container via `docker-compose.yml`) |
| FR-2.2 | `teleop_twist_joy` publishes `geometry_msgs/msg/Twist` on `/cmd_vel_raw`; `gamepad_manager` gates output to `/cmd_vel` (e-stop relay pattern) |
| FR-2.3 | Left joystick (axis 0) controls direction (angular Z); right joystick (axis 4) controls speed (linear X forward/reverse) |
| FR-2.4 | **E-stop** (red/B button, index 1): publishes zero velocity on `/cmd_vel`, sets `/estop` topic to `true`, disables all velocity output from gamepad until restart |
| FR-2.5 | **Restart** (green/A button, index 0): clears e-stop, sets `/estop` to `false`, re-enables velocity output |
| FR-2.6 | **Shutdown** (yellow/Y button, index 3): publishes zero velocity, sets `/estop=true`, sends SIGINT to process group — stops all gamepad nodes cleanly. Full auto-reboot deferred to Milestone 5 (systemd watchdog / docker restart policy on RPi). |
| FR-2.7 | `gamepad_manager` node: subscribes to `/joy`, manages e-stop state machine, publishes `/estop` (RELIABLE + TRANSIENT_LOCAL QoS), implements reboot logic |
| FR-2.8 | All velocity-publishing nodes (wanderer, patrol, teleop) must check `/estop` before publishing to `/cmd_vel` |
| FR-2.9 | Simulator Dockerfile installs `ros-jazzy-joy` and `ros-jazzy-teleop-twist-joy` |
| FR-2.10 | `gamepad.launch.py` starts joy_node + teleop_twist_joy + gamepad_manager |

**Risk — teleop_twist_joy message type**: The `teleop_twist_joy` package may publish
`TwistStamped` instead of `Twist` (similar to G11). This must be investigated during
development. If confirmed, a `joy_twist_adapter` wrapper node or configuration change
will be needed.

#### Applicable Gotchas

G3, G10, G12, G24, G25, G26

#### Deliverables

* `src/tb3_controller/` — `gamepad_manager` node
* `config/teleop_twist_joy.yaml` — joystick axis/button mapping
* Updated `docker/Dockerfile.simulator` (joy packages)
* `src/tb3_bringup/` — `gamepad.launch.py`
* `docs/user-guide-milestone-2.md`

#### Test-Gate Categories

| Category | Example Test |
|---|---|
| Gamepad input | `ros2 topic echo /joy` shows messages when F310 buttons/sticks are moved |
| Velocity output | Robot moves in Gazebo when right joystick is pushed forward |
| Direction control | Robot turns in Gazebo when left joystick is moved left/right |
| E-stop engage | Press red/B button; robot stops immediately; joystick input produces no motion |
| E-stop release | Press green/A button after e-stop; joystick control resumes |
| Shutdown | Press yellow/Y button; all gamepad nodes stop cleanly, zero velocity published |

---

### 5.3 Milestone 3: Autonomous Capabilities

**Objective**: Exercise TurtleBot3 sensors and navigation with autonomous behavior nodes.
Core capabilities are mandatory; optional capabilities are stretch goals.

#### Core Functional Requirements

| ID | Requirement |
|---|---|
| FR-3.1 | **Wanderer node** (`wanderer_node`): subscribes to `/scan`, publishes `/cmd_vel`. Drives forward when path is clear; turns away when closest obstacle is below configurable threshold (default 0.5m). Checks `/estop` before publishing. |
| FR-3.2 | **Patrol node** (`patrol_node`): uses Nav2 `NavigateToPose` action to visit waypoints in sequence. Configurable waypoints via YAML parameter (default: `[[1.0, 0.0], [2.0, 1.0], [0.0, 1.0]]`). Reports success/failure per waypoint to log. Checks `/estop`. |
| FR-3.3 | **LiDAR monitor node** (`lidar_monitor_node`): subscribes to `/scan`, computes minimum distance across all ranges, publishes to `/closest_obstacle` (`std_msgs/msg/Float32`). |
| FR-3.4 | Nav2 parameter file (`nav2_params.yaml`) tuned for TB3 Burger: robot_radius 0.105m, max linear velocity 0.22 m/s. |
| FR-3.5 | SLAM configuration: `slam_toolbox` in `online_async` mode. Maps saveable via service call: `ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap` (G18). |
| FR-3.6 | `capability_demo.launch.py` starts wanderer OR patrol (selectable via argument), plus SLAM, Nav2, and lidar_monitor. |

#### Optional Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-3.7 | **Health monitor node** (`health_monitor_node`): subscribes to `/battery_state` and `/imu`, logs status at 1 Hz. In simulation, a mock battery publisher node provides synthetic data. | Nice-to-have |
| FR-3.8 | **TF2 verifier script** (`tf2_verifier.py`): checks `map→base_link` transform exists and is recent (< 1s old). Exits 0 on success, 1 on failure. Usable as a test-gate. | Nice-to-have |
| FR-3.9 | **Scanning action** (`scan_action_server`): ROS 2 Action server accepting a goal to rotate 360°. Publishes feedback (degrees completed). Returns success/failure result. | Nice-to-have |

#### Applicable Gotchas

G4, G8, G9, G10, G11, G13, G14, G15, G17, G18, G19

#### Deliverables

* `src/tb3_controller/` — `wanderer_node`, `patrol_node`
* `src/tb3_monitor/` — `lidar_monitor_node`, (optional: `health_monitor_node`, `tf2_verifier.py`)
* `config/nav2_params.yaml`
* `config/slam_params.yaml`
* `src/tb3_bringup/` — `capability_demo.launch.py`, `nav2.launch.py`, `slam.launch.py`
* `docs/user-guide-milestone-3.md`

#### Test-Gate Categories

| Category | Example Test |
|---|---|
| Obstacle avoidance | Wanderer runs 60s in warehouse without collision; no `/cmd_vel` published when `/scan` minimum < 0.15m |
| Navigation | Patrol node visits 3 waypoints; `NavigateToPose` action result is SUCCEEDED for each |
| LiDAR processing | `/closest_obstacle` publishes `Float32` values > 0 while robot is in warehouse |
| SLAM mapping | After 60s of wandering, `/map` has non-zero width × height; map saveable via service (G18) |
| Nav2 parameters | Nav2 starts with custom params; `robot_radius` = 0.105 confirmed in parameter dump |
| (Optional) TF2 | `tf2_verifier.py` exits 0 when SLAM + odometry are running |
| (Optional) Health | `health_monitor_node` logs battery and IMU status at ~1 Hz |
| (Optional) Action | 360° scan action completes; feedback shows incremental degree progress |

---

### 5.4 Milestone 4: TMUX Monitoring Dashboard

**Objective**: Single-terminal monitoring of all active ROS 2 nodes via TMUX,
auto-configured when a user attaches to the container.

#### Functional Requirements

| ID | Requirement |
|---|---|
| FR-4.1 | `scripts/tmux_dashboard.sh` (or Tmuxinator YAML in `config/`) creates a multi-pane TMUX layout |
| FR-4.2 | Minimum panes: (1) `ros2 node list` refreshing periodically, (2) `ros2 topic echo /cmd_vel` live velocity, (3) `/closest_obstacle` or `/scan` closest distance, (4) `ros2 topic echo /odom --field pose.pose.position` robot position, (5) node log output (stdout from key nodes) |
| FR-4.3 | Script is idempotent: running again attaches to existing TMUX session or recreates if session died |
| FR-4.4 | Script is launchable via `bash scripts/tmux_dashboard.sh` from an attached terminal |
| FR-4.5 | TMUX session name is deterministic (e.g., `tb3_monitor`) |

**Note**: This milestone does NOT require re-running previous test-gates (per vision document).

#### Applicable Gotchas

G3, G17

#### Deliverables

* `scripts/tmux_dashboard.sh` (or `config/tmuxinator.yml`)
* `docs/user-guide-milestone-4.md`

#### Test-Gate Categories

| Category | Example Test |
|---|---|
| Layout | TMUX opens with 5+ panes, no error messages |
| Live data | `/cmd_vel` pane shows data when robot is being driven |
| Position tracking | `/odom` pane shows changing x/y values as robot moves |
| Idempotency | Running `tmux_dashboard.sh` twice does not create duplicate sessions |

---

### 5.5 Milestone 5: RPi 4 Hardware Deployment

**Objective**: Deploy `turtlebot3_robot` container to Raspberry Pi 4 on the physical
TurtleBot3 Burger. `turtlebot3_simulator` (Gazebo, with gamepad + monitoring)
runs on NucBoxM6. Both connected via GL.iNet travel router WiFi.

#### Functional Requirements

| ID | Requirement |
|---|---|
| FR-5.1 | RPi 4 running Ubuntu 24.04 Server (arm64) with Docker installed |
| FR-5.2 | Turtlebot container built from `robotis/turtlebot3:jazzy-sbc-latest` (arm64) |
| FR-5.3 | NucBoxM6 running Ubuntu 24.04 with Docker; simulator container installed |
| FR-5.4 | Both machines on same WiFi network (SSID "JeffTravelRouter-2.4"), same `ROS_DOMAIN_ID` |
| FR-5.5 | DDS multicast works across WiFi; both containers use `--network host` (G5) |
| FR-5.6 | F310 gamepad connected to NucBoxM6; `/dev/input/js0` passed to container |
| FR-5.7 | All M1-M3 core functionality works with real hardware replacing Gazebo simulation |
| FR-5.8 | RPi 4 turtlebot container runs headless (no GUI) |

#### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-5.1 | Document RPi 4 setup procedure: Ubuntu 24.04 install, Docker install, image build/pull |
| NFR-5.2 | Document network configuration: router setup, DDS discovery configuration |

#### Applicable Gotchas

G1, G2, G3, G5, G6, G14

#### Deliverables

* Updated `docker/Dockerfile.turtlebot` (arm64-verified)
* RPi 4 setup documentation (within user guide)
* Network configuration documentation
* `docs/user-guide-milestone-5.md`

#### Test-Gate Categories

| Category | Example Test |
|---|---|
| Connectivity | `ros2 node list` on NucBoxM6 shows nodes running on RPi 4 container |
| Hardware drive | Gamepad on NucBoxM6 moves physical TurtleBot3 robot |
| Sensor data | `ros2 topic echo /scan` on NucBoxM6 shows real LiDAR data from RPi 4 |
| Autonomous drive | Wanderer node runs on real robot; robot avoids physical walls |
| Regression | All M1-M3 test-gates pass (adapted for real hardware where applicable) |

---

## 6. ROS 2 Package Specifications

### 6.1 `tb3_bringup` (ament_python)

**Purpose**: Launch files and configuration for all system modes.

| Launch File | Description |
|---|---|
| `sim_bringup.launch.py` | Gazebo + bridge + robot_state_publisher; `headless:=true` arg |
| `teleop.launch.py` | teleop_twist_keyboard for keyboard control |
| `gamepad.launch.py` | joy_node + teleop_twist_joy + gamepad_manager |
| `slam.launch.py` | slam_toolbox online_async |
| `nav2.launch.py` | Full Nav2 stack with custom params |
| `capability_demo.launch.py` | Wanderer or patrol + SLAM + Nav2 + lidar_monitor |

### 6.2 `tb3_controller` (ament_python)

**Purpose**: Robot behavior and control nodes.

| Node | Description |
|---|---|
| `wanderer_node` | LiDAR-based obstacle avoidance; drives `/cmd_vel` |
| `patrol_node` | Nav2 waypoint following via `NavigateToPose` action |
| `gamepad_manager_node` | E-stop/restart/reboot logic from `/joy` input |
| (Optional) `scan_action_server` | 360° rotation action server |

### 6.3 `tb3_monitor` (ament_python)

**Purpose**: Monitoring and diagnostics nodes.

| Node/Script | Description |
|---|---|
| `lidar_monitor_node` | Publishes closest obstacle distance to `/closest_obstacle` |
| (Optional) `health_monitor_node` | Logs `/battery_state` and `/imu` at 1 Hz |
| (Optional) `tf2_verifier.py` | Checks `map→base_link` transform freshness |

---

## 7. Configuration and Parameters

| Node | Parameter | Type | Default | Description |
|---|---|---|---|---|
| `wanderer_node` | `obstacle_threshold` | float | 0.5 | Min distance (m) before turning |
| `wanderer_node` | `turn_speed` | float | 0.5 | Angular Z velocity (rad/s) when avoiding |
| `wanderer_node` | `forward_speed` | float | 0.15 | Linear X velocity (m/s) when path clear |
| `patrol_node` | `waypoints` | list | `[[1.0,0.0],[2.0,1.0],[0.0,1.0]]` | Ordered list of [x,y] coordinates |
| `patrol_node` | `goal_tolerance` | float | 0.25 | Distance (m) to consider waypoint reached |
| `gamepad_manager` | `estop_button` | int | 1 | F310 button index — red/B |
| `gamepad_manager` | `restart_button` | int | 0 | F310 button index — green/A |
| `gamepad_manager` | `shutdown_button` | int | 3 | F310 button index — yellow/Y (SIGINT to process group) |
| `teleop_twist_joy` | `axis_linear.x` | int | 4 | Right stick Y axis (speed) |
| `teleop_twist_joy` | `axis_angular.yaw` | int | 0 | Left stick X axis (direction) |
| `teleop_twist_joy` | `scale_linear.x` | float | -0.22 | Negated: SDL2 up=-1.0, so negative gives positive forward |
| `teleop_twist_joy` | `scale_angular.yaw` | float | -1.0 | Negated: SDL2 left=-1.0, gives correct CCW turn |
| `lidar_monitor_node` | `publish_rate` | float | 5.0 | Rate (Hz) for `/closest_obstacle` |
| `slam_toolbox` | `mode` | string | `online_async` | SLAM mode |
| `sim_bringup` | `headless` | bool | `false` | Skip Gazebo GUI client |

---

## 8. Simulation Environment

### 8.1 Gazebo World

* **Source**: `ros-jazzy-turtlebot3-gazebo` — `turtlebot3_world` (obstacle course) and `turtlebot3_house` (indoor rooms); AWS warehouse not available in apt (R7 materialised)
* **Files**: `src/tb3_bringup/worlds/tb3_warehouse.world` and `tb3_house.world` (SDF format)
* **Modification**: TB3 Burger model embedded directly in the SDF via `<include><uri>model://turtlebot3_burger</uri></include>` (G9: gz-sim 8.10 removed the spawner service `/world/default/create`)
* **Model path**: `/opt/ros/jazzy/share/turtlebot3_gazebo/models/turtlebot3_burger/` (accessed via `model://turtlebot3_burger` with `GZ_SIM_RESOURCE_PATH`)

### 8.2 ros_gz_bridge Configuration (`config/bridge_params.yaml`)

| ROS Topic | Gazebo Topic | Direction | ROS Type | GZ Type |
|---|---|---|---|---|
| `/cmd_vel` | `/cmd_vel` | ROS → GZ | `geometry_msgs/msg/Twist` | `gz.msgs.Twist` |
| `/scan` | `/lidar/scan` | GZ → ROS | `sensor_msgs/msg/LaserScan` | `gz.msgs.LaserScan` |
| `/odom` | `/odom` | GZ → ROS | `nav_msgs/msg/Odometry` | `gz.msgs.Odometry` |
| `/imu` | `/imu` | GZ → ROS | `sensor_msgs/msg/Imu` | `gz.msgs.IMU` |
| `/clock` | `/clock` | GZ → ROS | `rosgraph_msgs/msg/Clock` | `gz.msgs.Clock` |

---

## 9. User Guide Requirements

Each milestone produces a `docs/user-guide-milestone-N.md` containing:

1. **Prerequisites** — Docker running, host display configured, gamepad connected, etc.
2. **Quick Start** — step-by-step commands to start the system from scratch
3. **Test-Gate Instructions** — step-by-step commands for each test-gate with expected output
4. **Troubleshooting** — common issues with references to relevant G-IDs from Section 4
5. **Shutdown** — clean shutdown procedure

User guides are written for non-technical Makersmiths members who may operate demos.

---

## 10. Out of Scope

The following are explicitly NOT part of this specification:

* Multi-robot operation or fleet management
* Cloud connectivity, ROS 2 web bridge, or remote monitoring
* Computer vision or camera processing
* Custom URDF modifications to TurtleBot3
* Production-grade security (ROS 2 SROS2)
* CI/CD pipeline or automated deployment
* Detailed RPi 4 hardware troubleshooting beyond basic setup
* Custom DDS tuning (beyond Fast-DDS selection and `GZ_IP`)

---

## 11. Risks and Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | AWS Warehouse world SDF not compatible with Gazebo Harmonic | Medium | High | Verify SDF loads early in M1; fallback to simpler custom world |
| R2 | F310 gamepad not detected inside Docker container | Low | Medium | Pass `--device /dev/input/js0` in docker-compose; verify with `jstest` |
| R3 | `teleop_twist_joy` publishes `TwistStamped` instead of `Twist` | Medium | Medium | Investigate package version in M2; if confirmed, create wrapper node or use config option |
| R4 | Fast-DDS multicast fails across WiFi in M5 | Medium | High | Test DDS discovery early in M5; fallback to FastDDS Discovery Server |
| R5 | RPi 4 (4GB) memory insufficient for turtlebot container | Low | High | Monitor with `docker stats`; strip unnecessary packages from arm64 image |
| R6 | Nav2 goal failures in small warehouse (tight corridors) | Medium | Medium | Tune costmap inflation radius and planner parameters; adjust waypoints |

---

## Appendix A: Original Prompt and Clarification Q&A

### Original Prompt (3rd Claude Code Prompt)

> Read @/input/my-vision.md and create a specification document called @/docs/specification.md.
>
> Within the specification document you create, include this prompt,
> all question you ask me, along with my responses.
> Place this in an appendix and reference it at the beginning of the specification document
> and anywhere else in the text when its a useful reference.
>
> In a subsequent phase, I need this specification document to help prepare a detailed development plan.
> Think Very Hard about what must be specified in the specification document so a robust development plan can be created.
>
> Use the AskUserQuestions tool for all things that require further clarification.

### Clarification Questions and Responses

**Q1**: You're starting over (per recent commit). Should the spec reference prior phases 0-8
work as proven decisions, or treat everything as greenfield?
**A1**: Carry forward gotchas only — keep the `gotchas.md` as known constraints but re-spec everything else.

**Q2**: The vision mentions AWS RoboMaker Small Warehouse World for Gazebo. The gotchas
reference a custom `worlds/tb3_sim.world`. Which world should the spec target?
**A2**: AWS Small Warehouse — use `ros-jazzy-aws-robomaker-small-warehouse-world` package.

**Q3**: How detailed should test-gate definitions be in the spec? The vision says 2-8 tests
per phase but doesn't define them.
**A3**: Categories + examples — define test categories per milestone with 1-2 example tests; details deferred to dev plan.

**Q4**: Milestone 2 specifies gamepad button mapping in detail (left stick=direction, right
stick=speed, red=e-stop, green=restart, yellow=reboot). Should the spec also cover what
"reboot the whole demo system" means technically?
**A4**: Yes, fully specify — define e-stop behavior (zero velocity + disable), restart (re-enable),
reboot (container restart or ROS lifecycle reset).

**Q5**: For Milestone 3's autonomous capabilities, the vision lists several nodes (Wanderer,
Health Monitor, Patrol, LIDAR closest-obstacle, Nav2, TF2, 360-scan Action). Should the
spec treat these as firm requirements or as a suggested menu to pick from?
**A5**: Core + optional — Wanderer + Patrol are core; Health Monitor, TF2, Action are nice-to-have.

**Q6**: For Milestone 5 (RPi 4 deployment), the vision mentions WiFi via GL.iNet GL-AXT1800
router. Should the spec include network topology details (IP ranges, DDS discovery config,
latency requirements)?
**A6**: High-level only — just specify same-LAN WiFi + DDS multicast requirement; details in dev plan.

**Q7**: Should the spec define the ROS 2 node graph (topics, services, actions between nodes)
or leave that to the development plan / architecture doc?
**A7**: Key interfaces only — specify the critical topic names and message types (e.g., `/cmd_vel`,
`/scan`, `/map`) but not the full node graph.

**Q8**: F310 gamepad: are red/green/yellow references to B/A/Y buttons (Xbox-style labels),
or to physical button colors on your specific unit?
**A8**: Physical button colors — map by actual color printed on the F310 buttons.

**Q9**: Reboot button behavior: "container restart" (docker restart) vs "ROS lifecycle reset"
(restart nodes without restarting container). Which do you prefer?
**A9**: Support both via param — configurable parameter: default to lifecycle reset, option for
full container restart.

**Q10**: Patrol waypoints for Milestone 3 — should the spec include placeholder coordinates
to tune later, or leave them as "TBD after warehouse world is loaded"?
**A10**: Placeholders in spec — include reasonable defaults like `[[1.0,0.0],[2.0,1.0],[0.0,1.0]]`,
adjust during development.

**Q11**: The `teleop_twist_joy` ROS package may also hardcode `TwistStamped` (like
`turtlebot3_teleop`). Should the spec preemptively plan for a custom joy-to-Twist wrapper node?
**A11**: Investigate first — spec notes the risk; dev plan investigates actual message type before deciding.

---

## Appendix B: Known Gotchas Reference

Full text reproduced from `.claude/rules/gotchas.md` for self-contained readability.

* **G1 — Docker permission denied**: `jeff` in `docker` group but session predates `usermod`. Prefix with `sg docker -c "..."` until fresh login.
* **G2 — `ubuntu` user conflict**: `osrf/ros:jazzy-desktop-full` ships `ubuntu` at UID 1000. Dockerfile must `userdel -r ubuntu` before `useradd ros_user`.
* **G3 — `docker run -it` in Claude Code**: no TTY in subprocess — start detached with `sleep infinity`, then attach from user's terminal.
* **G4 — `ros2 topic list` hangs**: DDS peer discovery blocks. Use `which ros2` or `python3 -c "import rclpy"` to verify ROS without blocking.
* **G5 — Production networking**: turtlebot container on RPi 4 uses `--network host` (required for DDS multicast across machines on same LAN); simulator stays on desktop.
* **G6 — `robotis/turtlebot3` tag**: `jazzy` tag does NOT exist. Use `jazzy-pc-latest` (dev/amd64) or `jazzy-sbc-latest` (RPi4/arm64).
* **G7 — `gz` binary path**: not in standard PATH — at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`. Both Dockerfiles add it via `ENV PATH`.
* **G8 — Gazebo Harmonic**: use `gz sim` (not `gazebo`); `gz_ros2_control` bridge; `ros-jazzy-turtlebot3-gazebo` must have Harmonic-compatible worlds.
* **G9 — gz-sim 8.10 spawner removed**: `/world/default/create` service no longer exists in gz-sim 8.10. Embed the TB3 model directly in the world SDF instead of using `ros_gz_sim` spawner.
* **G10 — `/cmd_vel` bridge type**: upstream `turtlebot3_gazebo` bridge uses `TwistStamped`; our `bridge_params.yaml` overrides to `geometry_msgs/msg/Twist` — required for `teleop_keyboard`, `obstacle_avoidance_node`, and Nav2.
* **G11 — `turtlebot3_teleop` v2.3.6 hardcodes `TwistStamped`**: no parameter to switch it. Our `ros_gz_bridge` expects `Twist`, so all drive commands are silently dropped. Use `teleop_twist_keyboard` instead.
* **G12 — `teleop_keyboard` needs TTY**: Never launch via non-interactive `docker exec`. Use `bash scripts/attach_terminal.sh turtlebot3_simulator`, then run from within that session.
* **G13 — headless sim for testing**: pass `headless:=true` to `sim_bringup.launch.py` when launching via `docker exec` (no display). The gz sim server still runs and publishes `/clock`.
* **G14 — CycloneDDS hangs on hosts with many bridge/veth interfaces**: `rclpy.init()` blocks joining multicast groups. Switched to `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (Fast-DDS).
* **G15 — gz-transport also uses multicast for discovery**: `GZ_IP=127.0.0.1` forces gz-transport to use loopback, fixing the bridge connection between Gazebo and `ros_gz_bridge`. Set in docker-compose.yml.
* **G16 — `scripts/` is mounted into the container**: `./scripts` → `~/ros2_ws/scripts`. If the container predates the mount, use `docker cp` instead.
* **G17 — `ros2` CLI breaks when only workspace setup is sourced**: Always source both — `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash`.
* **G18 — `map_saver_cli` fails with "Failed to spin map subscription"**: QoS/DDS issue. Use the slam_toolbox service instead: `ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap`.
* **G19 — `/map` is 0x0 until robot moves**: slam_toolbox publishes an empty initial map. Map fills as the robot drives and LiDAR scans accumulate.
* **G20 — `teleop_twist_keyboard` key bindings**: `i`=forward, `,`=back, `j`/`l`=turn, `k`=stop. Hold key to keep moving.
* **G21 — Gazebo GUI on host**: `docker-compose.yml` passes `DISPLAY` + mounts X11 socket. Run `xhost +local:docker` once per login.
* **G22 — `libgl1-mesa-glx` removed in Ubuntu 24.04**: package no longer exists; replaced by `libgl1-mesa-dri`. Remove from Dockerfile apt installs.
* **G23 — `/opt/ros/jazzy/bin` not in ENV PATH**: osrf and robotis base images add ROS bin to PATH only via `source setup.bash`, not via `ENV`. Dockerfiles must explicitly add `/opt/ros/${ROS_DISTRO}/bin` to `ENV PATH`.
* **G24 — `docker compose restart` does NOT re-read compose file**: new `devices`, volumes, or env vars added to compose.yaml are NOT applied on restart. Must use `docker compose up -d --force-recreate <service>`.
* **G25 — `ros-jazzy-joy` uses SDL2, not the kernel joystick API**: requires `/dev/input/eventX` (evdev). Fix: bind-mount `/dev/input:/dev/input` + `device_cgroup_rules: ["c 13:* rmw"]` + `group_add: ["102"]` (input GID). `joy_node` must have `use_sim_time: False`.
* **G26 — YAML merge (`<<: *anchor`) does NOT concat lists**: adding a `volumes:` key to a service that uses `<<: *ros-common` completely replaces the anchor's volumes list. Always put shared mounts in the anchor itself.
* **G27 — `async_slam_toolbox_node` is a lifecycle node**: spawning it directly with `Node()` leaves it in unconfigured state — no `/scan` subscription, no `/map` publication. Use slam_toolbox's provided `online_async_launch.py` (with `autostart:=true`) which emits CONFIGURE → ACTIVATE lifecycle events automatically.
* **G28 — `ros2 service call` blocks indefinitely if service is unavailable**: unlike topic echo which has a `--timeout` option, `ros2 service call` waits forever if the server isn't up. Always wrap with `timeout 20 ros2 service call ...` in scripts.

---

## Appendix C: Glossary

| Term | Definition |
|---|---|
| ROS 2 | Robot Operating System 2 — middleware framework for robotics |
| Jazzy Jalisco | ROS 2 distribution released May 2024 (LTS until May 2029) |
| Gazebo Harmonic | Physics-based robot simulator (successor to Gazebo Classic) |
| DDS | Data Distribution Service — pub/sub middleware underlying ROS 2 |
| Fast-DDS | eProsima's DDS implementation (`rmw_fastrtps_cpp`) |
| SLAM | Simultaneous Localization and Mapping |
| slam_toolbox | ROS 2 SLAM package supporting online/offline mapping |
| Nav2 | ROS 2 Navigation Stack — path planning, obstacle avoidance, waypoint following |
| tf2 | ROS 2 transform library for coordinate frame management |
| QoS | Quality of Service — DDS reliability/durability/history profiles |
| SDF | Simulation Description Format — Gazebo world/model file format |
| URDF | Unified Robot Description Format — ROS robot model file format |
| ros_gz_bridge | Bidirectional message bridge between ROS 2 and Gazebo transport |
| teleop_twist_joy | ROS 2 package converting joystick input to velocity commands |
| colcon | ROS 2 build tool (replaces catkin) |
| ament_python | ROS 2 build type for Python packages |
