# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reviving a **TurtleBot3 Burger** (Raspberry Pi 4, 4 GB) at Makersmiths using **ROS 2 Jazzy Jalisco** in Docker DevContainers.
See `input/my-vision.md` for full context.

**Current status**: Phase 0 ✅, Phase 1 ✅, Phase 2 ✅, Phase 3 ✅, Phase 4 ✅, Phase 5 ✅, Phase 6 ✅ (T6 passed 2026-03-04). Next: Phase 7 — autonomous navigation (Nav2).
See [`development-plan.md`](development-plan.md) for full phase plan and living decisions log.

**Session-start protocol** — at the start of each work session:
1. Read `development-plan.md`.
2. Update phase statuses, D6 (image decision), and the Risk Register per Section 7 of that document.
3. Update the phase status line in this file to match.

### Target Architecture: Two-Container System

| Container | Image | Role |
|---|---|---|
| `turtlebot` | `robotis/turtlebot3` | Headless robot controller |
| `simulator` | `osrf/ros:jazzy-desktop-full` | Gazebo, RViz, rqt, full desktop |

Containers communicate over a shared Docker network. The `turtlebot` container runs on the physical Raspberry Pi 4 in production.

### Development Phases

0. **Prerequisites** ✅ — D6/R1/R2 resolved; R3 (arm64) deferred to Phase 10
1. **DevContainer** ✅ — T1 passed 2026-03-03; gz at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`
2. **Workspace scaffold** ✅ — `src/` packages, rosdep, colcon config (2026-03-03)
3. **Architecture design** ✅ — Node graph, topic contracts, tf2 frame tree (`docs/architecture.md`)
4. **Teleoperation in sim** ✅ — T3+T4 passed 2026-03-05; GZ_IP+Fast-DDS fixes required
5. **Obstacle avoidance** ✅ — Reactive node using `/scan`; T5 passed 2026-03-04
6. **SLAM + map building** ✅ — `slam_toolbox` online async; T6 passed 2026-03-04
7. **Autonomous navigation** ❌ — Nav2; test T2
8. **Automated tests** ❌ — T1–T4 pytest suite; JUnit XML
9. **Operational documentation** ❌ — `docs/operations.md` for sim environment
10. **Hardware load** ❌ — Ubuntu 24.04 + Docker on Raspberry Pi 4; arm64 image

### Container Environment

- User: `ros_user` (UID 1000; `ubuntu` user removed in Dockerfile)
- Workspace: `/home/ros_user/ros2_ws`; host `src/` mounted to `ros2_ws/src`
- `TURTLEBOT3_MODEL=burger`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=0`

### Key Commands

See `.claude/rules/commands.md` for all per-phase launch and test-gate commands.

```bash
# Build both images (sg needed until fresh login after docker group usermod)
sg docker -c "bash scripts/build.sh"

# Start both containers (GPU auto-detected)
sg docker -c "docker compose up -d"

# Attach shell to simulator
bash scripts/attach_terminal.sh turtlebot3_simulator

# Build workspace inside simulator container
docker exec turtlebot3_simulator bash /home/ros_user/ros2_ws/scripts/workspace.sh

# Markdown lint (run before committing .md files)
markdownlint-cli2 "**/*.md"
markdownlint-cli2 --fix "**/*.md"
```

## File Layout

```
turtlebot3/
├── .devcontainer/
│   ├── Dockerfile.simulator  # osrf:jazzy-desktop-full + TB3/Nav2/SLAM + ros_user
│   ├── Dockerfile.turtlebot  # robotis/turtlebot3:jazzy + CycloneDDS + ros_user
│   └── devcontainer.json     # VS Code entry (simulator container)
├── .claude/
│   ├── CLAUDE.md             # this file
│   └── rules/
│       ├── commands.md       # per-phase launch + test-gate commands
│       └── gotchas.md        # all known pitfalls and workarounds
├── .colcon/defaults.yaml     # colcon build defaults (mounted into both containers)
├── .markdownlint-cli2.jsonc  # max line length 300; disabled: MD012 MD022 MD024 MD041 MD045
├── scripts/
│   ├── build.sh              # build both images
│   ├── run_docker.sh         # start both containers (GPU auto-detect)
│   ├── attach_terminal.sh    # attach shell to named container
│   ├── workspace.sh          # rosdep + colcon build (run inside container)
│   ├── test_t4.py            # T4: publish /cmd_vel, verify /odom changes
│   ├── test_t5.py            # T5: verify obstacle_avoidance_node blocks fwd motion
│   ├── test_t6.py            # T6: verify /map published by slam_toolbox
│   └── drive_circle.py       # drive robot in circle to build SLAM map (15 s)
├── docker-compose.yml        # services: simulator, turtlebot (network_mode: host)
├── entrypoint.sh             # sources ROS + workspace on container startup
├── config/params.yaml        # TurtleBot3 node params
├── input/                    # raw author inputs (vision, prompts)
├── specification.md          # full project spec: architecture, phases, test criteria
├── development-plan.md       # living dev plan: phases, decisions log, risk register
├── docs/
│   └── architecture.md       # Phase 3 deliverable: node graph, topic contracts, tf2 frames
└── src/                      # colcon workspace (host-mounted into both containers)
    ├── tb3_bringup/
    │   ├── launch/
    │   │   ├── sim_bringup.launch.py         # Gazebo Harmonic + TB3 + robot_state_publisher; headless:=true for tests
    │   │   ├── teleop.launch.py              # turtlebot3_teleop_keyboard; cmd_vel_topic arg for Ph5 remap
    │   │   ├── obstacle_avoidance.launch.py  # launches obstacle_avoidance_node
    │   │   ├── slam.launch.py                # sim_bringup + slam_toolbox online_async
    │   │   └── nav2_bringup.launch.py        # [Ph7] map_server + amcl + nav2 stack + rviz
    │   ├── config/
    │   │   ├── gazebo_params.yaml            # use_sim_time: true (wildcard for all nodes)
    │   │   ├── bridge_params.yaml            # gz_ros2_bridge: /cmd_vel as Twist (not TwistStamped)
    │   │   ├── slam_params.yaml              # slam_toolbox tuned for TB3 Burger
    │   │   ├── nav2_params.yaml              # [Ph7] Nav2 tuned for TB3 footprint + speeds
    │   │   └── maps/                         # saved maps (.pgm + .yaml) go here
    │   ├── rviz/
    │   │   ├── teleop.rviz
    │   │   └── nav2.rviz                     # [Ph7]
    │   └── worlds/tb3_sim.world              # embeds TB3 burger model directly (no spawner service needed)
    └── tb3_controller/
        ├── tb3_controller/obstacle_avoidance_node.py  # sub /scan + /cmd_vel_raw; pub /cmd_vel; blocks fwd if obstacle
        └── config/obstacle_params.yaml                # threshold_m, front_arc_deg
```

## Test Requirements (from `specification.md`)

Non-interactive; run via `docker exec`. pytest + JUnit XML output.

| ID | Test | Pass Criteria | Status |
|----|------|---------------|--------|
| T1 | Container startup | Both containers start; `which ros2` exits 0 | ✅ |
| T2 | Topic comms | `/scan` published by turtlebot, received by simulator | ❌ Ph7 |
| T3 | Gazebo launch | TB3 world loads; `/clock` active | ✅ |
| T4 | Drive command | Publish `Twist` to `/cmd_vel`; `/odom` changes | ✅ |
| T5 | Obstacle avoidance | `obstacle_avoidance_node` zeros `linear.x` when `/scan` < threshold | ✅ |
| T6 | SLAM map building | `/map` published by `slam_toolbox`; non-empty after robot moves | ✅ |


## Git Commitment Guidelines
Whenever you perform a git commit, you MUST follow the industry standard Conventional Commits specification.

1. **Format**: Use the structure: `<type>(<scope>): <description>`
   - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
   - Scope: The specific module (e.g., lidar, navigation, gazebo, sbc).
2. **Subject Line**:
   - Use the imperative mood ("Add feature" not "Added feature").
   - Max 50 characters.
   - No period at the end.
3. **Body**:
   - If the change is complex, include a blank line and a bulleted list of changes.
   - Focus on the "why" behind the change, not just the "what."
4. **Constraints**:
   - NEVER use generic messages like "update files" or "fix bug."
   - If you are unsure of the scope, omit it: `feat: add laser scan filter`.
5. **Auto-Summarization**:
   - Before committing, always run `git diff --cached` to review your changes
     and ensure the commit message accurately reflects every modified line.

## Known Gotchas

See `.claude/rules/gotchas.md` for the full list. Critical highlights:

- **Docker permission denied**: prefix commands with `sg docker -c "..."` until fresh login.
- **Always source both setups**: `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash` — workspace-only source breaks `ros2` CLI.
- **`teleop_keyboard` needs TTY**: launch via `bash scripts/attach_terminal.sh turtlebot3_simulator`, not `docker exec`.
- **Map saving**: use `ros2 service call /slam_toolbox/save_map ...` — `map_saver_cli` fails due to QoS mismatch.
- **Map save path must be outside `src/`**: saving to `/home/ros_user/ros2_ws/src/...` inside the container returns result=255. Save to `~/` then `cp` to `src/tb3_bringup/config/maps/`.
- **headless sim**: pass `headless:=true` to `sim_bringup.launch.py` in all `docker exec` test commands.
- **`slam.launch.py` docstring is wrong**: it says `map_saver_cli` — ignore it; use the slam_toolbox service as noted above.
