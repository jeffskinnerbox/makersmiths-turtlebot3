# Known Gotchas

- **G28 — `ros2 service call` blocks indefinitely if service is unavailable**: unlike topic echo which has a timeout flag, `ros2 service call` waits forever if the server isn't up. Always wrap with `timeout 20 ros2 service call ...` in scripts.
- **G27 — `async_slam_toolbox_node` is a lifecycle node**: spawning it directly with `Node()` leaves it in unconfigured state — no `/scan` subscription, no `/map` publication. Use slam_toolbox's provided `online_async_launch.py` (with `autostart:=true`) which emits CONFIGURE → ACTIVATE lifecycle events automatically.
- **G26 — YAML merge (`<<: *anchor`) does NOT concat lists**: adding a `volumes:` key to a service that uses `<<: *ros-common` completely replaces the anchor's volumes list. Always put shared mounts in the anchor itself, never in per-service `volumes:` overrides.
- **G25 — `ros-jazzy-joy` uses SDL2, not the kernel joystick API**: requires `/dev/input/eventX` (evdev), not just `/dev/input/jsX`. Fix: bind-mount `/dev/input:/dev/input` in compose + `device_cgroup_rules: ["c 13:* rmw"]` + `group_add: ["102"]` (input GID on this host). Axis indices from SDL2 match jstest (same kernel order), but triggers start at 1.0 (not -32767) at rest.
- **G24 — `docker compose restart` does NOT re-read compose file**: new `devices`, volumes, or env vars added to compose.yaml are NOT applied on restart. Must use `docker compose up -d --force-recreate <service>` to pick up compose changes.
- **G22 — `libgl1-mesa-glx` removed in Ubuntu 24.04**: package no longer exists; replaced by `libgl1-mesa-dri`. Remove from Dockerfile apt installs.
- **G23 — `/opt/ros/jazzy/bin` not in ENV PATH**: osrf and robotis base images add ROS bin to PATH only via `source setup.bash`, not via `ENV`. Dockerfiles must explicitly add `/opt/ros/${ROS_DISTRO}/bin` to `ENV PATH` for `which ros2` and `docker exec` to work without sourcing.
- **Docker permission denied**: `jeff` in `docker` group but session predates `usermod`. Prefix with `sg docker -c "..."` until fresh login.
- **`ubuntu` user conflict**: `osrf/ros:jazzy-desktop-full` ships `ubuntu` at UID 1000. Dockerfile must `userdel -r ubuntu` before `useradd ros_user`.
- **`docker run -it` in Claude Code**: no TTY in subprocess — start detached with `sleep infinity`, then attach from user's terminal.
- **`ros2 topic list` hangs**: DDS peer discovery blocks. Use `which ros2` or `python3 -c "import rclpy"` to verify ROS without blocking.
- **Production networking**: turtlebot container on RPi 4 uses `--network host` (required for DDS multicast across machines on same LAN); simulator stays on desktop.
- **`robotis/turtlebot3` tag**: `jazzy` tag does NOT exist. Use `jazzy-pc-latest` (dev/amd64) or `jazzy-sbc-latest` (RPi4/arm64).
- **`gz` binary path**: not in standard PATH — at `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz`. Both Dockerfiles add it via `ENV PATH`.
- **Gazebo Harmonic**: use `gz sim` (not `gazebo`); `gz_ros2_control` bridge; `ros-jazzy-turtlebot3-gazebo` must have Harmonic-compatible worlds (risk R2).
- **gz-sim 8.10 spawner removed**: `/world/default/create` service no longer exists in gz-sim 8.10. Embed the TB3 model directly in the world SDF (`src/tb3_bringup/worlds/tb3_warehouse.world` or `tb3_house.world`) instead of using `ros_gz_sim` spawner.
- **`/cmd_vel` bridge type**: upstream `turtlebot3_gazebo` bridge uses `TwistStamped`; our `bridge_params.yaml` overrides to `geometry_msgs/msg/Twist` — required for `teleop_keyboard`, `obstacle_avoidance_node`, and Nav2.
- **`turtlebot3_teleop` v2.3.6 hardcodes `TwistStamped`**: no parameter to switch it. Our `ros_gz_bridge` expects `Twist`, so all drive commands are silently dropped. Use `teleop_twist_keyboard` instead: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`. `teleop.launch.py` has been updated to use this package.
- **`teleop_keyboard` needs TTY**: `turtlebot3_teleop_keyboard` is interactive. Never launch via non-interactive `docker exec`. Use `bash scripts/attach_terminal.sh turtlebot3_simulator`, then run `ros2 launch tb3_bringup teleop.launch.py` from within that session.
- **headless sim for testing**: pass `headless:=true` to `sim_bringup.launch.py` when launching via `docker exec` (no display). The gz sim server still runs and publishes `/clock`; only the GUI client is skipped.
- **CycloneDDS hangs on hosts with many bridge/veth interfaces**: `rclpy.init()` blocks joining multicast groups. Switched to `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (Fast-DDS). Both packages are installed in the image.
- **gz-transport also uses multicast for discovery**: `GZ_IP=127.0.0.1` forces gz-transport to use loopback, fixing the bridge connection between Gazebo and `ros_gz_bridge`. Set in docker-compose.yml.
- **`scripts/` is mounted into the container**: `./scripts` → `~/ros2_ws/scripts`. Scripts run inside the container are available at `~/ros2_ws/scripts/`. If the container predates a new volume mount, use `docker cp` to push the file in instead of restarting.
- **`ros2` CLI breaks when only workspace setup is sourced**: Always source both — `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash` — before running `ros2 node list`, `ros2 topic echo`, etc. Sourcing only the workspace overlay causes `importlib.metadata.PackageNotFoundError: ros2cli`.
- **`map_saver_cli` fails with "Failed to spin map subscription"**: QoS/DDS issue prevents it from receiving the latched `/map` topic. Use the slam_toolbox service instead: `ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap '{name: {data: "/path/map"}}'`. This saves `.pgm` + `.yaml` reliably.
- **`/map` is 0x0 until robot moves**: slam_toolbox publishes an empty initial map. Map fills as the robot drives and LiDAR scans accumulate.

