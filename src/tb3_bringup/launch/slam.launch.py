"""slam.launch.py — Phase 6

Starts the full SLAM stack:
  1. sim_bringup.launch.py  — Gazebo Harmonic + TB3 + robot_state_publisher + ros_gz_bridge
  2. slam_toolbox            — online_async mapper; publishes /map and odom→map transform

Usage:
  # Headless (for testing via docker exec):
  ros2 launch tb3_bringup slam.launch.py headless:=true

  # Interactive (opens Gazebo GUI + RViz with map):
  ros2 launch tb3_bringup slam.launch.py use_rviz:=true

Drive the robot with teleop to build the map:
  ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw
  (obstacle_avoidance_node also keeps it safe — launch obstacle_avoidance.launch.py first)

Save the map when done (map_saver_cli fails with QoS mismatch — use the service):
  ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap '{name: {data: "/home/ros_user/my_map"}}'
  # then: cp ~/my_map.pgm ~/my_map.yaml ~/ros2_ws/src/tb3_bringup/config/maps/
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')

    tb3_bringup_share = get_package_share_directory('tb3_bringup')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')

    slam_params_file = os.path.join(tb3_bringup_share, 'config', 'slam_params.yaml')

    # --- 1. Simulation (Gazebo + robot_state_publisher + bridge) ---------------
    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_bringup_share, 'launch', 'sim_bringup.launch.py')
        ),
        launch_arguments={
            'headless': headless,
            'use_sim_time': use_sim_time,
            'use_rviz': use_rviz,
        }.items(),
    )

    # --- 2. slam_toolbox online_async ------------------------------------------
    slam_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_share, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'slam_params_file': slam_params_file,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use Gazebo simulation clock'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Skip Gazebo GUI (use true for docker exec testing)'),
        DeclareLaunchArgument(
            'use_rviz', default_value='false',
            description='Launch RViz2'),
        sim_bringup,
        slam_bringup,
    ])
