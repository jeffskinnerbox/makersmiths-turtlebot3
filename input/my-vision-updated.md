


Move some things from my-claude-prompts.md to here.


---

## Target Architecture Planning
Claude Code Prompt:
1. My Target Architecture
* The architecture is for the TurtleBot3's to have physically onboard a Raspberry Pi 4 machine
    running a headless Ubuntu 24.04 Docker container using the [`robotis/turtlebot3`](https://hub.docker.com/r/robotis/turtlebot3/tags) Jazzy image,
    This container interface with the TurtleBot3 sensors, motors, and does physical control of the robot.
    I'll call this container "turtlebot3_robot".
* There would be 2nd machine, a NucBoxM6, physically off of the TurtleBot3, running Ubuntu 24.04,
    with a Docker container using the [`osrf/ros:jazzy-desktop-full`](https://hub.docker.com/layers/osrf/ros/jazzy-desktop-full/images/) Jazzy image.
    This container supports everything else needed for the TurtleBot3's operation (e.g. teleop, gamepad, navigational planning, etc.),
    and supports the simulation of the TurtleBot3 for development & testing (e.g. Gazebo, RViz, rq_graph, etc.).
    I'll call this container "turtlebot3_ops".
* The Raspberry Pi and the NucBoxM6 will be put on the same WiFi network provided by a
    [GL.iNet GL-AXT1800 Portable Travel Router](https://store-us.gl-inet.com/products/slate-ax-gl-axt1800-gigabit-wireless-router).
2. My Development & Testing Architecture
* The architecture is for the TurtleBot3's to use my desktop Ubuntu 24.04 machine, called "desktop",
    where all containers defined for the Target Architecture will operate in one machine.
* I expect the containers developed & tested here will be easily transition to the Target Architecture
    with little or no modification.
* I expect to move the developed & tested from desktop to the NucBoxM6, potential mid-development, with minimal changes.
* WiFi will not be used for ROS2 communications.

Given I have two physical machines, and with separate containers,
should I have two git repositories or is there an advantage of having one?

---

Claude Prompt:
_I'm building a ROS2 robot (specifically a TurtleBot3 Burger) and I would like to use a
MacBook Pro, or Chromebook, or Windows 11 or Linux for an X Windows display when developing/testing/demo'ing the robot.
Can I do this and what are my options?_

---

# My Vision for the Turtlebot3 at Makersmiths

## Use Case
TurtleBot3 is a small, affordable, programmable, ROS-based mobile robot
for use in education, research, hobby, and product prototyping.
[Makersmiths][03] has a [Turtlebot3 Burger][04] with a Raspberry Pi 4,
4GB processor that hasn't operated in a long time.
I believe the hardware is in good working order but
the TurtleBot3 needs its software completely refreshed with the latest
ROS 2 platform + TurtleBot3 software and comprehensively tested.

I want to bring the TurtleBot3 back to life so that it can be
demonstrated within Makersmiths for guest visitors.
Since most Makersmiths members are not familiar with robotic, ROS2, TurtleBot3, etc.
I want to create a launch method that makes demonstrations
quick to setup, informative demo, and easy to do.
I want to use Docker to construct this robotics demonstration to make it easy to maintain
and so that it can be build, tested via simulation, and deployed easily.

## Target Architecture
At the conclusion of all development & testing,
the target architecture is for the TurtleBot3's to have physically onboard a Raspberry Pi 4 machine
running a headless Ubuntu 24.04 in a Docker container using the [`robotis/turtlebot3`][01] Jazzy image,
This container interface with the TurtleBot3 sensors, motors, and does physical control of the robot.
I'll call this container "turtlebot3_robot".
There would be 2nd machine, a NucBoxM6, physically off of the TurtleBot3, running Ubuntu 24.04,
with a Docker container using the [`osrf/ros:jazzy-desktop-full`][02] Jazzy image.
This container supports everything else needed for the TurtleBot3's operation (e.g. teleop, gamepad, navigational planning, etc.),
and supports the simulation of the TurtleBot3 for development & testing (e.g. Gazebo, RViz, rq_graph, etc.).
I'll call this container "turtlebot3_ops".
The Raspberry Pi (along with the turtlebot3_robot container)
and the NucBoxM6 (along with the turtlebot3_ops container)
will be put on the same WiFi network provided by a [GL.iNet GL-AXT1800 Portable Travel Router][08].
A user will have an option to bring up a simulated TurtleBot3 or a physically real TurtleBot3
via a launch scripts.
When doing a simulation, the simulation will be in the turtlebot3_ops container on the NucBoxM6.
When using Gazebo or RViz with a live robot,
I expect all the computation will be on the NucBoxM6.
The X Window display mechanizing will be on the NucBoxM6, or MacBook Pro, or Chromebook, or Windows 11.

## Development/Testing Architectures
During the evolutionary development and testing of this project,
I expect to build and use the following intermediate architectures
and should come about naturally in the development plan:

1. **Desktop Test Architecture:** The architecture is for the TurtleBot3's to use my desktop Ubuntu 24.04 machine, called "desktop",
   where all containers defined for the Target Architecture will operate in the desktop machine.
   The desktop machine is a full Ubuntu desktop environment with X Windows.
   There is no robot hardware, so the physical robot is simulated via ROS2 tools.
   All ROS2 interprocess communication is internal to desktop, no WiFi used by ROS2.
   I expect the containers developed & tested here will be easily transition to the NucBoxM6 Test Architecture
   with little or no modification.
   **Purpose:** The environment used here is rich with support tools, powerful machines, and will help me move quickly.
   I would like to do as much work in this environment as possible.
1. **NucBoxM6 Test Architecture:** I expect to move the developed & tested from desktop machine to the NucBoxM6.
   All containers defined for the Target Architecture will operate in the NucBoxM6 machine
   The NucBoxM6 machine is a headless Ubuntu and the desktop X Windows will be used for the NucBoxM6 display.
   There is no robot hardware, so the physical robot is simulated via ROS2 tools.
   All ROS2 interprocess communication is internal to desktop, no WiFi used by ROS2.
   I will no long use the desktop machine for X Window display, but instead I will be using a MacBook Pro,
   or Chromebook or Windows 11 or any Linux desktop for display.
   **Purpose:** This environment will make the simulation portable (just need the NucBoxM6 + laptop)
   and will allow me to test out a display mechanism that will be suitable for demonstrations at the makerspace.
1. **RPi Test Architecture:** I expect to move the turtlebot3_robot container to a Raspberry Pi 4 with a Ubuntu 24.04 OS.
   This Raspberry Pi 4 is standalone, not on the physical TurtleBot3 robot.
   The turtlebot3_robot container will be installed in the Ubuntu OS on the Raspberry Pi 4.
   The turtlebot3_ops container remains on the NucBoxM6.
   Some ROS2 interprocess communication will be over WiFi network provided by a [GL.iNet GL-AXT1800 Portable Travel Router][08].
   **Purpose:**  This environment will allow me to test the impact of WiFi usage for communications
   and test the configuration of the turtlebot3_robot container on the Raspberry Pi 4.
1. **Target Architecture:** This is as stated in the "Target Architecture"" section above.

## Development Phased Plan
I want to build the TurtleBot3 via a phased plan, and at the end of each build phase,
four to eight tests, I'll call these "test-gates",
will be performed to validate what has been created within that phase.
Do not move onto the next phase until all test-gates pass.

Within this phased plan, there will be a sets of sequenced phases, when completed successfully,
are called a milestone.
When a milestone is reached, all the test-gates for the phases that make up the milestone should be executed again.
This is called a milestone-tests.

I envision the following major milestone within this phased plan:

1. **1st Milestone:** This milestone uses the Desktop Testing Architecture.
   I want to create a complete simulation of the TurtleBot3 on my desktop Ubuntu 24.04 system.
   The entire solution should be contained in two Docker containers.
   One Docker container would contain the TurtleBot3
   (headless devcontainer image called "turtlebot" using [`robotis/turtlebot3`][01] image)
   and the other would have a have all the ROS 2 simulation tools
   (full desktop devcontainer image called "simulator" using [`osrf/ros:jazzy-desktop-full`][02] image)
   The two images will be designed such that the turtlebot image will operate in the simulator.
   The simulator will be [Gazebo Harmonic][06] and it would use the
   [TurtleBot3 House World][05], [TurtleBot3 World][13], and [TurtleBot3 AutoRace 2020][14].
   The execution of these test must be observable by the human operator via Gazebo
   in a X Window on the Ubuntu computer hosting the simulator container.
   When complete, perform the milestone-test and
   create a user guide document (called `user-guide-milestone-1.md`)
   written so all tests can be manually repeated.
1. **2nd Milestone:** This milestone uses the Desktop Testing Architecture.
   Within the simulator container,
   add ROS2 packages to manually control the TurtleBot3 via a [Logitech F310 Gamepad][07]
   using the [`joy`][11] and [`teleop_twist_joy`][12] ROS2 packages.
   The gamepad's left joystick should control the direction the robot with travel
   and the right joystick will control the speed forward or reverse.
   One of the gamepad buttons should code as an emergency stop (red button)
   and a second button as a restart (green button), and a yellow button as a reboot of the whole demo system.
   A user should also be able to perform some manual testing using the gamepad.
   The execution of these test must be observable by the human operator via Gazebo.
   When complete, perform the milestone-test and
   create a user guide document (called `user-guide-milestone-2.md`) written so all tests can be manually repeated.
1. **3rd Milestone:** This milestone uses the Desktop Testing Architecture.
   Acting as a autonomous robotics test engineer,
   rather than just a code generator, analyze the available topics for the TurtleBot3 (LIDAR, IMU, Odom, etc.)
   and develop a capabilities test package that includes at least (more is better):
    * **A Wanderer node:** Uses LIDAR to avoid factory walls.
    * **A Health Monitor:** Subscribes to /battery_state and /imu to log status.
    * **A Patrol Task:** Uses Nav2 to visit three specific coordinates in the factory floor.
  To ensure you are truly "exercising all features," follow these patterns:
    * **LIDAR:** Write a node that finds the 'closest obstacle' and publishes its distance to a custom topic.
    * **Navigation:** Configure a Nav2 param file optimized for the small footprint of the Burger.
    * **TF2 (Transforms):** Create a script that verifies the transform between base_link and map is stable.
    * **Actions:** Use a ROS 2 Action to perform a 360-degree 'Scanning' rotation and return a success result.
   The execution of these test must be observable by the human operator via Gazebo.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-3.md`) written so all tests can be manually repeated.
1. **4th Milestone:** This milestone uses the Desktop Testing Architecture.
   I want to monitor the TurtleBot3 ROS2 nodes status in an easy to use terminal screen.
   I would like to use TMUX to display all the nodes within a container in a single terminal window for each of the containers.
   I want to login to the TurtleBot3 container instance
   and have the TMUX screen pre-configure, or better yet self-configure, to display the status of all the nodes.
   To achieve this, I expect to use a [Tmuxinator][09] script
   or a custom bash script that leverages [Tmux][10] ability to split panes via the command line.
   The execution of test-gates must be observable by the human operator via via the monitoring terminal screen.
   No need to execute previous test-gates.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-4.md`) written so all tests can be manually repeated.
1. **5th Milestone:** This milestone uses the NucBoxM6 Testing Architecture.
   The turtlebot3_ops container should be installed on another Ubuntu 24.04 system, called NucBoxM6,
   along with the F310 Gamepad.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-5.md`) written so all tests can be manually repeated.
1. **6th Milestone:** This milestone uses the RPi Testing Architecture.
   The turtlebot3_robot container should be moved to the Raspberry Pi 4 on the TurtleBot3.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-6.md`) written so all tests can be manually repeated.
1. **7th Milestone:** This milestone uses the Target Architecture.
   The turtlebot3_robot container should be moved to the Raspberry Pi 4 on the TurtleBot3.
   The Raspberry Pi needs to have Ubuntu 24.04 installed, followed by Docker, and the turtlebot3_ops container.
   The simulator container should be installed on another Ubuntu 24.04 system, called NucBoxM6,
   along with the F310 Gamepad.
   The Raspberry Pi and the NucBoxM6 should be put on the same WiFi network provided by a
[GL.iNet GL-AXT1800 Portable Travel Router][08] with SSID "JeffTravelRouter-2.4".
   Also create test-gates for this work.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-7.md`) written so all tests can be manually repeated.
   The execution of these test must be observable by the human operator via Gazebo.



[01]:https://hub.docker.com/r/robotis/turtlebot3/tags
[02]:https://hub.docker.com/layers/osrf/ros/jazzy-desktop-full/images/
[03]:https://makersmiths.org/
[04]:https://www.turtlebot.com/turtlebot3/
[05]:https://github.com/ROBOTIS-GIT/turtlebot3_simulations/blob/main/turtlebot3_gazebo/worlds/turtlebot3_house.world
[06]:https://gazebosim.org/docs/harmonic/ros_installation/
[07]:https://www.logitechg.com/en-us/shop/p/f310-gamepad
[08]:https://store-us.gl-inet.com/products/slate-ax-gl-axt1800-gigabit-wireless-router
[09]:https://medium.com/@johanjohansson_63760/how-to-use-tmux-and-tmuxinator-efficiently-f58ccdd46406
[10]:https://blog.petrzemek.net/2016/02/11/my-tmux-configuration/
[11]:https://docs.ros.org/en/jazzy/p/joy/
[12]:https://docs.ros.org/en/jazzy/p/teleop_twist_joy/
[13]:https://github.com/ROBOTIS-GIT/turtlebot3_simulations/blob/main/turtlebot3_gazebo/worlds/turtlebot3_world.world
[14]:https://github.com/ROBOTIS-GIT/turtlebot3_simulations/blob/main/turtlebot3_gazebo/worlds/turtlebot3_autorace_2020.world

