# TurtleBot3 Development Plan

> **This is a living document.** Update it at the start of each work session to reflect completed phases,
> new decisions, and discovered risks. Do not let it describe a state that no longer exists.
> See [Section 7 — How to maintain this document](#7-maintaining-this-document).
>
> **Appendix A** contains the original prompt that generated this plan.
> **Appendix B** contains all clarifying Q&A used to shape it.
> Refer to the appendices when re-reading a decision that seems arbitrary.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Technical Decisions](#2-key-technical-decisions)
3. [Risk Register](#3-risk-register)
4. [Software Component Map](#4-software-component-map)
5. [Phase Plan](#5-phase-plan)
6. [Skills Cross-Reference](#6-skills-cross-reference)
7. [Maintaining This Document](#7-maintaining-this-document)
8. [Appendix A — Original Prompt](#appendix-a--original-prompt)
9. [Appendix B — Clarifying Q&A](#appendix-b--clarifying-qa)

---

## 1. Project Overview

Revive a **TurtleBot3 Burger** (Raspberry Pi 4, 4 GB) at Makersmiths using **ROS 2 Jazzy Jalisco** in Docker.
Full context: [`input/my-vision.md`](input/my-vision.md) | Detailed spec: [`specification.md`](specification.md)

### Target robot behaviors (in build order)

| # | Behavior | Requires |
|---|---|---|
| 1 | Teleoperation | `/cmd_vel`, diff-drive controller |
| 2 | Obstacle avoidance | LiDAR `/scan`, reactive stop/avoid |
| 3 | SLAM + mapping | `slam_toolbox`, saved map |
| 4 | Autonomous navigation | `nav2`, pre-built map |

### Two-container deployment model

```text
turtlebot  (robotis/turtlebot3 or custom)  ←── headless; runs on RPi4 in production
simulator  (osrf/ros:jazzy-desktop-full)   ←── Gazebo Harmonic, RViz, rqt; desktop only
```

Both containers share `src/` and communicate over Docker bridge `ros_net` (simulation)
or host LAN with `--network host` (production).

---

## 2. Key Technical Decisions

This section records *what* was decided and *why*. Update when a decision changes.

| # | Decision | Choice | Rationale | Status |
|---|---|---|---|---|
| D1 | ROS distro | Jazzy Jalisco | LTS, Ubuntu 24.04, current | ✅ Final |
| D2 | Gazebo version | **Harmonic** | Default for Jazzy; Gazebo Classic deprecated | ✅ Final |
| D3 | DDS middleware | CycloneDDS (`rmw_cyclonedds_cpp`) | Best multi-machine perf; Jazzy default | ✅ Final |
| D4 | Language | Python (rclpy) | Faster iteration; sufficient for TB3 scale | ✅ Final |
| D5 | Repo structure | Monorepo (`src/` in this repo) | Solo project; simplest CI and atomic commits | ✅ Final |
| D6 | turtlebot base image | `FROM robotis/turtlebot3:jazzy` | Tag confirmed to exist (2026-03-03) | ✅ Final |
| D7 | SLAM library | `slam_toolbox` (online async) | Jazzy default, active maintenance | ✅ Final |
| D8 | Navigation stack | Nav2 | Standard ROS 2 nav; Jazzy-compatible | ✅ Final |
| D9 | Obstacle avoidance approach | Reactive node using `/scan` | Simpler than full Nav2 costmap; build first, then integrate with Nav2 | ✅ Final |
| D10 | tf2 frame prefix | None (single robot) | One robot, no namespace collision | ✅ Final |
| D11 | GUI method | X11 forwarding | Linux desktop only; simplest; no VNC overhead | ✅ Final |
| D12 | Hardware interface (RPi4) | `ros2_control` + TB3 firmware | Standard ROBOTIS TB3 approach | ✅ Final |

### D6 resolution path

✅ **Resolved 2026-03-03**: `robotis/turtlebot3:jazzy` confirmed to exist.
Use `FROM robotis/turtlebot3:jazzy` in `Dockerfile.turtlebot`.
R1 retired. R3 (arm64 support) still needs `docker manifest inspect` verification.

---

## 3. Risk Register

Update status and notes as risks materialize or are retired.

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | `robotis/turtlebot3` has no Jazzy Docker tag | High | High | Verify in Phase 0; fallback: custom Dockerfile from `osrf/ros:jazzy-ros-base` | ✅ Retired — tag confirmed 2026-03-03 |
| R2 | `turtlebot3_gazebo` not ported to Gazebo Harmonic | Medium | High | Use `turtlebot3_gazebo` from `ros-jazzy-turtlebot3-*` apt packages; verify in Phase 1 | ⚠️ Open |
| R3 | RPi4 Docker image is x86-only (no `linux/arm64`) | Medium | High | Check `docker manifest inspect robotis/turtlebot3:jazzy` for arm64 support; may need multi-arch build | ⚠️ Open |
| R4 | Nav2 Jazzy API changes vs Humble | Low | Medium | Pin to `ros-jazzy-navigation2`; follow Jazzy migration guide | ⚠️ Open |
| R5 | CycloneDDS multicast blocked on LAN | Low | Medium | Use unicast peer list in `cyclone_dds.xml`; test with `ros2 doctor` | ⚠️ Open |
| R6 | Gazebo Harmonic + software rendering (`LIBGL_ALWAYS_SOFTWARE`) too slow | Medium | Low | Acceptable for demo; mitigate with reduced world complexity | ⚠️ Open |
| R7 | slam_toolbox map quality poor in simulation | Low | Low | Tune scan match params; use `tb3_house.world` which is well-tested | ⚠️ Open |

---

## 4. Software Component Map

### 4a. Docker images

| Image | Container | Built from | Installed extras |
|---|---|---|---|
| `turtlebot3_dev` (current devcontainer) | `turtlebot` (sim) or standalone | `osrf/ros:jazzy-desktop-full` | `ros-jazzy-turtlebot3*`, `rmw-cyclonedds-cpp` |
| **`turtlebot3_robot`** (to build) | `turtlebot` | `robotis/turtlebot3:jazzy` OR `osrf/ros:jazzy-ros-base` | TB3 packages, CycloneDDS |
| **`turtlebot3_sim`** (to build) | `simulator` | `osrf/ros:jazzy-desktop-full` | Gazebo Harmonic, RViz, Nav2, slam_toolbox |

### 4b. colcon workspace packages (`src/`)

Build order matters — follow the layer model (dependencies flow upward only):

```text
Layer 0 — Hardware abstraction
  (none custom; TB3 firmware + ros2_control come from upstream apt packages)

Layer 1 — Interfaces
  (none custom initially; use std_msgs, sensor_msgs, geometry_msgs, nav_msgs)

Layer 2 — Core logic
  tb3_controller/      velocity controller, obstacle-avoidance node, behavior coordinator

Layer 4 — Bringup (depends on everything)
  tb3_bringup/         all launch files, param files, RViz configs, world files
  tb3_description/     URDF/xacro + meshes (only if not shipped in ROBOTIS image)
```

> **Build order**: `tb3_description` → `tb3_controller` → `tb3_bringup`
> If `tb3_description` is not needed (URDF is in the ROBOTIS image), start with `tb3_controller`.

### 4c. Upstream ROS packages (apt, not custom)

| Package | Purpose | Phase first needed |
|---|---|---|
| `ros-jazzy-turtlebot3` | Meta-package (TB3 core) | Phase 1 |
| `ros-jazzy-turtlebot3-gazebo` | Gazebo Harmonic worlds + models | Phase 4 |
| `ros-jazzy-turtlebot3-teleop` | Keyboard teleoperation | Phase 4 |
| `ros-jazzy-slam-toolbox` | Online SLAM | Phase 5 |
| `ros-jazzy-navigation2` | Nav2 stack | Phase 6 |
| `ros-jazzy-nav2-bringup` | Nav2 launch files | Phase 6 |
| `ros-jazzy-robot-state-publisher` | URDF → tf2 | Phase 4 |
| `ros-jazzy-rmw-cyclonedds-cpp` | DDS middleware | Phase 1 |

### 4d. Key topic/service contracts

Defined here upfront to avoid interface drift between phases:

| Interface | Type | Message | Publisher | Subscriber |
|---|---|---|---|---|
| `/cmd_vel` | Topic | `geometry_msgs/Twist` | teleop / nav2 | diff-drive controller |
| `/scan` | Topic | `sensor_msgs/LaserScan` | LiDAR driver | slam, obstacle_node, costmap |
| `/odom` | Topic | `nav_msgs/Odometry` | diff-drive controller | slam, nav2 |
| `/map` | Topic | `nav_msgs/OccupancyGrid` | slam_toolbox | nav2 map_server, RViz |
| `/tf` | Topic | `tf2_msgs/TFMessage` | robot_state_pub, controllers | all |
| `/navigate_to_pose` | Action | `nav2_msgs/NavigateToPose` | user / mission node | nav2 bt_navigator |

### 4e. tf2 frame tree

```text
map
└── odom                       ← published by slam_toolbox (or nav2_amcl post-SLAM)
    └── base_footprint         ← published by diff-drive controller
        └── base_link
            ├── base_scan      ← static; published by robot_state_publisher (URDF)
            ├── imu_link       ← static
            └── wheel_*_link   ← joint states from robot_state_publisher
```

---

## 5. Phase Plan

Each phase ends with a **test gate** — do not proceed to the next phase until all tests pass.

---

### Phase 0 — Prerequisites verification

**Goal**: Resolve risks R1, R2, R3 before writing any code.

**Deliverables**:

- [ ] Pull `robotis/turtlebot3:jazzy` → confirm tag exists or update D6 to fallback plan
- [ ] Check `docker manifest inspect robotis/turtlebot3:jazzy` → confirm `linux/arm64` support (R3)
- [ ] Confirm `ros-jazzy-turtlebot3-gazebo` exists in apt (`apt-cache search turtlebot3` inside a jazzy container)
- [ ] Update D6 and R1/R2/R3 in this document with findings

**Test gate**: All three checks completed; D6 updated; no showstopper blockers unmitigated.

**Claude Code tasks**: Run `docker pull` and `docker manifest inspect` via `docker exec` into a temporary jazzy container.

---

### Phase 1 — Two-container DevContainer

**Goal**: Both containers build, start, and pass T1 (container startup test).

**Depends on**: Phase 0 (D6 resolved)

**Skills**: `ros_devcontainer`

**Deliverables**:

```text
.devcontainer/
  Dockerfile.turtlebot        ← headless turtlebot container
  Dockerfile.simulator        ← desktop + Gazebo + Nav2
  devcontainer.json           ← VS Code entry (simulator container)
docker-compose.yml            ← services: turtlebot, simulator; network: ros_net
entrypoint.sh                 ← source ROS + workspace on startup
scripts/
  build.sh                    ← build both images
  run_docker.sh               ← start stack (GPU auto-detect)
  attach_terminal.sh
  workspace.sh                ← rosdep + colcon build (run inside container)
config/
  params.yaml                 ← shared TB3 node params
```

**Test gate** (T1):

```bash
# Both containers start
docker-compose up -d
docker exec turtlebot3_turtlebot which ros2   # exits 0
docker exec turtlebot3_simulator which ros2   # exits 0
docker exec turtlebot3_simulator which gazebo  # exits 0
```

**Phase 1 fallback (if R1 confirmed)**: `Dockerfile.turtlebot` uses `FROM osrf/ros:jazzy-ros-base` and installs:

```dockerfile
RUN apt-get install -y ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-msgs \
    ros-jazzy-rmw-cyclonedds-cpp
```

---

### Phase 2 — Workspace scaffold

**Goal**: `src/` has the package skeleton; colcon builds cleanly inside both containers.

**Skills**: `ros_workspace`

**Deliverables**:

```text
src/
  tb3_description/   ← URDF/xacro + meshes (skip if ROBOTIS image has it)
  tb3_controller/    ← placeholder Python package; no logic yet
  tb3_bringup/       ← placeholder; no launch files yet
.colcon/defaults.yaml
```

**Test gate**:

```bash
docker exec turtlebot3_simulator bash -c "
  cd ~/ros2_ws &&
  colcon build --symlink-install 2>&1 | tail -5"
# Expected: 'Summary: X packages finished'
```

---

### Phase 3 — Architecture design

**Goal**: Node graph, topic contracts, and tf2 frame tree locked before any node code is written.
Decisions made here prevent costly refactors in Phases 4–6.

**Skills**: `ros_architect`

**Deliverables**:

```text
docs/architecture.md    ← node graph, communication contracts table, frame tree, QoS profiles
```

**Content required in `docs/architecture.md`**:

1. Node graph (ASCII or Mermaid) covering all four behaviors
2. Full communication contracts table (expand Section 4d above)
3. tf2 frame tree (verify against URDF)
4. QoS profile assignments per interface
5. Lifecycle node list (which nodes need managed startup)
6. Open questions at time of writing

**Test gate**: Document reviewed; Section 4d of this plan updated with any changes; no unresolved blocking questions.

---

### Phase 4 — Teleoperation in simulation

**Goal**: Drive the TurtleBot3 in a Gazebo Harmonic world from the keyboard; odometry responds.

**Skills**: `ros_launch`, `ros_package_node`

**Deliverables**:

```text
tb3_bringup/launch/
  sim_bringup.launch.py       ← starts Gazebo Harmonic + TB3 model + robot_state_publisher
  teleop.launch.py            ← starts turtlebot3_teleop_keyboard (in simulator container)
tb3_bringup/config/
  gazebo_params.yaml
  rviz/teleop.rviz
```

**Test gate** (T3 + T4):

```bash
# T3: Gazebo world loads
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup sim_bringup.launch.py &
  sleep 15 &&
  ros2 topic list | grep /clock"
# Expected: /clock present

# T4: cmd_vel → odom changes
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 topic pub --once /cmd_vel geometry_msgs/Twist '{linear: {x: 0.1}}' &&
  sleep 2 &&
  ros2 topic echo --once /odom" | grep -v "^---"
# Expected: non-zero position in odom
```

---

### Phase 5 — Obstacle avoidance

**Goal**: Robot reactively slows and stops when LiDAR detects an obstacle within threshold distance.
Implemented as a standalone node before full Nav2 (simpler, testable in isolation).

**Skills**: `ros_package_node`, `ros_topics_services_actions`

**Deliverables**:

```text
tb3_controller/
  tb3_controller/obstacle_avoidance_node.py
    ← subscribes /scan; publishes /cmd_vel; stops if min_range < threshold
  tb3_controller/config/obstacle_params.yaml
tb3_bringup/launch/
  obstacle_avoidance.launch.py
```

**Test gate**:

```bash
# Place a wall model in Gazebo near the robot, run obstacle node,
# publish forward velocity, verify robot stops before collision.
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 topic echo --once /scan | python3 -c \"
import sys, json
data = sys.stdin.read()
assert 'ranges' in data, 'No scan data'
print('PASS: /scan publishing')
\""
```

---

### Phase 6 — SLAM + map building

**Goal**: Drive the robot around; `slam_toolbox` builds a map; map is saved to disk.

**Skills**: `ros_launch`

**Deliverables**:

```text
tb3_bringup/launch/
  slam.launch.py              ← sim_bringup + slam_toolbox (online_async)
tb3_bringup/config/
  slam_params.yaml            ← slam_toolbox tuning for TB3
  maps/                       ← saved maps (.yaml + .pgm) go here
```

**Test gate**:

```bash
# /map topic must be publishing after ~30 s of slam launch
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup slam.launch.py &
  sleep 30 &&
  ros2 topic hz /map --window 3 2>&1 | grep Hz"
# Expected: non-zero Hz output

# Map can be saved
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 run nav2_map_server map_saver_cli -f /tmp/test_map &&
  ls /tmp/test_map.yaml"
```

---

### Phase 7 — Autonomous navigation (Nav2)

**Goal**: Robot navigates to a 2D goal pose in a pre-built map without colliding with obstacles.

**Skills**: `ros_launch`, `ros_architect`

**Deliverables**:

```text
tb3_bringup/launch/
  nav2_bringup.launch.py      ← map_server + amcl + nav2 stack + rviz
tb3_bringup/config/
  nav2_params.yaml            ← tuned for TB3 footprint + speeds
  rviz/nav2.rviz
```

**Test gate** (T2):

```bash
# Topic communication test: turtlebot container /scan received by simulator
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  timeout 10 ros2 topic echo --once /scan" | grep -c "ranges"
# Expected: output with ranges data

# Nav2 goal reaches result
# (Manual verification via RViz '2D Nav Goal' click, or scripted via action client)
```

---

### Phase 8 — Automated test suite

**Goal**: All T1–T4 tests run non-interactively via `pytest`; JUnit XML output for CI.

**Skills**: `ros_testing`

**Deliverables**:

```text
tb3_bringup/test/
  test_container_startup.py   ← T1
  test_topic_comms.py         ← T2
  test_gazebo_launch.py       ← T3
  test_drive_command.py       ← T4
scripts/
  run_tests.sh                ← docker exec wrapper; runs pytest; outputs JUnit XML
```

**Test gate**: All four test modules pass with zero failures in a fresh environment.

---

### Phase 9 — Operational documentation

**Goal**: `docs/operations.md` lets a new user operate the simulation without asking questions.

**Deliverables**: `docs/operations.md` covering:

- Starting both containers (`docker-compose up`)
- Opening RViz and Gazebo
- Keyboard teleoperation
- Running obstacle avoidance
- Building a map (SLAM)
- Autonomous navigation to a goal
- Running the automated test suite

---

### Phase 10 — Hardware deployment (Raspberry Pi 4)

**Goal**: `turtlebot` container runs on physical RPi4; teleoperation and navigation work over LAN.

**Depends on**: R3 resolved (arm64 image confirmed or built)

**Deliverables**:

```text
scripts/
  rpi_setup.sh              ← Ubuntu 24.04 + Docker install instructions / script
  deploy_robot.sh           ← pull image + start turtlebot container on RPi4
docker-compose.prod.yml     ← turtlebot service only; --network host
```

**Steps**:

1. Install Ubuntu 24.04 Server on RPi4 (headless)
2. Install Docker CE: `apt install docker.io`
3. Pull or build arm64 turtlebot image
4. Configure LAN: desktop + Pi on same subnet, `ROS_DOMAIN_ID=0`
5. Start turtlebot container with `--network host` (required for DDS multicast)
6. Start simulator container on desktop
7. Verify `/scan` flows from Pi to desktop (T2 variant)

**Test gate**: T2 over physical LAN (same test, different network); teleoperation works end-to-end.

---

## 6. Skills Cross-Reference

| Phase | Skill(s) to invoke |
|---|---|
| 0 | None (bash checks only) |
| 1 | `ros_devcontainer` |
| 2 | `ros_workspace` |
| 3 | `ros_architect` |
| 4 | `ros_launch`, `ros_package_node` |
| 5 | `ros_package_node`, `ros_topics_services_actions` |
| 6 | `ros_launch` |
| 7 | `ros_launch` |
| 8 | `ros_testing` |
| 9 | — (writing only) |
| 10 | `ros_devcontainer` (arm64 Dockerfile variant) |

---

## 7. Maintaining This Document

This document is useful only if it reflects reality. Follow these rules:

### At the start of each Claude Code session

1. Read this document.
2. Update the status column in the Phase 5 table for any phases completed since last session.
3. Update D6 (image decision) and the Risk Register if any risks were resolved.

### When a phase is complete

- Change the phase header to include ✅
- Mark off the deliverable checkboxes
- Add any new risks discovered to Section 3

### When a decision changes

- Update the **Key Technical Decisions** table (Section 2), add a note with date
- If the change affects a phase, update that phase's deliverables

### What NOT to do

- Do not rewrite phases that are done — only add a ✅ and notes
- Do not delete the Risk Register rows — mark them ✅ Retired instead
- Do not add implementation details that belong in code comments

---

## Appendix A — Original Prompt

*Reproduced from [`input/my-claude-prompts.md`](input/my-claude-prompts.md), Section 3:*

> Read `@input/my-vision.md` and `@specification.md` and create a development plan, to be called
> "development-plan.md", describing how & when things are to be created / built.
> The development plan must reflect an incrementally build approach with testing after each increment.
>
> Make sure to cover all major software components and their build order,
> key technical decisions to resolve upfront (e.g., which Python library to use),
> a rough phasing that mirrors the sequence reflected in `@input/my-vision.md` and `@specification.md`,
> and any external dependencies or risks (like software version mismatch).
>
> Produce the plan as a living document it can update as the project evolves,
> not just a one-time artifact.
> I want it to serve as an ongoing reference rather than going stale after the first few sessions.
> Given the scope of this project — raspberry pi software, a simulator on desktop computer, and
> incremental testing — I want the plan to save significant back-and-forth with Claude Code over
> the course of development.
>
> Within the development plan document you create (to be called "development-plan.md"), include this prompt,
> all questions you ask me, along with my responses.
> Place this in an appendix and reference it at the beginning of the development plan
> and anywhere else in the text when it's a useful reference.
>
> Think Hard about what must be done to create a robust plan.
> Use the AskUserQuestions tool for all things that require further clarification.

---

## Appendix B — Clarifying Q&A

*Questions asked by Claude Code on 2026-03-03. Answers given by Jeff.*

---

**Q1: What should the TurtleBot3 actually DO in simulation and on hardware?**
(This drives the entire node architecture.)

**A**: All four: Teleoperation, SLAM + mapping, Autonomous navigation (Nav2), Obstacle avoidance.

*Impact*: Phases planned in behavior-build order: teleop → obstacle avoidance → SLAM → Nav2.
Each phase tests and validates the previous before adding complexity.

---

**Q2: Which Gazebo version should we target?**
(Jazzy officially ships with Gazebo Harmonic, not Gazebo Classic.)

**A**: Gazebo Harmonic (Recommended).

*Impact*: All simulation launch files use `gz sim` (not `gazebo`); use `gz_ros2_control` bridge;
`ros-jazzy-turtlebot3-gazebo` must ship Harmonic-compatible worlds (verify in Phase 0, risk R2).

---

**Q3: Have you verified that `robotis/turtlebot3` has a Jazzy Docker tag?**
(Official ROBOTIS images may only have Humble/Foxy tags.)

**A**: Not verified — need to check.

*Impact*: Phase 0 added specifically to resolve this before any Dockerfile work begins.
Decision D6 remains open until Phase 0 completes. Fallback: custom Dockerfile from
`osrf/ros:jazzy-ros-base`.

---

**Q4: What is the actual current state of the DevContainer files?**
(`.devcontainer/Dockerfile`, `docker-compose.yml`, `scripts/` are referenced in CLAUDE.md as ✅ Done
but do not appear in the repository.)

**A**: Not built yet — Phase 1 still open.

*Impact*: CLAUDE.md status corrected to reflect that Phase 1 (DevContainer) is the next step,
not Phase 2. Phase 0 (prerequisites) added ahead of Phase 1.
