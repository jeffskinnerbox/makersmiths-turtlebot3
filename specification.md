# TurtleBot3 Simulation & Deployment Specification

## 1. Project Overview

### Goals

1. Create a complete simulation of TurtleBot3 on Ubuntu 24.04 using two Docker containers.
2. Build and test each container as a standalone unit, then test the two containers together.
3. Automate test execution via Claude Code.
4. Generate operational documentation for the simulated environment.
5. Perform manual testing of the physical TurtleBot3 in the simulation environment.
6. Load Ubuntu 24.04 onto the Raspberry Pi 4, install Docker, and deploy the turtlebot container.

### Current Status

| Item | Status |
|------|--------|
| DevContainer scaffolded & verified | ✅ Done |
| `ros2_ws/` workspace scaffold | ❌ Next |
| Node architecture design | ❌ Pending |
| ROS 2 packages & nodes | ❌ Pending |
| Launch files | ❌ Pending |
| Automated tests | ❌ Pending |
| Operational documentation | ❌ Pending |
| Hardware deployment (RPi 4) | ❌ Pending |

---

## 2. System Architecture

### Two-Container Design

```text
┌─────────────────────────────────────────────────────────────────┐
│  Ubuntu 24.04 Desktop (development & simulation host)           │
│                                                                 │
│  ┌─────────────────────┐      ┌──────────────────────────────┐  │
│  │  turtlebot          │      │  simulator                   │  │
│  │  robotis/turtlebot3 │◄────►│  osrf/ros:jazzy-desktop-full │  │
│  │  Headless           │      │  Gazebo · RViz · rqt         │  │
│  │  ROS 2 Jazzy        │      │  ROS 2 Jazzy                 │  │
│  └─────────────────────┘      └──────────────────────────────┘  │
│           │                               │                     │
│           └──────────── ros_net ──────────┘                     │
│                    (Docker bridge)                              │
└─────────────────────────────────────────────────────────────────┘
                    ↕ X11 forwarding (DISPLAY)
```

### Communication

- **Middleware**: CycloneDDS (`RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`)
- **Domain**: `ROS_DOMAIN_ID=0` on both containers; no DDS router needed
- **Network (simulation)**: Docker bridge network `ros_net` via `docker-compose`
- **Network (production)**: turtlebot container uses `--network host` on RPi 4; same LAN as desktop

---

## 3. Container Specifications

### 3a. `turtlebot` Container

| Property | Value |
|----------|-------|
| Image | `robotis/turtlebot3` (Jazzy tag) |
| Role | Headless robot controller |
| GUI | None |
| Deployment | Raspberry Pi 4, 4 GB RAM, Ubuntu 24.04 (production) |
| Workspace | `/home/ros_user/ros2_ws` |
| Host mount | `./src` → `/home/ros_user/ros2_ws/src` |

**Environment variables:**

```bash
TURTLEBOT3_MODEL=burger
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=0
ROS_DISTRO=jazzy
```

### 3b. `simulator` Container

| Property | Value |
|----------|-------|
| Image | `osrf/ros:jazzy-desktop-full` |
| Role | Gazebo simulation, RViz visualization, rqt tools |
| GUI | X11 forwarding |
| Deployment | Ubuntu 24.04 desktop (development & simulation) |
| Workspace | `/home/ros_user/ros2_ws` |
| Host mount | `./src` → `/home/ros_user/ros2_ws/src` |

**Environment variables:**

```bash
TURTLEBOT3_MODEL=burger
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=0
ROS_DISTRO=jazzy
DISPLAY=$DISPLAY                  # passed from host
LIBGL_ALWAYS_SOFTWARE=1           # software rendering (no GPU)
```

**X11 configuration:**

```yaml
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix
environment:
  - DISPLAY=$DISPLAY
```

**User:** `ros_user` (UID 1000). Base `ubuntu` user must be removed in Dockerfile before creating `ros_user`.

---

## 4. Workspace Structure

A single `src/` directory is host-mounted into both containers. Both containers build from the same source.

```text
turtlebot3/
└── src/                           # host-mounted colcon workspace
    ├── tb3_bringup/               # launch files for sim + robot
    ├── tb3_controller/            # velocity controller node (phase 4+)
    └── tb3_description/           # URDF/meshes (if not in robotis image)
```

Build command (inside either container):

```bash
cd /home/ros_user/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Package layout will be finalized by the `ros_workspace` skill in phase 2.

---

## 5. Development Phases

| Phase | Deliverable | Skills | Status |
|-------|-------------|--------|--------|
| 1 | DevContainer: Dockerfile, scripts, docker-compose | `ros_devcontainer` | ✅ Done |
| 2 | Workspace: `src/` layout, rosdep, colcon config | `ros_workspace` | ❌ |
| 3 | Architecture: node graph, topics, tf2 frame tree | `ros_architect` | ❌ |
| 4 | Packages & nodes (Python/rclpy) | `ros_package_node`, `ros_topics_services_actions` | ❌ |
| 5 | Launch files: sim bringup, robot bringup | `ros_launch` | ❌ |
| 6 | Automated tests (T1–T4) | `ros_testing` | ❌ |
| 7 | Operational documentation | — | ❌ |
| 8 | Hardware deployment on Raspberry Pi 4 | — | ❌ |

---

## 6. Test Requirements

All tests run non-interactively (no TTY). Claude Code executes them via `docker exec`.

| ID | Test | Pass Criteria |
|----|------|---------------|
| T1 | Container startup | Both containers start; `which ros2` exits 0 inside each |
| T2 | Topic communication | `turtlebot` publishes `/scan`; `simulator` receives it (and vice versa) |
| T3 | Gazebo launch | TurtleBot3 world loads without error; `/clock` topic is active |
| T4 | Drive command | Publish `geometry_msgs/Twist` to `/cmd_vel`; odometry on `/odom` changes |

**Test runner**: pytest via `ros_testing` skill; results in JUnit XML for CI compatibility.

---

## 7. Documentation Requirements

After phase 6, produce `docs/operations.md` covering:

- Starting both containers: `docker-compose up`
- Opening RViz and Gazebo
- Teleoperation of the simulated robot
- Running the automated test suite

---

## 8. Hardware Deployment (Phase 8)

Steps for deploying the turtlebot container to the physical Raspberry Pi 4:

1. Install Ubuntu 24.04 Server (headless) on RPi 4
2. Install Docker CE (`apt install docker.io`)
3. Pull `robotis/turtlebot3` image
4. Configure LAN: desktop and Pi on same subnet, `ROS_DOMAIN_ID=0`
5. Run turtlebot container with `--network host` (required for DDS multicast across machines)
6. Run simulator container on Ubuntu desktop (same LAN)

---

## 9. Constraints & Assumptions

| Constraint | Detail |
|------------|--------|
| Host OS | Ubuntu 24.04 only |
| GPU | None — software rendering (`LIBGL_ALWAYS_SOFTWARE=1`) |
| GUI method | X11 forwarding only (no VNC) |
| ROS distro | Jazzy Jalisco only |
| Docker permissions | `sg docker -c "..."` required until fresh login (jeff in docker group) |
| Container user | `ros_user` at UID 1000; `ubuntu` base user removed in Dockerfiles |
| RPi 4 RAM | 4 GB — turtlebot container only; simulator stays on desktop |
