---
name: ros2-jazzy-architect
description: Design and reason about the high-level architecture of a ROS 2 Jazzy Jalisco robotic system. Use this skill when the user asks how to structure a robot's software system, decompose capabilities into nodes and packages, select communication patterns (topics vs services vs actions), choose a middleware/DDS configuration, design a node graph, plan lifecycle management, define a tf2 frame tree, or make system-level trade-offs. This is a design and decision-making skill, not a code generation skill — it produces architecture documents, node graphs, design rationale, and structured recommendations.
---

This skill guides the architectural design of ROS 2 Jazzy Jalisco robotic systems. A ROS 2 architect owns the system's **node graph**, **communication contracts**, **package boundaries**, **execution model**, and **non-functional qualities** (latency, reliability, scalability, maintainability). Good architecture makes the difference between a robot that is easy to extend and debug and one that becomes an unmaintainable tangle of coupled nodes.

---

## 1. Architectural Thinking Process

Before writing a single line of code or a single package name, answer these questions in order:

**1. What does the robot do?**
Define the robot's mission in one sentence. Every architectural decision should trace back to this.

**2. What are the robot's capabilities?**
List the top-level functional capabilities (e.g., perceive, localize, plan, control, interact). These become candidate subsystems.

**3. What are the real-time constraints?**
Identify which data flows are time-critical (sensor ingestion, control loops) vs. best-effort (logging, UI). This drives executor and QoS choices.

**4. What fails, and how badly?**
Define failure modes. Which components can crash and restart gracefully? Which require clean shutdown? This drives lifecycle node decisions.

**5. Who develops what?**
Package boundaries should align with team boundaries (Conway's Law applies to robotics). If two teams own separate capabilities, they should own separate packages.

---

## 2. System Decomposition — Subsystems to Nodes

### Standard Subsystem Map

A well-architected mobile robot typically decomposes into these subsystems. Adapt as needed for your robot type.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ROS 2 Node Graph                         │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  PERCEPTION  │  LOCALIZATION│   PLANNING   │     CONTROL        │
│              │              │              │                    │
│ camera_node  │ slam_node    │ nav2_planner │ diff_drive_ctrl    │
│ lidar_node   │ amcl_node    │ behavior_tree│ joint_ctrl_node    │
│ imu_node     │ ekf_node     │ path_smoother│ vel_smoother_node  │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│                    HARDWARE ABSTRACTION                         │
│   motor_driver_node    sensor_hub_node    power_monitor_node    │
├─────────────────────────────────────────────────────────────────┤
│                     SYSTEM MANAGEMENT                           │
│   lifecycle_manager    diagnostics_node    parameter_server     │
├─────────────────────────────────────────────────────────────────┤
│                       INTERFACES                                │
│     rviz2 / foxglove     web_bridge_node     mission_server     │
└─────────────────────────────────────────────────────────────────┘
```

### Node Granularity Rules

- **One node = one responsibility.** A node that does perception AND control is a design smell.
- **One node = one hardware resource.** Never share a serial port, camera, or GPIO between two nodes.
- **Prefer thin driver nodes.** Hardware driver nodes should only translate hardware data to ROS messages — no business logic.
- **Avoid "god nodes."** If a node has more than ~5 publishers/subscribers, it is doing too much.
- **Lifecycle nodes for anything with hardware.** Any node that opens a device, connects a socket, or allocates significant resources should be a `LifecycleNode`.

---

## 3. Communication Pattern Selection

Choose the right mechanism for every data flow. This is the single most impactful architectural decision.

### Decision Tree

```
Is the data a continuous stream (sensor, odometry, state)?
  └─ YES → Topic (pub/sub)
        └─ Is message loss acceptable? → BEST_EFFORT QoS
        └─ Must every message arrive?  → RELIABLE QoS + KEEP_ALL or KEEP_LAST

Is this a one-time request that expects a fast response (<100ms)?
  └─ YES → Service (client/server)
        └─ Can the caller block? → synchronous call_async + spin_until_future
        └─ Must caller stay responsive? → async with add_done_callback

Is this a long-running task (seconds to minutes) needing progress + cancellation?
  └─ YES → Action (goal/feedback/result)
        └─ Navigation, manipulation, long computations → Action

Is this shared configuration read by many nodes?
  └─ YES → ROS 2 Parameters + Parameter Server (not a topic)

Is this a one-time event broadcast (e.g., mode change, e-stop)?
  └─ YES → Latched topic (TRANSIENT_LOCAL durability) or Service
```

### Communication Contracts Table

Document every interface in your system like this before implementing:

| Interface Name | Type | Message/Srv/Action | Publisher/Server | Subscriber/Client | QoS | Notes |
|---|---|---|---|---|---|---|
| `/scan` | Topic | `sensor_msgs/LaserScan` | `lidar_node` | `slam_node`, `costmap` | BEST_EFFORT | 10 Hz |
| `/cmd_vel` | Topic | `geometry_msgs/Twist` | `nav2_controller` | `diff_drive_ctrl` | RELIABLE | 20 Hz |
| `/navigate_to_pose` | Action | `nav2_msgs/NavigateToPose` | — | `nav2_bt_navigator` | — | Goal + feedback |
| `/set_mode` | Service | `std_srvs/SetBool` | `mission_node` | `state_manager` | — | Blocking OK |

---

## 4. QoS Architecture

QoS profiles must be deliberately matched between publishers and subscribers. Mismatches fail silently — one of the most common ROS 2 bugs.

### Canonical QoS Profiles for Jazzy

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy, LivelinessPolicy
from rclpy.duration import Duration

# ── Sensor data (high rate, loss tolerable) ───────────────────────────────────
SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
    durability=DurabilityPolicy.VOLATILE,
)

# ── Control commands (must arrive, low latency) ───────────────────────────────
CONTROL_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    durability=DurabilityPolicy.VOLATILE,
)

# ── Latched / static data (robot description, map, initial params) ────────────
LATCHED_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)

# ── System events (e-stop, mode changes — must never be missed) ───────────────
SYSTEM_EVENT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_ALL,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)
```

### QoS Compatibility Matrix

| Publisher \ Subscriber | BEST_EFFORT | RELIABLE |
|---|---|---|
| **BEST_EFFORT** | ✅ Compatible | ❌ Incompatible (silent failure) |
| **RELIABLE** | ✅ Compatible (degrades) | ✅ Compatible |

| Publisher \ Subscriber | VOLATILE | TRANSIENT_LOCAL |
|---|---|---|
| **VOLATILE** | ✅ Compatible | ❌ Incompatible |
| **TRANSIENT_LOCAL** | ✅ Compatible | ✅ Compatible |

---

## 5. tf2 Frame Tree Design

The `tf2` frame tree is the spatial backbone of the robot. Design it explicitly — never let it grow organically.

### Standard Mobile Robot Frame Tree

```
map
└── odom
    └── base_footprint
        └── base_link
            ├── laser_link          (LiDAR)
            ├── camera_link
            │   └── camera_optical_link
            ├── imu_link
            ├── wheel_left_link
            └── wheel_right_link
```

### Frame Design Rules

- **`map → odom`** is published by the localization system (SLAM or AMCL). It corrects accumulated drift.
- **`odom → base_footprint`** is published by odometry (wheel encoders, VIO). It is always continuous but drifts.
- **`base_link`** is the robot's rigid body center — all sensor frames are children of this.
- **Sensor frames must be static** (published by `robot_state_publisher` via URDF or `static_transform_publisher`) unless the sensor physically moves.
- **Never publish the same transform from two nodes.** This causes TF tree conflicts and is extremely hard to debug.
- **`camera_optical_link`** is required if you use ROS image pipelines — it rotates the camera frame to OpenCV convention (z forward, x right, y down).

### Broadcaster Ownership Map

| Transform | Published By | Method |
|---|---|---|
| `map → odom` | `slam_toolbox` / `nav2_amcl` | Dynamic TF broadcaster |
| `odom → base_footprint` | `robot_localization` / `diff_drive_ctrl` | Dynamic TF broadcaster |
| `base_link → sensor_*` | `robot_state_publisher` | Static (from URDF) |
| `world → map` | Mission / map server | Static or latched |

---

## 6. Execution Model & Executors

Choosing the wrong executor causes missed deadlines, priority inversion, and subtle timing bugs.

### Executor Selection Guide

| Executor | When to Use |
|---|---|
| `SingleThreadedExecutor` | Simple nodes, prototyping, nodes with no parallel callbacks |
| `MultiThreadedExecutor` | Nodes with multiple independent callbacks that must not block each other |
| `StaticSingleThreadedExecutor` | High-performance nodes where the callback set is fixed at startup |
| Custom executor (rclcpp) | Real-time nodes requiring deterministic scheduling |

### Callback Group Strategy (Jazzy)

In Jazzy, use **callback groups** to control concurrency within a multi-threaded executor:

```python
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup

# Sensor callbacks — can run concurrently with each other
sensor_group = ReentrantCallbackGroup()

# Control callbacks — must never run concurrently (shared state)
control_group = MutuallyExclusiveCallbackGroup()

self.create_subscription(LaserScan, '/scan', self.scan_cb, 10,
                         callback_group=sensor_group)
self.create_timer(0.05, self.control_loop,
                  callback_group=control_group)
```

### Real-Time Considerations

- **Never call `spin_until_future_complete` inside a callback** — this deadlocks a `SingleThreadedExecutor`.
- **Control loops belong in timers**, not in subscription callbacks (rate decoupling).
- **Long-blocking work** (file I/O, network, ML inference) must run in a thread pool or separate process — never block the executor.
- **`rclcpp::spin_some`** is preferred over `spin` in nodes that share a thread with other logic.

---

## 7. Lifecycle Node Architecture

Any node managing hardware, network connections, or expensive resources should be a `LifecycleNode`. The `nav2_lifecycle_manager` can coordinate groups of lifecycle nodes.

### Lifecycle State Machine

```
        on_configure()          on_activate()
[Unconfigured] ──────► [Inactive] ──────────► [Active]
                            ▲                     │
               on_cleanup() │     on_deactivate() │
                            └─────────────────────┘
                                       │ on_shutdown()
                                       ▼
                                  [Finalized]
```

### Which Nodes Need Lifecycle?

| Node Type | Use LifecycleNode? | Reason |
|---|---|---|
| Hardware driver (camera, LiDAR, motor) | **Yes** | Device open/close must be managed |
| Navigation stack nodes (Nav2) | **Yes** | Nav2 requires it |
| Pure computation (transforms, filters) | Optional | Simpler without it |
| Short-lived utility nodes | **No** | Overhead not justified |

### Lifecycle Manager Pattern

```python
# In your bringup launch file — use nav2_lifecycle_manager to coordinate
from launch_ros.actions import Node

lifecycle_manager = Node(
    package='nav2_lifecycle_manager',
    executable='lifecycle_manager',
    name='lifecycle_manager_navigation',
    output='screen',
    parameters=[{
        'autostart': True,
        'node_names': [
            'map_server',
            'amcl',
            'controller_server',
            'planner_server',
            'bt_navigator',
        ],
    }],
)
```

---

## 8. DDS & Middleware Selection

Jazzy supports multiple RMW (ROS Middleware) implementations. Choose deliberately.

| RMW | Package | Best For |
|---|---|---|
| **CycloneDDS** (default in Jazzy) | `rmw_cyclonedds_cpp` | General purpose, excellent multi-machine |
| **FastDDS** | `rmw_fastrtps_cpp` | Compatibility with ROS 2 ecosystem tools, large messages |
| **Zenoh** (new in Jazzy) | `rmw_zenoh_cpp` | Unstable networks, IoT, WAN communication |

```bash
# Set RMW for a session
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# OR for a single node
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ros2 run my_pkg my_node
```

### Multi-Machine / Multi-Robot Domain Isolation

```bash
# All nodes in a robot cell must share the same domain ID
export ROS_DOMAIN_ID=42          # Range: 0–101 (avoid 0 for production)

# For absolute isolation between robots (no cross-talk even on same domain):
export ROS_LOCALHOST_ONLY=1      # Restrict to loopback — single machine only
```

### CycloneDDS Configuration for Reliability

Create `~/cyclone_dds.xml` for tuned multi-robot environments:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>eth0</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>50</MaxAutoParticipantIndex>
    </Discovery>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///home/ros_user/cyclone_dds.xml
```

---

## 9. Security & Safety Architecture

### E-Stop Architecture Pattern

Every mobile robot must have a hardware-independent software e-stop layer:

```
[E-Stop Sources]          [E-Stop Aggregator]       [Actuator Nodes]
  /estop/hardware  ──────►                     ──────► motor_driver_node
  /estop/software  ──────► estop_manager_node  ──────► gripper_node
  /estop/watchdog  ──────►  (publishes /estop)  ──────► (all actuators subscribe)
```

- **E-stop topic must use `SYSTEM_EVENT_QOS`** (RELIABLE + TRANSIENT_LOCAL) so a node that comes up late still receives the current e-stop state.
- **Hardware e-stop is always primary** — software e-stop is a belt-and-suspenders addition.
- **Watchdog pattern**: a heartbeat timer in safety-critical nodes that triggers e-stop if the control loop misses deadlines.

### Namespace Isolation for Multi-Robot

```
/robot1/
  scan, odom, cmd_vel, navigate_to_pose, ...
/robot2/
  scan, odom, cmd_vel, navigate_to_pose, ...
/fleet_manager/
  assign_goal, robot_status, ...
```

Never use global topic names (`/scan`) in multi-robot systems. Always namespace every topic.

---

## 10. Architecture Document Template

When producing an architecture document, always include these sections:

```markdown
# [Robot Name] ROS 2 Architecture

## 1. Mission Statement
One sentence describing what this robot does.

## 2. Capability Map
List of top-level capabilities → mapped to subsystems → mapped to packages.

## 3. Node Graph
ASCII or Mermaid diagram of all nodes, topics, services, and actions.

## 4. Communication Contracts
Table of every topic/service/action interface (see Section 3 above).

## 5. tf2 Frame Tree
Diagram of all coordinate frames and who publishes each transform.

## 6. QoS Profiles
Named profiles used and which interfaces use them.

## 7. Execution Model
Executor type per node, callback groups, any real-time constraints.

## 8. Lifecycle Management
Which nodes are LifecycleNodes, who manages them, startup/shutdown order.

## 9. DDS / Middleware
RMW choice, domain ID, multi-machine configuration.

## 10. Open Questions & Trade-offs
Design decisions that are not yet resolved, with pros/cons.
```

---

## 11. Jazzy Architect Gotchas

- **Jazzy uses CycloneDDS by default** (changed from FastDDS in Humble). If migrating from Humble, explicitly set `RMW_IMPLEMENTATION` to avoid surprise behavior differences.
- **`/tf` and `/tf_static` are global** — they ignore namespaces. In multi-robot systems, use `tf_prefix` in URDF or the `frame_prefix` parameter in `robot_state_publisher`.
- **Action servers are not re-entrant by default** — a new goal cancels the current one unless you implement `GoalResponse::ACCEPT_AND_DEFER` and manage a queue.
- **Parameter changes at runtime**: In Jazzy, `add_on_set_parameters_callback` replaces the old parameter event subscriber pattern. Use it to validate and react to parameter changes.
- **Component nodes vs. standalone nodes**: For production systems, prefer `rclcpp_components` (composable nodes) over standalone executables — they run in the same process and communicate via intra-process channels, eliminating serialization overhead on high-bandwidth topics.
- **`ros2 doctor`** is your first diagnostic tool. Run it to check DDS configuration, RMW, and environment variable correctness before assuming a bug in your code.
- **Never hard-code frame names** (`"base_link"`, `"map"`) as string literals scattered through node code. Declare them as parameters with sensible defaults so they can be remapped without rebuilding.
