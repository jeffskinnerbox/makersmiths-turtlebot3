# My Vision for the Turtlebot3 at Makersmiths
Makersmiths has a [Turtlebot3 Burger][] with a Raspberry Pi 4, 4GB processor that hasn't operated in a long time.
I want to bring it back to life.
TurtleBot3 is a small, affordable, programmable, ROS-based mobile robot for use in education, research, hobby, and product prototyping.

There are three phases to this ROS2 Jazzy DevContainer project
1. **ROS2 Base Headless** - This devcontainer will use the [ros:jazzy-ros-base][01] Docker image
   and applying the procedures outline in the book "RCLPY From Zero To Hero" on pages 14 to 23.
   It provides a headless (no desktop environment) deployment environment.
This development environment will be on a Docker container
Create a development environment where I can port from an Internet source (or create on my own)
  the code required by the TurtleBot3.
  This environment must have the required simulators and test tools to validate the TurtleBot3 software is ready for loading on the hardware.
  There will be two containers: a Base container containing only ROS2 Jazzy,

1. **TurtleBot3 DevContainer** -


| **Minimal CLI** | `ros:jazzy-ros-base` | Headless deployment, CI, embedded targets |
| **Full Desktop** | `osrf/ros:jazzy-desktop-full` | Local dev with RViz, Gazebo, GUI tools |


[01]:https://hub.docker.com/layers/library/ros/jazzy-ros-base/images/
