# My Claude Code Prompts

## Creation of ROS2 DevContainer Skill
### 1st Claude Code Prompt
Create for me a SKILL.md file with skill name of "ros_devcontainer", that is an expert in doing the following:
Create and configure a ROS 2 development Docker container (DevContainer)
and supporting these three types of containers: Minimal CLI, Full Desktop, and Custom Project containers.

Use the document @docs/RCLPY-From-Zero-To-Hero-1-kwlngi.pdf pages 14 to 23 as you primary guide for this skill.
Use these additional sources to expand your skill (reference these sources in the SKILL.md file):
* [The Complete Guide to Docker for ROS 2 Jazzy Projects — Automatic Addison](https://automaticaddison.com/the-complete-guide-to-docker-for-ros-2-jazzy-projects/)
* [The Complete Beginner's Guide to Using Docker for ROS 2 Deployment (2025) — RobotAir](https://blog.robotair.io/the-complete-beginners-guide-to-using-docker-for-ros-2-deployment-2025-edition-0f259ca8b378)
* [Introduction to ROS 2 Development with Docker](https://docs.docker.com/guides/ros2/)

The skill should also create bash scripts that assist the user & configuration of the devcontainer.

When using this skill, before generating any files, ask the user the following questions
and use this information to guide the creation of the ROS 2 devcontainer:

1. Host OS?
   * Linux (Ubuntu 24.04 preferred)
   * macOS (Intel or Apple Silicon)
   * Windows (with WSL2 recommended)
2. ROS2 distribution?
   * Kilted
   * Jazzy (recommended)
   * Humble
3. GPU type?
   * NVIDIA (needs Container Toolkit)
   * AMD (Linux kernel drivers, no extra install)
   * None / software rendering (LIBGL_ALWAYS_SOFTWARE=1)
   * Unknown
4. GUI tools needed? (RViz, Gazebo, rqt)
   * Yes — full desktop image + X11 or VNC
   * No — headless / CLI only
5. Display method preference? (if GUI = yes)
   * X11 forwarding (Linux native, fastest)
   * VNC browser desktop (Windows, macOS, remote machines)
6. IDE workflow?
   * VS Code DevContainer (.devcontainer/devcontainer.json)
   * Convenience script (run_docker.sh + attach via Docker sidebar)
   * CLI only (manual docker run)
7. Robot / project type?
   * TurtleBot3
   * Custom robot / generic ROS 2 workspace
   * Simulation only (Gazebo / Ignition)
   * CI / deployment (no GUI, minimal image)
8. Hardware device access needed? (real robot, sensors, serial ports)
   * Yes (needs --privileged and /dev mount)
   * No
9. Multi-container setup? (e.g. separate simulator + controller containers)
   * Yes (use docker-compose with YAML anchors)
   * No (single container)

---


