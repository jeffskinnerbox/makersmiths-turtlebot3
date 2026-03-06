# Key Commands

```bash
# Build both images (sg needed until fresh login after docker group usermod)
sg docker -c "bash scripts/build.sh"

# Start both containers (GPU auto-detected)
sg docker -c "bash scripts/run_docker.sh"
# OR: sg docker -c "docker compose up -d"

# Attach shell to simulator
bash scripts/attach_terminal.sh turtlebot3_simulator
# OR: docker exec -it turtlebot3_simulator bash

# T1 test gate
docker exec turtlebot3_turtlebot which ros2   # exits 0
docker exec turtlebot3_simulator which ros2   # exits 0
docker exec turtlebot3_simulator which gz     # exits 0 (Gazebo Harmonic)

# Inside simulator container: build workspace
docker exec turtlebot3_simulator bash /home/ros_user/ros2_ws/scripts/workspace.sh

# Launch sim headless (no display; required for docker exec testing)
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup sim_bringup.launch.py headless:=true &"

# Launch sim with GUI (interactive; from attached terminal)
# ros2 launch tb3_bringup sim_bringup.launch.py use_rviz:=true

# T3 test gate: Gazebo world loads; /clock active
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  ros2 launch tb3_bringup sim_bringup.launch.py headless:=true &
  sleep 15 && ros2 topic list | grep /clock"

# T4 test gate: publish /cmd_vel; verify /odom changes
docker exec turtlebot3_simulator bash -c "
  source ~/ros2_ws/install/setup.bash &&
  python3 ~/ros2_ws/scripts/test_t4.py"

# Keyboard teleop (MUST be from attached terminal — needs TTY)
bash scripts/attach_terminal.sh turtlebot3_simulator
# then inside: ros2 launch tb3_bringup teleop.launch.py

# T5: obstacle avoidance (run after sim_bringup)
docker exec -d turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && ros2 launch tb3_bringup obstacle_avoidance.launch.py"
docker cp scripts/test_t5.py turtlebot3_simulator:/tmp/test_t5.py
docker exec turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && python3 /tmp/test_t5.py"
# Teleop remapped so obstacle_avoidance_node intercepts /cmd_vel_raw → /cmd_vel:
# ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw

# T6: SLAM stack
docker exec -d turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && ros2 launch tb3_bringup slam.launch.py headless:=true"
docker cp scripts/test_t6.py turtlebot3_simulator:/tmp/test_t6.py
docker exec turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && python3 /tmp/test_t6.py"
# Save map via slam_toolbox service (NOT map_saver_cli — see gotchas.md):
# ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap '{name: {data: "/path/to/my_map"}}'

# Phase 7: Nav2
docker exec -d turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && ros2 launch tb3_bringup nav2_bringup.launch.py headless:=true"
docker cp scripts/test_t7.py turtlebot3_simulator:/tmp/test_t7.py
docker exec turtlebot3_simulator bash -c "source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && python3 /tmp/test_t7.py"
# Output: T7_PASS

# Phase 8: Automated test suite (host-side orchestrator)
# Results written to ./test-results/results_<stage>.xml
bash scripts/run_tests.sh sim       # T1 + T2(xfail) + T3 + T4
bash scripts/run_tests.sh obstacle  # T5
bash scripts/run_tests.sh slam      # T6
bash scripts/run_tests.sh nav2      # T7
bash scripts/run_tests.sh all       # all stages (docker restart between each)

# Markdown lint (run before committing .md files)
markdownlint-cli2 "**/*.md"
markdownlint-cli2 --fix "**/*.md"
```
