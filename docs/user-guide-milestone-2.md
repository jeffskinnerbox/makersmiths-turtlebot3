# User Guide — Milestone 2: Gamepad Control

**Version**: 1.0
**Date**: 2026-03-08
**Hardware**: Logitech F310 Gamepad (D-mode, USB)

---

## Prerequisites

- Milestone 1 complete and working (`bash scripts/run_tests.sh m1` passes)
- F310 plugged into host USB
- Host: `xhost +local:docker` run once per login session (for Gazebo GUI)

Verify the F310 is detected:

```bash
cat /proc/bus/input/devices | grep "F310"
# Should show: N: Name="Logitech Gamepad F310"
```

---

## Quick Start

**Terminal 1** — Simulation:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup sim_bringup.launch.py
```

**Terminal 2** — Gamepad:

```bash
bash scripts/attach_terminal.sh turtlebot3_simulator
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 launch tb3_bringup gamepad.launch.py
```

Wait for Gazebo to fully load (robot visible in world), then drive.

---

## Driving Controls

| Action | Input |
|---|---|
| Enable motion | Hold **RB** (right bumper) |
| Move forward / backward | Hold RB + **right stick** up / down |
| Turn left / right | Hold RB + **left stick** left / right |
| Turbo speed (0.4 m/s) | Hold **LB** instead of RB |

> **Release RB** at any time to stop motion immediately (teleop safety).

Speed limits: normal 0.22 m/s, turbo 0.4 m/s.

---

## Safety Buttons

| Button | Color | Action |
|---|---|---|
| **B** | Red | **Emergency stop** — zero velocity, locks out joystick |
| **A** | Green | **Clear e-stop** — resumes normal joystick control |
| **Y** | Yellow | **Shutdown** — stops motion and exits gamepad nodes |

### E-Stop Details

- Pressing **B** immediately publishes zero `/cmd_vel` and sets `/estop=true`
- While e-stopped, joystick input is completely blocked at the `gamepad_manager` node
- `/estop` topic uses RELIABLE + TRANSIENT_LOCAL QoS — any new subscriber gets the current state
- Press **A** to clear and resume

---

## Topic Reference

| Topic | Type | Description |
|---|---|---|
| `/joy` | `sensor_msgs/Joy` | Raw gamepad axes and buttons |
| `/cmd_vel_raw` | `geometry_msgs/Twist` | Teleop output (pre-gate) |
| `/cmd_vel` | `geometry_msgs/Twist` | Gated velocity command to robot |
| `/estop` | `std_msgs/Bool` | E-stop state (latched) |

Monitor e-stop state:

```bash
ros2 topic echo /estop
```

---

## Running Automated Tests

```bash
# Headless (automated checks only — F310 must be plugged in)
bash scripts/run_tests.sh m2

# All milestones
bash scripts/run_tests.sh all

# With manual test prompts
bash scripts/run_tests.sh m2 --gui
```

Automated checks verify: `/joy` publishing, `/estop` latched initial state, `/cmd_vel_raw` remapping, and all 12 unit tests for the e-stop state machine.

---

## Troubleshooting

**`joy_enumerate_devices` shows no gamepad**
- Check F310 is plugged in and in **D-mode** (switch on back of controller)
- Verify: `cat /proc/bus/input/devices | grep F310`
- Container must have been started *after* plugging in the controller

**Robot doesn't move when holding RB + right stick**
- Source both: `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash`
- Confirm sim is running: `/clock` topic should be publishing
- Check e-stop not active: `ros2 topic echo /estop --once`

**Gamepad launch fails with "Package not found"**
- Build workspace: `cd ~/ros2_ws && colcon build`
- Source install: `source ~/ros2_ws/install/setup.bash`

**Motion is inverted (forward goes backward)**
- Edit `src/tb3_bringup/config/teleop_twist_joy.yaml`
- Negate `scale_linear.x` (change `-0.22` to `0.22`)
- Rebuild: `colcon build --packages-select tb3_bringup`

---

## Shutdown

```bash
# Stop gamepad nodes
Ctrl+C in Terminal 2  (or press Y button)

# Stop simulation
Ctrl+C in Terminal 1

# Stop containers
docker compose -f docker/docker-compose.yaml down
```
