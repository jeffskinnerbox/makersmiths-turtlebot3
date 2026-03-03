
# My Vision for the Turtlebot3 at Makersmiths
TurtleBot3 is a small, affordable, programmable, ROS-based mobile robot for use in education, research, hobby, and product prototyping.
[Makersmiths][03] has a [Turtlebot3 Burger][04] with a Raspberry Pi 4,
4GB processor that hasn't operated in a long time.
I want to do the following:

1. As my first step, I want to create a complete simulation of the TurtleBot3 on my home Ubuntu 24.04 system.
   The entire solution should be contained in two Docker containers.
   One Docker container would contain the TurtleBot3
   (headless devcontainer image called "turtlebot" using [`robotis/turtlebot3`][01] image)
   and the other would have a have all the ROS 2 simulation tools
   (full desktop devcontainer image called "simulator" using [`osrf/ros:jazzy-desktop-full`][02] image)
   The two images will be designed such that the turtlebot image will operate in the simulator.
1. Once the two Docker containers are built, they should be tested as standalone containers.
   Once the standalone tests are passed, the two containers will be tested together.
   These test cases should be automated as much as possible and executed by Claude Code.
1. Claude Code should create documentation for how to operate the TurtleBot3 within its simulated environment.
1. I will do some manual testing with the turtlebot3 and simulator.
1. I will then have Claude Code help me
    * load Ubuntu 24.04 onto the Raspberry Pi 4
    * install Docker onto the Raspberry Pi 4
    * install turtlebot3 Docker image onto the Raspberry Pi
    * install the simulator image onto my desktop Ubuntu computer
1. I will do some manual testing with the physical TurttleBot3 and simulator.



[01]:https://hub.docker.com/r/robotis/turtlebot3/tags
[02]:https://hub.docker.com/layers/osrf/ros/jazzy-desktop-full/images/
[03]:https://makersmiths.org/
[04]:https://www.turtlebot.com/turtlebot3/

