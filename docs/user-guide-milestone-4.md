# User Guide — Milestone 4: TMUX Monitoring Dashboard

**Version**: 1.0
**Date**: 2026-03-09
**Stack**: ROS 2 Jazzy, tmux (in simulator container)

---

## Overview

Milestone 4 adds a tmux monitoring dashboard that runs inside the `turtlebot3_simulator` container.
One command opens a 5-pane session showing live ROS data.

| Pane | Topic / Command | Description |
|---|---|---|
| 0 (top-left) | `watch ros2 node list` | Active nodes, refreshed every 3s |
| 1 (bottom) | `/rosout` | Log output from all running nodes |
| 2 (top-right) | `/cmd_vel` | Live velocity commands |
| 3 (mid-left) | `/closest_obstacle` | LiDAR nearest obstacle distance (m) |
| 4 (mid-right) | `/odom` position | Robot x/y/z from odometry |

---

## Prerequisites

- Milestone 1 complete (`bash scripts/run_tests.sh m1` passes)
- Docker containers running: `sg docker -c "bash scripts/run_docker.sh"`

The dashboard works without the simulation running — panes will wait for their topics to appear.

---

## Quick Start

**Terminal 1** — open dashboard:

```bash
bash scripts/tmux_dashboard.sh
```

This creates (or reattaches to) the `tb3_monitor` tmux session inside the container
and drops you into it.

**Terminal 2** — start simulation (optional, to see live data):

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup sim_bringup.launch.py
```

**Terminal 3** — start autonomous behavior (optional):

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup capability_demo.launch.py   # patrol (default)
# or
ros2 launch tb3_bringup wanderer.launch.py           # wanderer + lidar_monitor
```

---

## Idempotency

Running `tmux_dashboard.sh` a second time reattaches to the existing session rather
than creating a duplicate. To reset the dashboard:

```bash
# Inside the container, or via docker exec:
docker exec turtlebot3_simulator tmux kill-session -t tb3_monitor
bash scripts/tmux_dashboard.sh
```

---

## tmux Key Bindings

The dashboard uses the default tmux prefix (`Ctrl-b`).

| Key | Action |
|---|---|
| `Ctrl-b` then arrow | Move between panes |
| `Ctrl-b` then `z` | Zoom (fullscreen) a pane; repeat to unzoom |
| `Ctrl-b` then `d` | Detach from session (session keeps running) |
| `Ctrl-b` then `[` | Scroll mode — use arrows/PgUp/PgDn, `q` to exit |

---

## Troubleshooting

**Dashboard script says container not running**

```bash
sg docker -c "bash scripts/run_docker.sh"
bash scripts/tmux_dashboard.sh
```

**Panes show "waiting for nodes…" or topic echo hangs**

The simulation is not started. Start it in a separate terminal (see Quick Start above).
`ros2 topic echo` will begin showing data as soon as the topic is published.

**`/closest_obstacle` pane has no data**

`lidar_monitor_node` must be running. It starts automatically with:
- `ros2 launch tb3_bringup wanderer.launch.py`
- `ros2 launch tb3_bringup capability_demo.launch.py`

**`/odom` field not showing position**

The `--field pose.pose.position` filter requires a live `/odom` publisher.
Start the simulation (`sim_bringup.launch.py`) and confirm `/odom` is published:

```bash
docker exec turtlebot3_simulator bash -c \
  "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && \
   timeout 5 ros2 topic echo /odom --once"
```

---

## Automated Tests

```bash
# Requires containers running (sg docker -c "bash scripts/run_docker.sh" first)
bash scripts/run_tests.sh m4

# With manual test instructions:
bash scripts/run_tests.sh m4 --gui
```

Test gates:

| ID | Description | Type |
|---|---|---|
| T4.1a | Dashboard creates 5+ panes, no errors | Automated |
| T4.1b | `/cmd_vel` pane shows Twist messages when robot is driven | Manual (`--gui`) |
| T4.1c | Re-running script reattaches, does not create duplicate session | Automated |
| T4.1d | Session name is `tb3_monitor` | Automated |
