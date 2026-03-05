# TurtleBot3 ROS 2 Architecture

> **Phase 3 deliverable.** Lock this before writing node code.
> Update Section 10 (Open Questions) as decisions are made.

---

## 1. Mission Statement

A TurtleBot3 Burger that teleoperates, stops before obstacles, builds maps with SLAM, and
navigates autonomously in simulation (Gazebo Harmonic) and on the physical Raspberry Pi 4.

---

## 2. Capability Map

| Capability | Phase | Subsystem | Package(s) |
|---|---|---|---|
| Teleoperation | 4 | Control | `turtlebot3_teleop` (upstream) |
| Obstacle avoidance | 5 | Control | `tb3_controller` (custom) |
| SLAM + map building | 6 | Localization | `slam_toolbox` (upstream) |
| Autonomous navigation | 7 | Planning + Control | `nav2_bringup` (upstream) |
| Simulation | 4–9 | Simulation | `turtlebot3_gazebo` + Gazebo Harmonic |
| Visualization | 4+ | Interface | `rviz2` |
| Launch / bringup | all | Bringup | `tb3_bringup` (custom) |

---

## 3. Node Graph

Two deployment contexts share the same topic contracts; only the hardware abstraction differs.

### 3a. Simulation (Phases 4–9) — all nodes in `simulator` container

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    HARDWARE ABSTRACTION (simulated)                 │
│                                                                     │
│   gz sim ──► [gz_ros2_control / diff_drive_controller]             │
│              pub: /scan  /odom  /joint_states  /imu                │
│              sub: /cmd_vel                                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    robot_state_publisher    │  ← URDF (ships in ROBOTIS image)
          │  pub: /tf  /tf_static       │
          │  sub: /joint_states         │
          └──────────────┬──────────────┘
                         │
    ┌────────────────────┼─────────────────────────────────────────┐
    │                    │                                         │
    │  PHASE 4 — TELEOPERATION                                     │
    │  [turtlebot3_teleop_keyboard] ──/cmd_vel──► robot           │
    │                                                              │
    │  PHASE 5 — OBSTACLE AVOIDANCE (custom node in tb3_controller)│
    │  [teleop_keyboard] ──/cmd_vel_raw──►                        │
    │        [obstacle_avoidance_node] ──/cmd_vel──► robot        │
    │                 ▲                                            │
    │              /scan                                           │
    │                                                              │
    │  PHASE 6 — SLAM                                              │
    │  /scan + /tf(odom→base_footprint) ──►                       │
    │        [slam_toolbox] ──► /map  +  map→odom TF              │
    │                                                              │
    │  PHASE 7 — AUTONOMOUS NAVIGATION (Nav2)                     │
    │  /navigate_to_pose ──► [bt_navigator]                       │
    │        ──► [planner_server] ──► /plan                       │
    │        ──► [controller_server] ──/cmd_vel──► robot          │
    │  /scan + /map ──► [costmap_2d] (embedded in servers)        │
    │  /map + /scan ──► [amcl] ──► map→odom TF                   │
    │  [nav2_lifecycle_manager] manages all nav2 nodes            │
    │                                                              │
    │  VISUALIZATION (all phases)                                  │
    │  rviz2 ◄── /scan /odom /map /tf /tf_static /plan           │
    └──────────────────────────────────────────────────────────────┘
```

### 3b. Hardware (Phase 10) — split across two containers

```text
┌─────────────────────────────────┐     ┌──────────────────────────────────────┐
│   turtlebot container (RPi4)    │     │   simulator container (desktop)       │
│                                 │     │                                       │
│  [turtlebot3_node]              │     │  [robot_state_publisher]              │
│    pub: /scan /odom             │─DDS─►  [teleop_keyboard]                   │
│          /joint_states /imu     │◄────│  [obstacle_avoidance_node]            │
│    sub: /cmd_vel                │     │  [slam_toolbox]                       │
│                                 │     │  [nav2 stack]                         │
│  network_mode: host             │     │  [rviz2]                              │
└─────────────────────────────────┘     └──────────────────────────────────────┘
             LAN (DDS multicast over host network, ROS_DOMAIN_ID=0)
```

---

## 4. Communication Contracts

Full table of every ROS interface. Update if any interface changes before coding begins.

| Interface | Type | Message | Publisher | Subscriber(s) | QoS | Rate |
|---|---|---|---|---|---|---|
| `/scan` | Topic | `sensor_msgs/LaserScan` | `turtlebot3_node` / gz bridge | `obstacle_avoidance_node`, `slam_toolbox`, `costmap_2d` | BEST_EFFORT | 5 Hz |
| `/odom` | Topic | `nav_msgs/Odometry` | `turtlebot3_node` / gz bridge | `slam_toolbox`, `robot_localization`, nav2 | RELIABLE | 30 Hz |
| `/cmd_vel` | Topic | `geometry_msgs/Twist` | teleop (Ph4), `obstacle_avoidance_node` (Ph5), `controller_server` (Ph7) | `turtlebot3_node` / gz bridge | RELIABLE | event-driven |
| `/cmd_vel_raw` | Topic | `geometry_msgs/Twist` | `turtlebot3_teleop_keyboard` | `obstacle_avoidance_node` | RELIABLE | event-driven |
| `/joint_states` | Topic | `sensor_msgs/JointState` | `turtlebot3_node` / gz bridge | `robot_state_publisher` | RELIABLE | 30 Hz |
| `/imu` | Topic | `sensor_msgs/Imu` | `turtlebot3_node` / gz bridge | (optional: nav2 EKF) | BEST_EFFORT | 200 Hz |
| `/map` | Topic | `nav_msgs/OccupancyGrid` | `slam_toolbox` (Ph6), `map_server` (Ph7) | `costmap_2d`, `amcl`, `rviz2` | RELIABLE + TRANSIENT_LOCAL | on change |
| `/plan` | Topic | `nav_msgs/Path` | `planner_server` | `controller_server`, `rviz2` | RELIABLE | on demand |
| `/tf` | Topic | `tf2_msgs/TFMessage` | `robot_state_publisher`, `slam_toolbox`, `amcl` | all | RELIABLE | dynamic |
| `/tf_static` | Topic | `tf2_msgs/TFMessage` | `robot_state_publisher` | all | RELIABLE + TRANSIENT_LOCAL | startup |
| `/navigate_to_pose` | Action | `nav2_msgs/NavigateToPose` | user / mission | `bt_navigator` | — | — |
| `/slam_toolbox/save_map` | Service | `slam_toolbox/SaveMap` | user | `slam_toolbox` | — | — |
| `/map_saver/save_map` | Service | `nav2_msgs/SaveMap` | user | `map_saver_server` | — | — |

### `/cmd_vel` arbitration across phases

| Phase | Who publishes `/cmd_vel` | Who publishes to what |
|---|---|---|
| 4 — Teleop | `turtlebot3_teleop_keyboard` | direct → `/cmd_vel` |
| 5 — Obstacle avoidance | `obstacle_avoidance_node` (filter) | teleop → `/cmd_vel_raw`; node → `/cmd_vel` |
| 7 — Nav2 | `controller_server` | direct → `/cmd_vel` (teleop disabled or via `twist_mux`) |

> **Phase 7 open question**: if simultaneous teleop override is wanted during Nav2, add `twist_mux`
> with teleop at higher priority. See Section 10.

---

## 5. tf2 Frame Tree

Based on the TurtleBot3 Burger URDF (ships in ROBOTIS image).

```text
map                          ← published by slam_toolbox (Ph6) / amcl (Ph7)
└── odom                     ← published by turtlebot3_node / diff_drive_controller
    └── base_footprint       ← published by turtlebot3_node / diff_drive_controller
        └── base_link        ← published by robot_state_publisher (static, from URDF)
            ├── base_scan    ← static; robot_state_publisher (URDF)
            ├── imu_link     ← static; robot_state_publisher (URDF)
            ├── wheel_left_link   ← robot_state_publisher (from /joint_states)
            └── wheel_right_link  ← robot_state_publisher (from /joint_states)
```

### Broadcaster ownership

| Transform | Published by | When |
|---|---|---|
| `map → odom` | `slam_toolbox` | Phase 6 (online SLAM) |
| `map → odom` | `amcl` | Phase 7 (localization in saved map) |
| `odom → base_footprint` | `turtlebot3_node` / gz `diff_drive_controller` | always |
| `base_footprint → base_link` and children | `robot_state_publisher` | always (static from URDF) |

> **Rule**: Only one node may publish `map→odom` at a time. `slam_toolbox` is stopped before
> `amcl` is started in Phase 7 bringup. Do not run both simultaneously.

---

## 6. QoS Profiles

Three named profiles used across all nodes. Mismatching publisher/subscriber QoS causes silent
dropped messages.

| Profile name | Reliability | Durability | History | Depth | Used for |
|---|---|---|---|---|---|
| `SENSOR_QOS` | BEST_EFFORT | VOLATILE | KEEP_LAST | 5 | `/scan`, `/imu` |
| `RELIABLE_QOS` | RELIABLE | VOLATILE | KEEP_LAST | 10 | `/odom`, `/cmd_vel`, `/cmd_vel_raw`, `/joint_states` |
| `LATCHED_QOS` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST | 1 | `/map`, `/tf_static` |

In Python (`rclpy`):

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
    durability=DurabilityPolicy.VOLATILE,
)

RELIABLE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    durability=DurabilityPolicy.VOLATILE,
)

LATCHED_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)
```

> **Important**: `turtlebot3_node` publishes `/scan` with `BEST_EFFORT`. Subscribers must also use
> `BEST_EFFORT` (or `RELIABLE`, which degrades gracefully). Never subscribe with
> `RELIABLE + VOLATILE` to a `BEST_EFFORT` publisher — the connection is silently dropped.

---

## 7. Execution Model

All custom nodes use `SingleThreadedExecutor` (default). No parallel callback requirements exist
for `obstacle_avoidance_node` — scan and timer callbacks are both fast and sequential is fine.

| Node | Executor | Notes |
|---|---|---|
| `obstacle_avoidance_node` | SingleThreaded | scan_cb + control_timer; no shared state issues |
| `robot_state_publisher` | SingleThreaded | upstream; no change needed |
| Nav2 nodes | MultiThreaded | managed internally by Nav2 |
| `slam_toolbox` | MultiThreaded | managed internally |

No real-time constraints exist at this scale. The TB3 control loop runs at ~30 Hz; standard Python
executors are sufficient.

---

## 8. Lifecycle Management

| Node | Lifecycle? | Managed by |
|---|---|---|
| `turtlebot3_node` | Yes (upstream) | standalone / `nav2_lifecycle_manager` |
| `map_server` | Yes (upstream) | `nav2_lifecycle_manager` |
| `amcl` | Yes (upstream) | `nav2_lifecycle_manager` |
| `planner_server` | Yes (upstream) | `nav2_lifecycle_manager` |
| `controller_server` | Yes (upstream) | `nav2_lifecycle_manager` |
| `bt_navigator` | Yes (upstream) | `nav2_lifecycle_manager` |
| `slam_toolbox` | Yes (upstream) | `nav2_lifecycle_manager` or standalone |
| `obstacle_avoidance_node` | **No** | standalone (simple node, no hardware) |

`nav2_lifecycle_manager` is included in `tb3_bringup` launch files for Phases 6 and 7.
Set `autostart: true` so nodes activate on launch without manual intervention.

### Startup order (Phase 7 — full nav2)

```text
1. turtlebot3_node (or Gazebo) — hardware up first
2. robot_state_publisher        — URDF frames available
3. map_server                   — map available before localization starts
4. amcl                         — begins localizing once map is ready
5. planner_server + controller_server + bt_navigator
6. nav2_lifecycle_manager       — activates all of the above in order
7. rviz2                        — visualization (non-critical, last)
```

---

## 9. DDS / Middleware

| Setting | Value | Set in |
|---|---|---|
| RMW | `rmw_cyclonedds_cpp` | Dockerfile `ENV` |
| `ROS_DOMAIN_ID` | `0` | Dockerfile `ENV` |
| Network mode | `host` (both containers) | `docker-compose.yml` |
| IPC | `host` | `docker-compose.yml` |

`network_mode: host` enables DDS multicast across machines on the same LAN without any
CycloneDDS unicast configuration. This works in simulation (same host) and production (RPi4 +
desktop on same LAN).

If R5 materializes (multicast blocked), add a `cyclone_dds.xml` with unicast peer list and set
`CYCLONEDDS_URI`. See Risk Register R5 in `development-plan.md`.

---

## 10. Open Questions

Resolve these before the relevant phase begins.

| # | Question | Phase | Options |
|---|---|---|---|
| Q1 | Does `obstacle_avoidance_node` act as a filter (`/cmd_vel_raw` → `/cmd_vel`) or a standalone publisher? Filter is cleaner (teleop intent preserved; node zeroes velocity). Standalone requires a `twist_mux`. | 5 | **Filter (recommended)** vs. standalone + twist_mux |
| Q2 | Does Phase 7 need `twist_mux` for simultaneous teleop override during Nav2? Nav2 has its own recoveries; probably not needed for workshop scope. | 7 | Add `twist_mux` vs. disable teleop during nav2 |
| Q3 | Does `slam_toolbox` shutdown need to be explicit before starting `amcl`, or does `nav2_lifecycle_manager` handle the transition cleanly? | 7 | Separate launch files (safe) vs. combined bringup with lifecycle ordering |
| Q4 | Is the TB3 URDF frame tree identical to what is shown in Section 5? Verify by running `ros2 topic echo /tf_static` inside a running container with `robot_state_publisher`. | 4 | — |
| Q5 | Is `/imu` needed for any node in Phases 4–7? (Not currently listed as a subscriber.) If not, it can be ignored until Phase 10. | 4 | Ignore vs. feed into `robot_localization` EKF |
