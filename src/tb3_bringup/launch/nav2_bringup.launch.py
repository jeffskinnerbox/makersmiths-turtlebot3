"""nav2_bringup.launch.py — Phase 7

Starts autonomous navigation using a pre-built SLAM map:
  1. sim_bringup.launch.py  — Gazebo Harmonic + TB3 + robot_state_publisher + ros_gz_bridge
  2. nav2_bringup           — map_server + amcl + controller + planner + bt_navigator

Usage:
  # Headless (for testing via docker exec):
  ros2 launch tb3_bringup nav2_bringup.launch.py headless:=true

  # Interactive (opens Gazebo GUI + RViz with Nav2 panel):
  ros2 launch tb3_bringup nav2_bringup.launch.py use_rviz:=true

  # Use a different map:
  ros2 launch tb3_bringup nav2_bringup.launch.py map:=/path/to/my_map.yaml

Send a 2D Nav Goal:
  - Via RViz: click '2D Goal Pose' button on the toolbar
  - Via CLI:
    ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
      '{"pose": {"header": {"frame_id": "map"}, "pose": {"position": {"x": 0.5, "y": 0.0, "z": 0.0}, "orientation": {"w": 1.0}}}}'

Notes:
  - AMCL requires the robot to start near its initial_pose (0,0 in map frame by default).
    If localization fails, use RViz '2D Pose Estimate' to re-initialize.
  - Do NOT launch obstacle_avoidance.launch.py alongside Nav2 — Nav2 publishes
    directly to /cmd_vel; obstacle_avoidance_node expects /cmd_vel_raw input.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')

    tb3_bringup_share = get_package_share_directory('tb3_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')

    default_map = os.path.join(
        tb3_bringup_share, 'config', 'maps', 'phase6_map.yaml')
    default_params = os.path.join(
        tb3_bringup_share, 'config', 'nav2_params.yaml')
    nav2_rviz_config = os.path.join(
        tb3_bringup_share, 'rviz', 'nav2.rviz')

    # --- 1. Simulation (Gazebo + robot_state_publisher + bridge) ---------------
    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_bringup_share, 'launch', 'sim_bringup.launch.py')
        ),
        launch_arguments={
            'headless': headless,
            'use_sim_time': use_sim_time,
            'use_rviz': 'false',  # we launch our own nav2.rviz below
        }.items(),
    )

    # --- 2. Nav2 full stack (map_server + amcl + planners + bt_navigator) ------
    # nav2_bringup/launch/bringup_launch.py manages the lifecycle of all Nav2 nodes.
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml,
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'autostart': autostart,
        }.items(),
    )

    # --- 3. Optional RViz2 with Nav2 panel ------------------------------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', nav2_rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=IfCondition(use_rviz),
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
            description='Launch RViz2 with Nav2 panel'),
        DeclareLaunchArgument(
            'map', default_value=default_map,
            description='Full path to map yaml file'),
        DeclareLaunchArgument(
            'params_file', default_value=default_params,
            description='Full path to nav2 params yaml file'),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically start Nav2 lifecycle nodes'),
        sim_bringup,
        nav2_bringup,
        rviz_node,
    ])
