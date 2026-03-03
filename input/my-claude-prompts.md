# My Claude Code Prompts

## Creation of ROS2 DevContainer Skill
### 1st Claude Code Prompt
Create for me a SKILL.md file with skill name of "ros_devcontainer".
This skill assumes you ares an expert in doing the following:
Create and configure a ROS 2 development Docker container (DevContainer)
and supporting these three types of containers configurations:
* Minimal CLI - for production robot, built without GUI, simulator, test tools, etc.
* Full Desktop - for developing & testing
* Custom Project - user choose a robot (TurtleBot3 currently only choose)

Use the document @docs/RCLPY-From-Zero-To-Hero-1-kwlngi.pdf pages 14 to 23 as you primary guide for this skill.
Use these additional sources to expand your ROS2 / Docker skill further:
* [The Complete Guide to Docker for ROS 2 Jazzy Projects — Automatic Addison](https://automaticaddison.com/the-complete-guide-to-docker-for-ros-2-jazzy-projects/)
* [The Complete Beginner's Guide to Using Docker for ROS 2 Deployment (2025) — RobotAir](https://blog.robotair.io/the-complete-beginners-guide-to-using-docker-for-ros-2-deployment-2025-edition-0f259ca8b378)
* [Introduction to ROS 2 Development with Docker](https://docs.docker.com/guides/ros2/)
With the body of the SKILL.md file, reference the above sources.

The skill should also create bash scripts and ROS2 launch scripts
that assist the user in the configuration and operation of the devcontainer.

When using this skill, and before generating any files, ask the user the following questions
and use this information to guide the creation of the ROS 2 devcontainer:

1. ROS 2 distribution that you want to use in the Docker container?
   * Kilted
   * Jazzy                       ( recommended )
   * Humble

1. Host OS where the ROS 2 Docker container will run?
   * Linux                       ( Ubuntu 24.04 preferred )
   * macOS                       ( Intel or Apple Silicon )
   * Windows                     ( with WSL2 recommended )

1. GPU type used within the host where the Docker container runs?
   * NVIDIA                      ( Use this if you have an Nvidia graphics card, needs Container Toolkit )
   * AMD                         ( Use this if you have an AMD graphics card, Linux kernel drivers, no extra install )
   * None                        ( Use this if you have no dedicated graphics card, LIBGL_ALWAYS_SOFTWARE=1 )
   * Unknown                     ( same as None )

1. Are ROS GUI tools (RViz, Gazebo, rqt) needed in the Docker container?
   * Yes                         ( full desktop ROS 2 image + X11 or VNC, operations via Terminal & GUI )
   * No                          ( headless Linux, no simulators, all operations via Terminal only )

1. GUI display method you plan to use on remote machine? (if ROS GUI tools is Yes)
   * X11 forwarding              ( for Linux remote machines, fastest )
   * VNC browser desktop         ( for Linux or Windows or macOS remote machines )

1. IDE used in your workflow?
   * VS Code DevContainer        ( VS Code loads/starts container, .devcontainer/devcontainer.json )
   * Convenience script          ( run_docker.sh + attach via Docker sidebar )
   * Terminal only               ( manual docker run )

1. Your robot / project type?
   * TurtleBot3 with GUI         ( TurtleBot3 on desktop ROS 2 image )
   * TurtleBot3 with Terminal    ( TurtleBot3 on headless ROS 2 image )
   * Custom robot                ( create empty generic ROS 2 workspace )
   * Simulation only             ( load simulators RViz, Gazebo / Ignition )
   * CI / deployment             ( no GUI, minimal image size )

1. Hardware device access needed? (real robot, sensors, serial ports)
   * Yes                         ( needs --privileged and /dev mount )
   * No                          ( simulation only )

1. You need multi-container setup? (e.g. separate simulator + controller containers)
   * Yes                         ( use docker-compose with YAML anchors )
   * No                          ( single container )

---

### 2nd Claude Code Prompt
Read @docs/my-vision.md and create a specification document @specification.md.
In a subsequent phase, I need this this specification document to help prepare a detailed development plan.
Think Hard about what must be specified in the specification document so a robust development plan can be created.

Use the AskUserQuestions tool for all things that require further clarification.


