
# TurtleBot3 Burger
TurtleBot3 is a small, affordable, programmable, ROS-based mobile robot for use in education, research, hobby, and product prototyping.
[Makersmiths][03] has a [Turtlebot3 Burger][04] with a Raspberry Pi 4,
4GB processor that hasn't operated in a long time.
My plan is to revive this devices and bring it back to an operational state.

I want to create a complete simulation of the TurtleBot3 on my home Ubuntu 24.04 system.
The entire solution should be contained in two Docker containers.
One Docker container would contain the TurtleBot3
(headless devcontainer image called "turtlebot3_robot" using [`robotis/turtlebot3`][01] image)
and the other would have a have all the ROS 2 simulation tools
(full desktop devcontainer image called "turtlebot3_simulator" using [`osrf/ros:jazzy-desktop-full`][02] image)
The two images will be designed such that the turtlebot3_robot image will operate in the turtelbot3_simulator,
no robot hardware required.

* [Makersmiths Turtlebot3 Wiki](http://wiki.makersmiths.org/display/MAK/Turtlebot+3)

* [Raspberry Pi Pico Simulator](https://www.howtogeek.com/test-raspberry-pi-pico-projects-without-hardware/)
* [pure Raspberry Pi OS Docker images](https://www.hackster.io/news/vasco-guita-gives-raspberry-pi-homelabbers-a-gift-scratch-raspberry-pi-os-docker-images-5ae595e73982)
* [Forest3D](https://github.com/unitsSpaceLab/Forest3D/tree/main) is a comprehensive toolkit that generates realistic forest environments for Gazebo robotics simulation
  by processing Blender assets and DEM terrain data through automated procedural placement algorithms.



[01]:https://hub.docker.com/r/robotis/turtlebot3/tags
[02]:https://hub.docker.com/layers/osrf/ros/jazzy-desktop-full/images/
[03]:https://makersmiths.org/
[04]:https://www.turtlebot.com/turtlebot3/

