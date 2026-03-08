# TurtleBot3 Autonomous Robot Workshop — Development Plan

* **Version**: 1.0
* **Date**: 2026-03-07
* **Author**: Jeff (vision & requirements) + Claude Code (plan)
* **Status**: Active

> This plan was generated from the project specification (`docs/specification.md`)
> through a structured clarification process. The original prompt, all questions asked,
> and user responses are recorded in [Appendix A](#appendix-a-original-prompt-and-clarification-qa).

**Key References**:
* Requirements: `input/my-vision.md`
* Specification: `docs/specification.md` — FR-IDs, G-IDs, test-gate categories
* Gotchas: `.claude/rules/gotchas.md` — 26 pitfalls (G1–G21 original + G22–G23 added during M1 + G24–G26 added during M2)
* Skills: `.claude/skills/` — 7 ROS 2 domain skills

---

## 1. How to Use This Document

This is a **living document** — update it as the project evolves.

### Status Markers

Each phase has a status field. Valid values:

| Status | Meaning |
|---|---|
| `NOT STARTED` | No work begun |
| `IN PROGRESS` | Currently being implemented |
| `COMPLETE` | All deliverables created, all test-gates pass |
| `BLOCKED` | Cannot proceed; see notes for reason |

### When to Update

* **Starting a phase**: set status to `IN PROGRESS`, note the date
* **Completing a phase**: set status to `COMPLETE`, note the date
* **Making a technical decision**: add row to [Decisions Log](#7-decisions-log)
* **Changing the plan**: add row to [Change Log](#8-change-log)
* **Discovering a new gotcha**: add to `.claude/rules/gotchas.md` AND note in Decisions Log

### Convention for Claude Code Sessions

At the start of each session, Claude Code should:
1. Read this plan to determine the current phase
2. Read the Decisions Log for prior decisions
3. Execute the current phase's deliverables and test-gates
4. Update status markers and logs before ending the session

---

## 2. Technical Decisions to Resolve Upfront

These must be investigated before or during the indicated phase. Record results in the [Decisions Log](#7-decisions-log).

| # | Decision | Phase | Investigation Method | Fallback |
|---|---|---|---|---|
| D1 | AWS warehouse SDF file path in ros package | 1.3 | `ros2 pkg prefix aws_robomaker_small_warehouse_world` inside container | Custom simple world |
| D2 | TB3 Burger SDF model location | 1.3 | `find /opt/ros/jazzy -name "*.sdf" \| grep burger` inside container | Download from ROBOTIS GitHub |
| D3 | How to embed TB3 model in world SDF | 1.3 | Use gz-sim `<include>` SDF syntax with model URI | Inline full model SDF |
| D4 | `teleop_twist_joy` publishes Twist or TwistStamped? | 2.1 | `ros2 interface show` or source inspection inside container | Create adapter node |
| D5 | F310 axis indices (left stick X, right stick Y) | 2.1 | `jstest /dev/input/js0` on host | Trial and error with config |
| D6 | Nav2 params for turtlebot3_world / turtlebot3_house corridors | 3.2 | Start with TB3 defaults, tune `inflation_radius` | Widen corridors in world SDF |
| D7 | tmux vs tmuxinator for dashboard | 4.1 | Check if tmuxinator available in container | Pure tmux script (no extra dep) |
| D8 | FastDDS Discovery Server for WiFi | 5.1 | Test multicast first across WiFi | Configure discovery server |

---

## 3. Phase Breakdown

### Milestone 1: Docker Simulation Environment

#### Phase 1.1 — Docker Infrastructure

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Medium |
| **Depends on** | Nothing |
| **Spec refs** | FR-1.1, FR-1.2, FR-1.3, FR-1.8 |
| **Gotchas** | G1, G2, G3, G6, G7, G14, G15 |

**Deliverables**:
* `docker/Dockerfile.simulator` — FROM `osrf/ros:jazzy-desktop-full`; `userdel -r ubuntu` (G2); install TB3, Nav2, SLAM, Gazebo Harmonic, ros_gz_bridge, teleop_twist_keyboard; set `ENV PATH` for gz binary (G7); set `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (G14)
* `docker/Dockerfile.turtlebot` — FROM `robotis/turtlebot3:jazzy-pc-latest` (G6); similar ENV setup
* `docker/docker-compose.yaml` — `network_mode: host`, `ipc: host`, `GZ_IP=127.0.0.1` (G15), `ROS_DOMAIN_ID=0`, X11 socket mount, volume mounts for `src/`, `scripts/`, `config/`, `.colcon/`
* `entrypoint.sh` — sources `/opt/ros/jazzy/setup.bash` + workspace setup (G17)
* `.colcon/defaults.yaml` — colcon build defaults

**Test-Gates**:
* T1.1a: `sg docker -c "bash scripts/build.sh"` exits 0 (G1)
* T1.1b: `docker exec turtlebot3_simulator which ros2` returns valid path
* T1.1c: `docker exec turtlebot3_robot which ros2` returns valid path
* T1.1d: `docker exec turtlebot3_simulator python3 -c "import rclpy; print('ok')"` prints `ok`

**Notes**: No `.devcontainer/devcontainer.json` — develop on host, use docker exec / attach_terminal.sh.

---

#### Phase 1.2 — Helper Scripts + tb3_bringup Skeleton

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Small |
| **Depends on** | Phase 1.1 |
| **Spec refs** | FR-1.7, FR-1.9 |
| **Gotchas** | G1, G3, G16 |

**Deliverables**:
* `scripts/build.sh` — wraps `docker compose build`; uses `sg docker -c` (G1)
* `scripts/run_docker.sh` — wraps `docker compose up -d`
* `scripts/attach_terminal.sh` — `docker exec -it <container> bash` (G3: only user runs this)
* `scripts/workspace.sh` — workspace setup helper
* `src/tb3_bringup/` — ament_python package skeleton:
  * `package.xml`, `setup.py`, `setup.cfg`, `resource/tb3_bringup`, `tb3_bringup/__init__.py`

**Test-Gates**:
* T1.2a: `colcon build` inside simulator container exits 0 with `tb3_bringup` in output
* T1.2b: `bash scripts/attach_terminal.sh turtlebot3_simulator` opens interactive shell (manual)

---

#### Phase 1.3 — Gazebo World + Bridge + Launch Files

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Large |
| **Depends on** | Phase 1.2 |
| **Spec refs** | FR-1.4, FR-1.5, FR-1.6, FR-1.10 |
| **Gotchas** | G7, G8, G9, G10, G13, G15, G21 |
| **Decisions** | D1, D2, D3 (resolve before coding) |
| **Risk** | R1 (AWS warehouse SDF compat), R7 (package availability) |

**Technical Investigation** (do first):
1. Inside simulator container, run `ros2 pkg prefix aws_robomaker_small_warehouse_world` to find SDF path (D1)
2. Find TB3 Burger SDF model: `find /opt/ros/jazzy -name "*.sdf" | grep -i burger` (D2)
3. Test embedding TB3 in world SDF using `<include>` syntax (D3, G9)
4. Record findings in Decisions Log

**Deliverables**:
* `src/tb3_bringup/worlds/tb3_warehouse.world` — turtlebot3_world obstacle course with TB3 Burger embedded (G9; D1: AWS warehouse not available)
* `src/tb3_bringup/worlds/tb3_house.world` — turtlebot3_house indoor environment with TB3 Burger embedded (G9)
* `src/tb3_bringup/config/bridge_params.yaml` — ros_gz_bridge config: `/cmd_vel` (Twist, G10), `/scan`, `/odom`, `/imu`, `/clock`
* `src/tb3_bringup/launch/sim_bringup.launch.py` — starts Gazebo + bridge + robot_state_publisher using tb3_warehouse world; `headless:=true` arg (G13)
* `src/tb3_bringup/launch/sim_house.launch.py` — same as sim_bringup but uses tb3_house world
* `src/tb3_bringup/launch/teleop.launch.py` — starts `teleop_twist_keyboard` (G11)

**Test-Gates**:
* T1.3a: `gz topic -l` inside container returns `/world/...` topics
* T1.3b: headless launch (`sim_bringup.launch.py headless:=true`) starts without errors, `/clock` published
* T1.3c: `/scan`, `/odom`, `/cmd_vel` accessible — verified via `ros2 topic echo --once` per topic (G4: `ros2 topic list` hangs; see Decisions Log)
* T1.3d: `bridge_params.yaml` uses `geometry_msgs/msg/Twist` for `/cmd_vel` (G10, verified by inspection)

---

#### Phase 1.4 — Integration Test + User Guide

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Small |
| **Depends on** | Phase 1.3 |
| **Spec refs** | Section 9 (user guide requirements) |
| **Gotchas** | G12, G20, G21 |

**Deliverables**:
* `scripts/run_tests.sh` — initial version with M1 test suite; supports `run_tests.sh m1` and `--gui` flag
* `docs/user-guide-milestone-1.md` — prerequisites, quick start, test-gate instructions, troubleshooting, shutdown

**Test-Gates**:
* T1.4a: `bash scripts/run_tests.sh m1` passes all automated checks (headless)
* T1.4b: Human confirms Gazebo GUI shows warehouse + TB3 (manual, `--gui` flag, G21)
* T1.4c: `teleop_twist_keyboard` in attached terminal moves robot in Gazebo (manual, G12, G20)
* T1.4d: Headless mode works: `run_tests.sh m1` passes without DISPLAY set

**Unit Tests** (pytest):
* `src/tb3_bringup/test/test_bridge_params.py` — 8 tests: cmd_vel type, direction, required fields, all topics present
* `src/tb3_bringup/test/test_launch_args.py` — 12 tests: launch files exist, headless default, world references, teleop package, Python syntax

---

### Milestone 2: Gamepad Control (Logitech F310)

#### Phase 2.1 — Technical Investigation

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Small (research only) |
| **Depends on** | Phase 1.4 |
| **Decisions** | D4, D5 |
| **Risk** | R2 (gamepad detection), R3 (TwistStamped) |

**Investigation Tasks**:
1. Connect F310 gamepad, verify `/dev/input/js0` appears on host
2. Run `jstest /dev/input/js0` to map axis indices (D5): confirm left stick X = axis 0, right stick Y = axis 4
3. Inside container, check `teleop_twist_joy` message type (D4):
   * `ros2 pkg xml teleop_twist_joy` or inspect source
   * Check for `publish_stamped_twist` parameter (added in some versions)
   * If publishes `TwistStamped`: plan adapter node or config workaround
4. Test docker device passthrough: add `devices: ["/dev/input/js0"]` to compose, verify `ls /dev/input/js0` inside container

**Output**: Decisions Log entries for D4 and D5. No code deliverables.

---

#### Phase 2.2 — Gamepad Nodes + Launch

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Medium |
| **Depends on** | Phase 2.1 |
| **Spec refs** | FR-2.1, FR-2.2, FR-2.3, FR-2.7, FR-2.9, FR-2.10 |
| **Gotchas** | G3, G10 |

**Deliverables**:
* `src/tb3_controller/` — ament_python package skeleton (setup.py, package.xml, etc.)
* `src/tb3_controller/tb3_controller/gamepad_manager_node.py` — subscribes to `/joy`, initial skeleton (e-stop logic added in Phase 2.3)
* `config/teleop_twist_joy.yaml` — axis/button mapping per D5 results; `scale_linear.x: 0.22`, `scale_angular.yaw: 1.0`
* `src/tb3_bringup/launch/gamepad.launch.py` — starts joy_node + teleop_twist_joy + gamepad_manager
* Updated `docker/Dockerfile.simulator` — add `ros-jazzy-joy`, `ros-jazzy-teleop-twist-joy`
* Updated `docker/docker-compose.yaml` — add `devices: ["/dev/input/js0"]` to simulator service
* If D4 found TwistStamped: `src/tb3_controller/tb3_controller/joy_twist_adapter_node.py`

**Test-Gates**:
* T2.2a: `ros2 topic echo /joy` shows messages when F310 buttons/sticks moved
* T2.2b: Robot moves in Gazebo when right joystick pushed forward
* T2.2c: Robot turns in Gazebo when left joystick moved left/right

---

#### Phase 2.3 — E-Stop / Restart / Reboot + User Guide

| Field | Value |
|---|---|
| **Status** | `COMPLETE` |
| **Completed** | 2026-03-08 |
| **Complexity** | Medium |
| **Depends on** | Phase 2.2 |
| **Spec refs** | FR-2.4, FR-2.5, FR-2.6, FR-2.8 |

**Deliverables**:
* Expand `gamepad_manager_node.py` with e-stop state machine:
  * B button (index 1): publish zero velocity → set `/estop` to `true` (RELIABLE + TRANSIENT_LOCAL QoS) → disable velocity output
  * A button (index 0): clear e-stop → set `/estop` to `false` → re-enable velocity
  * Y button (index 3): reboot — two modes configurable via `reboot_mode` parameter:
    * `lifecycle` (default): ROS lifecycle transitions
    * `container`: implementation deferred — both docker-socket-mount and external-watchdog approaches noted; decide during this phase and record in Decisions Log
* `docs/user-guide-milestone-2.md`
* Updated `scripts/run_tests.sh` — add M2 tests

**Test-Gates**:
* T2.3a: Press B button → robot stops, `/estop` is `true`, joystick produces no motion
* T2.3b: Press A button → e-stop clears, joystick control resumes
* T2.3c: Press Y button (lifecycle mode) → nodes restart via lifecycle transitions
* T2.3d: Press Y button (container mode) → container restarts
* T2.3e: All M1 test-gates still pass (regression)

**Unit Tests** (pytest):
* `src/tb3_controller/test/` — test e-stop state transitions, test button index mapping

---

### Milestone 3: Autonomous Capabilities

#### Phase 3.1 — LiDAR Monitor + Wanderer

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Medium |
| **Depends on** | Phase 2.3 (needs e-stop pattern) |
| **Spec refs** | FR-3.1, FR-3.3 |
| **Gotchas** | G10, G13 |

**Deliverables**:
* `src/tb3_monitor/` — ament_python package skeleton
* `src/tb3_monitor/tb3_monitor/lidar_monitor_node.py` — subscribes to `/scan`, computes min distance, publishes `/closest_obstacle` (`Float32`) at configurable rate (default 5 Hz)
* `src/tb3_controller/tb3_controller/wanderer_node.py` — subscribes to `/scan`, publishes `/cmd_vel`; drives forward when clear, turns when obstacle < threshold (default 0.5m); checks `/estop` before publishing
* Launch file: `src/tb3_bringup/launch/wanderer.launch.py` (or integrate into `capability_demo.launch.py` in Phase 3.3)

**Test-Gates**:
* T3.1a: `/closest_obstacle` publishes `Float32` values > 0 while robot in warehouse
* T3.1b: Wanderer runs 60s without collision; no `/cmd_vel` published when `/scan` min < 0.15m
* T3.1c: Wanderer checks `/estop` — stops when e-stop active
* T3.1d: `colcon build` succeeds for all 3 packages (`tb3_bringup`, `tb3_controller`, `tb3_monitor`)

**Unit Tests** (pytest):
* `src/tb3_monitor/test/` — test min-distance computation with mock LaserScan data
* `src/tb3_controller/test/` — test wanderer obstacle threshold logic

---

#### Phase 3.2 — SLAM + Nav2 Configuration

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Medium |
| **Depends on** | Phase 3.1 (wanderer needed to generate map data) |
| **Spec refs** | FR-3.4, FR-3.5 |
| **Gotchas** | G18, G19 |
| **Decisions** | D6 |

**Deliverables**:
* `config/slam_params.yaml` — `slam_toolbox` in `online_async` mode
* `config/nav2_params.yaml` — tuned for TB3 Burger: `robot_radius: 0.105`, `max_vel_x: 0.22`
* `src/tb3_bringup/launch/slam.launch.py` — starts slam_toolbox with params
* `src/tb3_bringup/launch/nav2.launch.py` — starts full Nav2 stack with custom params

**Test-Gates**:
* T3.2a: SLAM launches, `/map` topic exists
* T3.2b: After wanderer runs 60s, `/map` has non-zero width × height (G19)
* T3.2c: Map saveable via `ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap` (G18)
* T3.2d: Nav2 stack launches without errors
* T3.2e: Nav2 `robot_radius` = 0.105 confirmed in parameter dump

---

#### Phase 3.3 — Patrol Node + Capability Demo Launch

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Medium |
| **Depends on** | Phase 3.2 |
| **Spec refs** | FR-3.2, FR-3.6 |

**Deliverables**:
* `src/tb3_controller/tb3_controller/patrol_node.py` — uses Nav2 `NavigateToPose` action to visit waypoints; configurable via YAML (default: `[[1.0,0.0],[2.0,1.0],[0.0,1.0]]`); checks `/estop`
* `src/tb3_bringup/launch/capability_demo.launch.py` — starts wanderer OR patrol (selectable via `mode` arg) + SLAM + Nav2 + lidar_monitor

**Test-Gates**:
* T3.3a: Patrol visits 3 waypoints; `NavigateToPose` action result = SUCCEEDED for each
* T3.3b: Patrol checks `/estop` — stops when active
* T3.3c: `capability_demo.launch.py mode:=wanderer` starts wanderer stack
* T3.3d: `capability_demo.launch.py mode:=patrol` starts patrol stack

**Unit Tests** (pytest):
* `src/tb3_controller/test/` — test waypoint sequencing logic, test goal tolerance

---

#### Phase 3.4 — Optional Nodes + Integration Test + User Guide

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Small-Medium |
| **Depends on** | Phase 3.3 |
| **Spec refs** | FR-3.7, FR-3.8, FR-3.9 (all optional) |

**Deliverables** (implement as time allows):
* `src/tb3_monitor/tb3_monitor/health_monitor_node.py` — subscribes `/battery_state` + `/imu`, logs at 1 Hz; mock battery publisher for sim
* `src/tb3_monitor/tb3_monitor/tf2_verifier.py` — checks `map→base_link` transform exists and is recent (< 1s); exit 0/1
* `src/tb3_controller/tb3_controller/scan_action_server.py` — 360° rotation action server with degree-progress feedback

**Required deliverables**:
* `docs/user-guide-milestone-3.md`
* Updated `scripts/run_tests.sh` — add M3 tests

**Test-Gates**:
* T3.4a: All M1+M2+M3 core tests pass via `run_tests.sh m3`
* T3.4b: (if built) `tf2_verifier.py` exits 0 with SLAM running
* T3.4c: (if built) `health_monitor_node` logs at ~1 Hz
* T3.4d: (if built) 360° scan action completes with incremental feedback

---

### Milestone 4: TMUX Monitoring Dashboard

#### Phase 4.1 — TMUX Dashboard + User Guide

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Small |
| **Depends on** | Phase 3.4 (all monitoring topics must exist) |
| **Spec refs** | FR-4.1 through FR-4.5 |
| **Gotchas** | G3, G17 |
| **Decisions** | D7 |

**Deliverables**:
* `scripts/tmux_dashboard.sh` (or `config/tmuxinator.yml` if tmuxinator available per D7)
  * Pane 1: `ros2 node list` refreshing periodically
  * Pane 2: `ros2 topic echo /cmd_vel` — live velocity
  * Pane 3: `ros2 topic echo /closest_obstacle` — obstacle distance
  * Pane 4: `ros2 topic echo /odom --field pose.pose.position` — robot position
  * Pane 5: node log output (stdout from key nodes)
* Session name: `tb3_monitor` (deterministic)
* Idempotent: attach to existing session or recreate if dead
* `docs/user-guide-milestone-4.md`

**Test-Gates**:
* T4.1a: TMUX opens with 5+ panes, no error messages
* T4.1b: `/cmd_vel` pane shows data when robot is driven
* T4.1c: Running script twice does not create duplicate sessions
* T4.1d: Session name is `tb3_monitor`

**Note**: Per vision document, no need to re-run previous test-gates for M4.

---

### Milestone 5: RPi 4 Hardware Deployment

#### Phase 5.1 — RPi Setup + Container Build + Network

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Medium |
| **Depends on** | Phase 4.1 |
| **Spec refs** | FR-5.1, FR-5.2, FR-5.3, FR-5.4, FR-5.5, FR-5.8, NFR-5.1, NFR-5.2 |
| **Gotchas** | G1, G2, G3, G5, G6, G14 |
| **Decisions** | D8 |
| **Risk** | R4 (WiFi multicast), R5 (RPi memory) |

**Deliverables**:
* Updated `docker/Dockerfile.turtlebot` — arm64-verified, FROM `robotis/turtlebot3:jazzy-sbc-latest` (G6)
* RPi 4 setup documentation (within user guide or standalone):
  * Ubuntu 24.04 Server install
  * Docker install
  * WiFi config: GL.iNet GL-AXT1800, SSID "JeffTravelRouter-2.4"
  * DDS discovery config (multicast or FastDDS Discovery Server per D8)

**Test-Gates**:
* T5.1a: Turtlebot container builds on RPi 4 (`docker build` exits 0)
* T5.1b: `docker exec turtlebot3_robot which ros2` returns valid path on RPi
* T5.1c: `docker exec turtlebot3_robot python3 -c "import rclpy; print('ok')"` prints `ok` on RPi
* T5.1d: DDS discovery works: `ros2 node list` on NucBoxM6 shows nodes from RPi container

---

#### Phase 5.2 — Integration Testing + User Guide

| Field | Value |
|---|---|
| **Status** | `NOT STARTED` |
| **Completed** | — |
| **Complexity** | Medium |
| **Depends on** | Phase 5.1 |
| **Spec refs** | FR-5.6, FR-5.7 |

**Deliverables**:
* `docs/user-guide-milestone-5.md` — RPi setup, network config, demo operation, troubleshooting
* Updated `scripts/run_tests.sh` — add M5 hardware tests

**Test-Gates**:
* T5.2a: `ros2 node list` on NucBoxM6 shows nodes running on RPi 4 container
* T5.2b: Gamepad on NucBoxM6 moves physical TurtleBot3 robot
* T5.2c: `ros2 topic echo /scan` on NucBoxM6 shows real LiDAR data from RPi 4
* T5.2d: Wanderer node runs on real robot; robot avoids physical walls
* T5.2e: All M1-M3 test-gates pass (adapted for real hardware where applicable)

---

## 4. Cross-Cutting Concerns

### 4.1 `scripts/run_tests.sh` Evolution

| Phase | Changes |
|---|---|
| 1.4 | Initial version — M1 tests (container health, colcon build, gz topics, bridge topics); `--gui` flag |
| 2.3 | Add M2 tests (gamepad input, velocity output, e-stop engage/release) |
| 3.4 | Add M3 tests (wanderer, SLAM, Nav2, patrol, lidar_monitor) |
| 5.2 | Add M5 tests (cross-machine connectivity, hardware sensors) |

Subcommands: `run_tests.sh m1`, `run_tests.sh m2`, `run_tests.sh m3`, `run_tests.sh all`
All tests support `--gui` flag (headless by default, G13).

### 4.2 `docker/docker-compose.yaml` Evolution

| Phase | Changes |
|---|---|
| 1.1 | Base: two containers, `network_mode: host`, `ipc: host`, Fast-DDS, `GZ_IP`, X11 mounts, volume mounts (`src/`, `scripts/`, `config/`, `.colcon/`) |
| 2.2 | Add `/dev/input:/dev/input` bind-mount + `device_cgroup_rules: ["c 13:* rmw"]` + `group_add: ["102"]` to x-ros-common anchor (G25, G26) |
| 5.1 | Separate compose files or profiles for sim-only vs hardware deployment |

### 4.3 Launch File Composition

| Phase | Launch File | Contents |
|---|---|---|
| 1.3 | `sim_bringup.launch.py` | Gazebo (tb3_warehouse world) + bridge + robot_state_publisher |
| 1.3 | `sim_house.launch.py` | Gazebo (tb3_house world) + bridge + robot_state_publisher |
| 1.3 | `teleop.launch.py` | teleop_twist_keyboard |
| 2.2 | `gamepad.launch.py` | joy_node + teleop_twist_joy + gamepad_manager |
| 3.1 | `wanderer.launch.py` | wanderer + lidar_monitor |
| 3.2 | `slam.launch.py` | slam_toolbox online_async |
| 3.2 | `nav2.launch.py` | Full Nav2 stack with custom params |
| 3.3 | `capability_demo.launch.py` | Composites: includes sim_bringup + slam + nav2 + selected behavior |

### 4.4 Package Build Order

`tb3_monitor` → `tb3_controller` → `tb3_bringup`

* `tb3_monitor` has no in-project dependencies
* `tb3_controller` has no direct dependency on `tb3_monitor` (reads `/scan` directly)
* `tb3_bringup` depends on both (launch files reference their nodes)

### 4.5 Testing Framework

* **Unit tests**: pytest — each package gets `test/` directory
* **Integration tests**: `ros2 launch_testing` for node-level integration
* **System tests**: `scripts/run_tests.sh` for full-stack validation
* All tests runnable headless (G13)

---

## 5. Risk Register

| ID | Risk | Likelihood | Impact | Phase | Mitigation |
|---|---|---|---|---|---|
| R1 | AWS warehouse SDF incompatible with Gazebo Harmonic | ~~Medium~~ | ~~High~~ | 1.3 | **Closed** — moot; R7 materialised first (package not in apt) |
| R2 | F310 gamepad not detected in Docker | Low | Medium | 2.1 | `--device /dev/input/js0`; verify with `jstest` |
| R3 | `teleop_twist_joy` publishes TwistStamped | Medium | Medium | 2.1 | Investigate; create adapter node if needed |
| R4 | Fast-DDS multicast fails over WiFi | Medium | High | 5.1 | Test early; fallback to FastDDS Discovery Server |
| R5 | RPi 4 (4GB) insufficient memory | Low | High | 5.1 | `docker stats` monitoring; strip image |
| R6 | Nav2 goal failures in tight corridors | Medium | Medium | 3.2 | Tune `inflation_radius` + planner params |
| R7 | `ros-jazzy-aws-robomaker-small-warehouse-world` package not available | **Materialised** | High | 1.3 | **Resolved** — using `turtlebot3_world` (obstacle maze) and `turtlebot3_house` (indoor) as alternates |

---

## 6. Decisions Log

Record all technical decisions made during execution.

| Date | Phase | Decision | Rationale |
|---|---|---|---|
| 2026-03-08 | 1.1 | `libgl1-mesa-glx` removed from Dockerfile.simulator | Package dropped in Ubuntu 24.04 Noble; `libgl1-mesa-dri` covers it |
| 2026-03-08 | 1.1 | Added `/opt/ros/jazzy/bin` to `ENV PATH` in both Dockerfiles | Base images only add ROS bin via setup.bash, not ENV; needed for `which ros2` in docker exec |
| 2026-03-08 | 1.3 | D1: AWS warehouse world not installed; using `turtlebot3_world` | R7 materialised — package not in apt; turtlebot3_world provides adequate obstacle environment |
| 2026-03-08 | 1.3 | D2: TB3 burger SDF at `/opt/ros/jazzy/share/turtlebot3_gazebo/models/turtlebot3_burger/` | Found via `find`; used as `model://turtlebot3_burger` with `GZ_SIM_RESOURCE_PATH` |
| 2026-03-08 | 1.3 | D3: TB3 embedded in world SDF via `<include><uri>model://turtlebot3_burger</uri></include>` | G9: spawner removed in gz-sim 8.10; world + bridge config kept inside tb3_bringup package |
| 2026-03-08 | 1.3 | `ros2 topic list` hangs in docker exec — use `ros2 topic echo --once` per topic for T1.3c | G4 DDS discovery blocks even with Fast-DDS in exec context; echo/info on specific topics works |
| 2026-03-08 | 2.1 | D4: `teleop_twist_joy` v2.6.5 publishes plain `Twist` by default | `publish_stamped_twist` param exists but defaults to `false`; no adapter node needed; confirmed via binary strings |
| 2026-03-08 | 2.1 | D5: F310 in D-mode, axis layout confirmed via jstest: axis[0]=Left-X (yaw), axis[1]=Left-Y, axis[2]=L-trigger, axis[3]=Right-X, axis[4]=Right-Y (linear), axis[5]=R-trigger, axis[6]=Dpad-X, axis[7]=Dpad-Y | Physically confirmed with jstest /dev/input/js0 |
| 2026-03-08 | 2.1 | D5: Button layout (D-mode): btn[0]=A(green/restart), btn[1]=B(red/estop), btn[2]=X(blue), btn[3]=Y(yellow/reboot), btn[4]=LB, btn[5]=RB, btn[6]=Back, btn[7]=Start, btn[8]=Guide, btn[9]=L-stick, btn[10]=R-stick | Standard F310 D-mode Linux joystick mapping |
| 2026-03-08 | 2.1 | Device passthrough: `/dev/input/js0` added to simulator service in docker-compose.yaml | `docker compose restart` does NOT re-read compose — must use `up --force-recreate`; ros_user has read access (others=r) |
| 2026-03-08 | 2.2 | G25: `ros-jazzy-joy` uses SDL2 — needs `/dev/input/eventX` + device_cgroup_rules + input group | js0 alone insufficient; fixed via /dev/input bind-mount in x-ros-common, cgroup rule `c 13:* rmw`, group_add 102 |
| 2026-03-08 | 2.2 | G26: YAML `<<:` merge does not concat lists — simulator `volumes:` override replaced x-ros-common volumes | Moved /dev/input mount into x-ros-common anchor; never add volumes in per-service override |
| 2026-03-08 | 2.2 | joy_node `use_sim_time: true` blocks publish until /clock received | Always set `use_sim_time: False` on joy_node (reads physical hardware, must use wall clock) |
| 2026-03-08 | 2.3 | E-stop via /cmd_vel_raw relay: teleop → /cmd_vel_raw → gamepad_manager → /cmd_vel | Cleaner than dual-publisher fight; gamepad_manager gates all motion |
| 2026-03-08 | 2.3 | Y button: sends SIGINT to process group, exits all gamepad nodes | Full auto-reboot deferred to Phase 5 hardware (systemd watchdog or docker restart policy) |
| 2026-03-08 | 2.3 | Button edge detection: prev=[0]*len on first message, not prev=buttons | First button press was never detected; fix applied in node and test stub |

---

## 7. Change Log

Record all modifications to this plan.

| Date | Change | Reason |
|---|---|---|
| 2026-03-07 | v1.0 — initial plan created | Generated from specification via Claude Code |
| 2026-03-08 | Milestone 2 complete (phases 2.1–2.3); all test-gates pass | Gamepad control, e-stop, restart, Y-shutdown all verified manually |
| 2026-03-08 | Phase 2.2 complete; T2.2a/b/c pass; G25+G26 added to gotchas.md | joy node works; robot moves with RB+right stick; turns with RB+left stick |
| 2026-03-08 | Phase 2.1 complete; D4+D5 resolved; G24 added to gotchas.md | teleop_twist_joy publishes Twist by default; F310 axis layout decoded; device passthrough confirmed |
| 2026-03-08 | Milestone 1 complete (phases 1.1–1.4) | All automated test gates pass (11/11 via `run_tests.sh m1`) |
| 2026-03-08 | Added `tb3_house.world` + `sim_house.launch.py` | User request; turtlebot3_house is a good SLAM/Nav2 demo environment |
| 2026-03-08 | Config/worlds moved into `src/tb3_bringup/` package | Standard ROS ament_python pattern; avoids extra docker volume mount |
| 2026-03-08 | Added G22, G23 to gotchas.md | libgl1-mesa-glx removed in Ubuntu 24.04; /opt/ros/jazzy/bin missing from ENV PATH |

---

## Appendix A: Original Prompt and Clarification Q&A

### Original Prompt (4th Claude Code Prompt)

> Read @/input/my-vision.md and @/docs/specification.md and create a development plan, to be called @/docs/development-plan.md,
> describing how & when thing are to be created / build.
> If an architecture document is created, also put that in @/docs/.
> The development plan must reflecting an incrementally build approach with testing after each increment.
>
> Make sure to cover the all major software components and their build order,
> key technical decisions to resolve upfront (e.g., which Python library to use),
> a rough phasing that mirrors the sequence reflected in @/input/my-vision.md and @/docs/specification.md,
> and any external dependencies or risks (like software version mismatch).
>
> Produce the plan as a living document so it can update as the project evolves,
> not just a one-time artifact.
> I want it to serves as an ongoing reference rather than going stale after the first few sessions.
> Given the scope of this project — raspberry pi software, a simulator on desktop computer, and incremental testing —
> I want the plan to save significant back-and-forth with Claude Code over the course of development.
>
> Within the development plan document you create (to be called @/docs/development-plan.md), include this prompt,
> all question you ask me, along with my responses.
> Place this in an appendix and reference it at the beginning of the development plan
> and anywhere else in the text when its a useful reference.
>
> Think Hard about what must be done to create a robust plan.
> Use the AskUserQuestions tool for all things that require further clarification.

### Clarification Questions and Responses

**Q1**: Should the plan prescribe a specific Python testing framework, or leave test implementation flexible?
**A1**: pytest + launch_testing — prescribe pytest for unit tests and ros2 launch_testing for integration tests, consistent with ROS 2 conventions.

**Q2**: Should Phase 5.1 (RPi 4 deployment) be split into sub-phases, or kept as one large phase?
**A2**: Split into 2 phases — 5.1 = RPi setup + container build + network config; 5.2 = integration testing + user guide. More testable increments.

**Q3**: For gamepad reboot (container mode), how should the node trigger `docker restart` from inside the container?
**A3**: Defer to implementation — note both options (docker socket mount vs external watchdog) in plan, decide during Phase 2.3.

**Q4**: Should ROS packages include pytest unit tests beyond the integration test-gates in `run_tests.sh`?
**A4**: Yes, basic unit tests — each package gets a `tests/` dir with pytest tests for core logic. Adds ~1 session per milestone.

**Q5**: Should the plan include creating/updating `.devcontainer/devcontainer.json` in Phase 1.1?
**A5**: Skip — not needed. Develop on host, use docker exec / attach_terminal.sh.

---

## Appendix B: File Creation Checklist

All files to be created, grouped by the phase that creates them.

### Phase 1.1
* [ ] `docker/Dockerfile.simulator`
* [ ] `docker/Dockerfile.turtlebot`
* [ ] `docker/docker-compose.yaml`
* [ ] `entrypoint.sh`
* [ ] `.colcon/defaults.yaml`

### Phase 1.2
* [ ] `scripts/build.sh`
* [ ] `scripts/run_docker.sh`
* [ ] `scripts/attach_terminal.sh`
* [ ] `scripts/workspace.sh`
* [ ] `src/tb3_bringup/package.xml`
* [ ] `src/tb3_bringup/setup.py`
* [ ] `src/tb3_bringup/setup.cfg`
* [ ] `src/tb3_bringup/resource/tb3_bringup`
* [ ] `src/tb3_bringup/tb3_bringup/__init__.py`

### Phase 1.3
* [ ] `src/tb3_bringup/worlds/tb3_warehouse.world`
* [ ] `src/tb3_bringup/worlds/tb3_house.world`
* [ ] `src/tb3_bringup/config/bridge_params.yaml`
* [ ] `src/tb3_bringup/launch/sim_bringup.launch.py`
* [ ] `src/tb3_bringup/launch/sim_house.launch.py`
* [ ] `src/tb3_bringup/launch/teleop.launch.py`

### Phase 1.4
* [ ] `scripts/run_tests.sh`
* [ ] `docs/user-guide-milestone-1.md`
* [ ] `src/tb3_bringup/test/test_launch_args.py`

### Phase 2.2
* [ ] `src/tb3_controller/package.xml`
* [ ] `src/tb3_controller/setup.py`
* [ ] `src/tb3_controller/setup.cfg`
* [ ] `src/tb3_controller/resource/tb3_controller`
* [ ] `src/tb3_controller/tb3_controller/__init__.py`
* [ ] `src/tb3_controller/tb3_controller/gamepad_manager_node.py`
* [ ] `src/tb3_bringup/config/teleop_twist_joy.yaml`
* [ ] `src/tb3_bringup/launch/gamepad.launch.py`

### Phase 2.3
* [ ] `docs/user-guide-milestone-2.md`
* [ ] `src/tb3_controller/test/test_gamepad_manager.py`

### Phase 3.1
* [ ] `src/tb3_monitor/package.xml`
* [ ] `src/tb3_monitor/setup.py`
* [ ] `src/tb3_monitor/setup.cfg`
* [ ] `src/tb3_monitor/resource/tb3_monitor`
* [ ] `src/tb3_monitor/tb3_monitor/__init__.py`
* [ ] `src/tb3_monitor/tb3_monitor/lidar_monitor_node.py`
* [ ] `src/tb3_controller/tb3_controller/wanderer_node.py`
* [ ] `src/tb3_monitor/test/test_min_distance.py`
* [ ] `src/tb3_controller/test/test_wanderer_logic.py`

### Phase 3.2
* [ ] `src/tb3_bringup/config/slam_params.yaml`
* [ ] `src/tb3_bringup/config/nav2_params.yaml`
* [ ] `src/tb3_bringup/launch/slam.launch.py`
* [ ] `src/tb3_bringup/launch/nav2.launch.py`

### Phase 3.3
* [ ] `src/tb3_controller/tb3_controller/patrol_node.py`
* [ ] `src/tb3_bringup/launch/capability_demo.launch.py`
* [ ] `src/tb3_controller/test/test_patrol_logic.py`

### Phase 3.4
* [ ] `src/tb3_monitor/tb3_monitor/health_monitor_node.py` (optional)
* [ ] `src/tb3_monitor/tb3_monitor/tf2_verifier.py` (optional)
* [ ] `src/tb3_controller/tb3_controller/scan_action_server.py` (optional)
* [ ] `docs/user-guide-milestone-3.md`

### Phase 4.1
* [ ] `scripts/tmux_dashboard.sh`
* [ ] `docs/user-guide-milestone-4.md`

### Phase 5.1
* [ ] Updated `docker/Dockerfile.turtlebot` (arm64 variant)

### Phase 5.2
* [ ] `docs/user-guide-milestone-5.md`
