
# My Vision for the Turtlebot3 at Makersmiths
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

I want to build the TurtleBot3 via a phased plan, and at the end of each build phase,
two to eight tests (I'll call these "test-gates") will be performed to validate what has been created.
Do not move onto the next phase until all test-gates pass.

I envision the following major milestone within this phased plan:

1. **1st Milestone:** I want to create a complete simulation of the TurtleBot3 on my home Ubuntu 24.04 system.
   The entire solution should be contained in two Docker containers.
   One Docker container would contain the TurtleBot3
   (headless devcontainer image called "turtlebot" using [`robotis/turtlebot3`][01] image)
   and the other would have a have all the ROS 2 simulation tools
   (full desktop devcontainer image called "simulator" using [`osrf/ros:jazzy-desktop-full`][02] image)
   The two images will be designed such that the turtlebot image will operate in the simulator.
   The simulator will be [Gazebo Harmonic][06] and it would use the [AWS RoboMaker Small Warehouse World][05].
   The execution of these test must be observable by the human operator via Gazebo
   in a X Window on the Ubuntu computer hosting the simulator container.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-1.md`) written so all tests can be manually repeated.
1. **2nd Milestone:** Within the simulator container,
   add ROS2 packages to manually control the TurtleBot3 via a [Logitech F310 Gamepad][07]
   using the [`joy`][11] and [`teleop_twist_joy`][12] ROS2 packages.
   The gamepad's left joystick should control the direction the robot with travel
   and the right joystick will control the speed forward or reverse.
   One of the gamepad buttons should code as an emergency stop (red button)
   and a second button as a restart (green button), and a yellow button as a reboot of the whole demo system.
   A user should also be able to perform some manual testing using the gamepad.
   The execution of these test must be observable by the human operator via Gazebo.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-2.md`) written so all tests can be manually repeated.
1. **3rd Milestone:** Acting as a autonomous robotics test engineer,
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
1. **4th Milestone:** I want to monitor the TurtleBot3 ROS2 nodes for there status.
   I would like to use TMUX to display all the nodes in a single terminal window.
   I want to login to the TurtleBot3 container instance
   and have the TMUX screen self configure to display the status of all the nodes.
   To achieve this, I expect to use a [Tmuxinator][09] script
   or a custom bash script that leverages [Tmux][10] ability to split panes via the command line.
   The execution of test-gates must be observable by the human operator via via the monitoring terminal screen.
   No need to execute previous test-gates.
   When completed, create a user guide document (called `user-guide-milestone-4.md`)
   written so all tests can be manually repeated.
1. **5th Milestone:** The turtlebot container should to be moved to the Raspberry Pi 4 on the TurtleBot3.
   The Raspberry Pi needs to have Ubuntu 24.04 installed, followed by Docker, and the turtlebot container.
   The simulator container should be installed on another Ubuntu 24.04 system, called NucBoxM6,
   along with the F310 Gamepad.
   The Raspberry Pi and the NucBoxM6 should be put on the same WiFi network provided by a
[GL.iNet GL-AXT1800 Portable Travel Router][08] with SSID "JeffTravelRouter-2.4".
   Also create test-gates for this work.
   When complete, perform all previous test-gates again,
   create a user guide document (called `user-guide-milestone-4.md`) written so all tests can be manually repeated.
   The execution of these test must be observable by the human operator via Gazebo.


[01]:https://hub.docker.com/r/robotis/turtlebot3/tags
[02]:https://hub.docker.com/layers/osrf/ros/jazzy-desktop-full/images/
[03]:https://makersmiths.org/
[04]:https://www.turtlebot.com/turtlebot3/
[05]:https://docs.ros.org/en/jazzy/p/aws_robomaker_small_warehouse_world/
[06]:https://gazebosim.org/docs/harmonic/ros_installation/
[07]:https://www.logitechg.com/en-us/shop/p/f310-gamepad
[08]:https://store-us.gl-inet.com/products/slate-ax-gl-axt1800-gigabit-wireless-router
[09]:https://medium.com/@johanjohansson_63760/how-to-use-tmux-and-tmuxinator-efficiently-f58ccdd46406
[10]:https://blog.petrzemek.net/2016/02/11/my-tmux-configuration/
[11]:https://docs.ros.org/en/jazzy/p/joy/
[12]:https://docs.ros.org/en/jazzy/p/teleop_twist_joy/

