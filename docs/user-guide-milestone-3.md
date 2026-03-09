# User Guide — Milestone 3: Autonomous Capabilities

**Version**: 1.0
**Date**: 2026-03-09
**Stack**: ROS 2 Jazzy, Gazebo Harmonic, SLAM Toolbox, Nav2

---

## Overview

Milestone 3 adds fully autonomous capabilities to the TurtleBot3 simulator:

| Capability | Launch / Command | Description |
|---|---|---|
| LiDAR monitor | `wanderer.launch.py` | Publishes closest obstacle distance |
| Wanderer | `wanderer.launch.py` | Reactive obstacle avoidance |
| SLAM | `slam.launch.py` | Builds a live occupancy map |
| Nav2 | `nav2.launch.py` | Path planning + navigation stack |
| Patrol | `capability_demo.launch.py` | Waypoint patrol via Nav2 |
| Health monitor | `ros2 run tb3_monitor health_monitor` | Battery + IMU status |
| TF2 verifier | `ros2 run tb3_monitor tf2_verifier` | Checks map→base_link TF |
| 360° scan action | `ros2 run tb3_controller scan_action_server` | Rotation action server |

---

## Prerequisites

- Milestone 1 + 2 complete (`bash scripts/run_tests.sh all` passes)
- Docker containers running: `sg docker -c "bash scripts/run_docker.sh"`
- Terminal helper: `bash scripts/attach_terminal.sh turtlebot3_simulator`

---

## Quick Start: Capability Demo

The `capability_demo.launch.py` runs the full M3 stack in one command.

**Terminal 1** — Simulation:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup sim_bringup.launch.py
```

**Terminal 2** — Autonomous demo:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash

# Patrol mode (default) — visits 3 waypoints via Nav2
ros2 launch tb3_bringup capability_demo.launch.py

# Wanderer mode — reactive obstacle avoidance
ros2 launch tb3_bringup capability_demo.launch.py mode:=wanderer
```

Wait ~30–60 seconds for SLAM and Nav2 to initialize. In patrol mode, watch the
terminal for:

```
[patrol]: Patrol → waypoint [0] (1.00, 0.00)
[patrol]: Waypoint [0] reached!
[patrol]: Patrol → waypoint [1] (2.00, 1.00)
```

---

## Launch Files

### `sim_bringup.launch.py` — Gazebo simulation

```bash
ros2 launch tb3_bringup sim_bringup.launch.py             # GUI
ros2 launch tb3_bringup sim_bringup.launch.py headless:=true  # headless
ros2 launch tb3_bringup sim_house.launch.py               # indoor house world
```

### `wanderer.launch.py` — LiDAR monitor + wanderer

```bash
ros2 launch tb3_bringup wanderer.launch.py
```

Starts:
- `lidar_monitor` — `/scan` → `/closest_obstacle` (Float32, 5 Hz)
- `wanderer` — drives forward until obstacle < 0.5 m, then turns

### `slam.launch.py` — SLAM mapping

```bash
ros2 launch tb3_bringup slam.launch.py
```

Starts `slam_toolbox online_async`. Publishes `/map` and the `map→odom` TF.
Map fills as the robot moves. Save map with:

```bash
# G18 — do NOT use map_saver_cli (fails with QoS error)
timeout 20 ros2 service call /slam_toolbox/save_map \
  slam_toolbox/srv/SaveMap '{name: {data: "/tmp/my_map"}}'
```

### `nav2.launch.py` — Navigation stack

```bash
ros2 launch tb3_bringup nav2.launch.py
```

Starts the full Nav2 stack (DWB controller, NavFn planner, bt_navigator).
Requires `slam.launch.py` to be running first — SLAM provides the map→odom TF.

### `capability_demo.launch.py` — Full demo

```bash
ros2 launch tb3_bringup capability_demo.launch.py mode:=patrol    # default
ros2 launch tb3_bringup capability_demo.launch.py mode:=wanderer
```

Always starts: SLAM + Nav2 + lidar_monitor + one of (wanderer | patrol).

---

## Patrol Node

The patrol node cycles through configurable waypoints using Nav2's
`NavigateToPose` action.

**Default waypoints** (map frame, metres):

| # | x | y |
|---|---|---|
| 0 | 1.0 | 0.0 |
| 1 | 2.0 | 1.0 |
| 2 | 0.0 | 1.0 |

**Custom waypoints** — override at launch:

```bash
ros2 launch tb3_bringup capability_demo.launch.py \
  mode:=patrol \
  --ros-args -p patrol.waypoints:="[1.5, 0.0, 3.0, 2.0, 0.0, 2.0]"
```

Waypoints are a flat `[x0, y0, x1, y1, …]` list. The node loops indefinitely
(`loop:=true` by default).

**E-stop** — Press **B** on the F310 gamepad (or publish `/estop=true`) to
cancel the current navigation goal. Press **A** to clear and resume patrol.

---

## LiDAR Monitor

```bash
# Check closest obstacle distance
ros2 topic echo /closest_obstacle
```

Publishes `std_msgs/Float32` at 5 Hz. Value is the minimum valid LiDAR
range in metres (0.0 = no valid reading / too close).

---

## Health Monitor

```bash
# Terminal 1 — mock battery (simulation only; real hardware publishes /battery_state natively)
ros2 run tb3_monitor mock_battery

# Terminal 2 — health monitor
ros2 run tb3_monitor health_monitor
```

Logs at 1 Hz:

```
[health_monitor]: battery: 12.00V  75% | imu: yaw=0.0°  ω=(0.00,0.00,0.01)rad/s
```

On real hardware the mock_battery node is not needed — the robot's OpenCR
board publishes `/battery_state` natively.

---

## TF2 Verifier

One-shot diagnostic script: exits 0 if `map→base_link` TF is available and
fresh, exits 1 if unavailable or stale.

```bash
# Requires SLAM to be running
ros2 run tb3_monitor tf2_verifier

# Custom parameters
ros2 run tb3_monitor tf2_verifier --ros-args -p max_age:=2.0 -p timeout:=8.0
```

Expected output when healthy:

```
[tf2_verifier]: Waiting up to 5.0s for map→base_link TF…
[tf2_verifier]: map→base_link OK — age=0.012s (max_age=1.0s) — PASS
```

Use as a test-gate in scripts:

```bash
ros2 run tb3_monitor tf2_verifier && echo "TF OK" || echo "TF MISSING"
```

---

## 360° Scan Action Server

Rotation action server on `/tb3_scan_360` using `nav2_msgs/action/Spin`.

```bash
# Terminal 1 — start sim
ros2 launch tb3_bringup sim_bringup.launch.py

# Terminal 2 — start server
ros2 run tb3_controller scan_action_server

# Terminal 3 — send 360° goal (6.283 rad = 2π)
ros2 action send_goal /tb3_scan_360 nav2_msgs/action/Spin \
  '{target_yaw: 6.283}' --feedback
```

Expected output:

```
Feedback:
  angular_distance_traveled: 1.234

Result:
  total_elapsed_time:
    sec: 7
    nanosec: 12345678
```

The server uses `/odom` to track actual yaw and publishes `/cmd_vel` to rotate.
Positive `target_yaw` = CCW, negative = CW.

---

## Topic Reference

| Topic | Type | Published by |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | Gazebo (LiDAR) |
| `/odom` | `nav_msgs/Odometry` | Gazebo (wheel encoders) |
| `/cmd_vel` | `geometry_msgs/Twist` | wanderer / patrol / gamepad / scan_action_server |
| `/closest_obstacle` | `std_msgs/Float32` | lidar_monitor |
| `/estop` | `std_msgs/Bool` | gamepad_manager (RELIABLE + TRANSIENT_LOCAL) |
| `/map` | `nav_msgs/OccupancyGrid` | slam_toolbox |
| `/battery_state` | `sensor_msgs/BatteryState` | mock_battery (sim) / OpenCR (hw) |
| `/imu` | `sensor_msgs/Imu` | Gazebo (sim) / OpenCR (hw) |

---

## Running Automated Tests

```bash
# All M3 tests (headless)
bash scripts/run_tests.sh m3

# All milestones
bash scripts/run_tests.sh all

# With manual test prompts
bash scripts/run_tests.sh m3 --gui
```

Automated checks:
- Build: `colcon build` (all 3 packages)
- Unit tests: wanderer logic, patrol logic (pytest, no ROS)
- Integration: wanderer publishes `/cmd_vel`, `/closest_obstacle`
- SLAM: `/map` publishes, non-zero width after robot moves, save via service
- Nav2: `bt_navigator` node running, `robot_radius=0.105`
- Phase 3.3: `capability_demo` starts correct node per mode
- Phase 3.4: `health_monitor` logs, `tf2_verifier` exits 0 with SLAM running

---

## Troubleshooting

**Patrol robot doesn't move after launch**
- Wait 30–60s for Nav2 lifecycle to activate fully
- Check SLAM is running: `ros2 topic echo /map --once`
- Confirm map→odom TF: `ros2 run tb3_monitor tf2_verifier`

**NavigateToPose goal rejected**
- Nav2 not fully active yet — wait for `bt_navigator` log: `"Lifecycle transition successful"`
- Verify no active e-stop: `ros2 topic echo /estop --once`

**`/map` is 0×0 (empty)**
- G19: map starts empty until robot moves and LiDAR accumulates scans
- Run wanderer for 30+ seconds before patrol

**`map_saver_cli` fails**
- G18: use `slam_toolbox/save_map` service instead (see slam.launch.py commands above)

**TF2 verifier exits 1 (stale)**
- SLAM not running, or robot hasn't moved yet
- Check: `ros2 launch tb3_bringup slam.launch.py` then drive a few seconds

**scan_action_server: "No /odom data"**
- Simulation not running — start `sim_bringup.launch.py` first

---

## Shutdown

```bash
# Stop autonomous stack
Ctrl+C in Terminal 2

# Stop simulation
Ctrl+C in Terminal 1

# Stop containers
docker compose -f docker/docker-compose.yaml down
```
