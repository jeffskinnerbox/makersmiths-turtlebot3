# User Guide — Milestone 1: Docker Simulation Environment

**Version**: 1.0 | **Date**: 2026-03-08

This guide covers building, running, and testing the TurtleBot3 simulation
environment. By the end you will have both Docker containers running, Gazebo
Harmonic simulating a TurtleBot3 Burger, and the ROS 2 bridge publishing sensor
and odometry data.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Ubuntu 24.04 | Host OS |
| Docker Engine | Install: `sudo apt install docker.io` |
| Docker group | `sudo usermod -aG docker $USER` then log out/in |
| X11 (for GUI) | Standard Ubuntu desktop; run `xhost +local:docker` once per session |

> **Fresh install note**: If you just added yourself to the `docker` group,
> prefix all `docker`/`bash scripts/` commands with `sg docker -c "..."` until
> you log out and back in.

---

## Quick Start

### 1. Build the Docker images (~10–20 min first time)

```bash
sg docker -c "bash scripts/build.sh"
```

This builds two images:
- `docker_turtlebot3_simulator` — Gazebo Harmonic + Nav2 + SLAM + ROS bridge
- `docker_turtlebot3_robot` — TurtleBot3 packages (used in Milestone 5 for RPi)

### 2. Start the containers

```bash
sg docker -c "bash scripts/run_docker.sh"
```

Both containers start detached. The simulator is ready when `docker ps` shows
both containers with status `Up`.

### 3. Launch the simulation

Open a terminal and attach to the simulator container:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
```

Inside the container, launch simulation (choose a world):

```bash
# Option A: turtlebot3_world — obstacle course maze
ros2 launch tb3_bringup sim_bringup.launch.py

# Option B: turtlebot3_house — indoor house with rooms (good for SLAM demos)
ros2 launch tb3_bringup sim_house.launch.py
```

Gazebo opens with the selected world and the TurtleBot3 Burger spawned at
position (-2.0, -0.5).

### 4. Drive the robot with keyboard

In a second terminal, attach again and launch teleop:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
ros2 launch tb3_bringup teleop.launch.py
```

Keyboard controls:

| Key | Action |
|---|---|
| `i` | Forward |
| `,` | Backward |
| `j` | Turn left |
| `l` | Turn right |
| `k` | Stop |

> Hold the key to keep moving — releasing stops the robot.

### 5. Stop the simulation

In the container terminal: `Ctrl+C`

To stop all containers from the host:

```bash
docker compose -f docker/docker-compose.yaml down
```

---

## Available Worlds

| Launch file | World | Best for |
|---|---|---|
| `sim_bringup.launch.py` | `turtlebot3_world` (obstacle course maze) | Basic sensor validation, wanderer |
| `sim_house.launch.py` | `turtlebot3_house` (indoor rooms + corridors) | SLAM mapping, Nav2 navigation |

Both worlds embed the TurtleBot3 Burger at pose `(-2.0, -0.5, 0)`.

---

## Running the Test Suite

### Automated tests (headless)

```bash
bash scripts/run_tests.sh m1
```

This runs all Milestone 1 automated tests and reports pass/fail. Expected
output:

```
══════════════════════════════════════════
  TurtleBot3 Test Runner
══════════════════════════════════════════
  Milestone : m1
  GUI mode  : false

▶ Milestone 1: Docker Simulation Environment
  Container health:
  PASS  T1.1b  ros2 CLI in simulator
  PASS  T1.1c  ros2 CLI in robot
  PASS  T1.1d  rclpy importable in simulator
  Workspace:
  PASS  T1.2a  colcon build (tb3_bringup)
  Config:
  PASS  T1.3d  bridge_params.yaml uses geometry_msgs/msg/Twist for /cmd_vel
  Unit tests (pytest):
  PASS  T1.4u  pytest tb3_bringup
  Simulation (headless):
  PASS  T1.3a  gz topics visible (/world/...)
  PASS  T1.3b  /clock published
  PASS  T1.3c  /scan published
  PASS  T1.3c  /odom published
  PASS  T1.3c  /cmd_vel accessible

══════════════════════════════════════════
  Results: 11 passed  0 failed  0 skipped
══════════════════════════════════════════
```

### With GUI tests

```bash
xhost +local:docker          # allow Docker X11 access (once per login)
bash scripts/run_tests.sh m1 --gui
```

The `--gui` flag adds T1.4b/T1.4c as manual checks with instructions printed
to the terminal. Confirm them visually in Gazebo.

---

## Manual Test Gates

### T1.4b — Gazebo GUI shows world + TurtleBot3

1. `bash scripts/attach_terminal.sh turtlebot3_simulator`
2. `ros2 launch tb3_bringup sim_bringup.launch.py`
3. Confirm Gazebo window opens and shows the maze with the orange TB3 Burger.

### T1.4c — Keyboard teleop moves the robot

1. Launch simulation (T1.4b above)
2. In a second terminal: `bash scripts/attach_terminal.sh turtlebot3_simulator`
3. `ros2 launch tb3_bringup teleop.launch.py`
4. Press `i` — confirm robot moves forward in Gazebo.
5. Press `k` — confirm robot stops.

---

## Troubleshooting

### `docker: permission denied`

```bash
# Option 1: prefix with sg until re-login
sg docker -c "bash scripts/build.sh"

# Option 2: fresh login after usermod
sudo usermod -aG docker $USER
# log out and back in
```

### Gazebo GUI does not open

```bash
xhost +local:docker          # run once per session on the host
```

If you see `libGL error` or a blank window, your host may lack a compatible
OpenGL driver. Try:

```bash
docker exec turtlebot3_simulator bash -c "export LIBGL_ALWAYS_SOFTWARE=1 && \
  ros2 launch tb3_bringup sim_bringup.launch.py"
```

### `/clock` not publishing after launch

The bridge takes ~10–15 s to connect to Gazebo. Wait and retry:

```bash
timeout 10 ros2 topic echo /clock --once
```

If still failing, check that `GZ_IP=127.0.0.1` is set:

```bash
docker exec turtlebot3_simulator printenv GZ_IP
```

### `ros2 topic list` hangs

Known issue (G4): DDS peer discovery blocks `ros2 topic list`. Use per-topic
checks instead:

```bash
timeout 8 ros2 topic echo /scan --once
timeout 8 ros2 topic info /cmd_vel
```

### colcon build fails with import errors

Always source both setup files before building:

```bash
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
cd ~/ros2_ws && colcon build
```

---

## Shutdown Procedure

1. `Ctrl+C` in any active `ros2 launch` terminal
2. From the host: `docker compose -f docker/docker-compose.yaml down`

---

## What's Next

Milestone 2 adds Logitech F310 gamepad control with e-stop functionality.
See `docs/user-guide-milestone-2.md` (created in Phase 2.3).
