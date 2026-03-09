"""
capability_demo.launch.py — Full autonomous capability demonstration.

Starts the complete M3 stack: SLAM + Nav2 + lidar_monitor + one of:
  - wanderer  (reactive obstacle avoidance, no Nav2 goals)
  - patrol    (NavigateToPose waypoint cycling through Nav2)

Intended to run alongside sim_bringup.launch.py or hardware bringup.

Usage:
  # Default: patrol mode
  ros2 launch tb3_bringup capability_demo.launch.py

  # Wanderer mode
  ros2 launch tb3_bringup capability_demo.launch.py mode:=wanderer

  # Hardware (real robot)
  ros2 launch tb3_bringup capability_demo.launch.py use_sim_time:=false

Arguments:
  mode          wanderer | patrol   (default: patrol)
  use_sim_time  true | false        (default: true)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EqualsSubstitution, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    tb3_bringup_dir = get_package_share_directory('tb3_bringup')
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    slam_params = os.path.join(tb3_bringup_dir, 'config', 'slam_params.yaml')
    nav2_params = os.path.join(tb3_bringup_dir, 'config', 'nav2_params.yaml')

    mode = LaunchConfiguration('mode')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ── SLAM ─────────────────────────────────────────────────────────────────
    # G27: use slam_toolbox's own launch to handle lifecycle CONFIGURE→ACTIVATE
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam_params_file': slam_params,
            'autostart': 'true',
        }.items(),
    )

    # ── Nav2 ─────────────────────────────────────────────────────────────────
    # navigation_launch.py: no map_server/AMCL — slam_toolbox provides /map TF
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params,
        }.items(),
    )

    # ── LiDAR monitor (always on) ─────────────────────────────────────────────
    lidar_monitor = Node(
        package='tb3_monitor',
        executable='lidar_monitor',
        name='lidar_monitor',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # ── Wanderer (mode:=wanderer) ─────────────────────────────────────────────
    wanderer = Node(
        package='tb3_controller',
        executable='wanderer',
        name='wanderer',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=IfCondition(EqualsSubstitution(mode, 'wanderer')),
    )

    # ── Patrol (mode:=patrol) ─────────────────────────────────────────────────
    patrol = Node(
        package='tb3_controller',
        executable='patrol',
        name='patrol',
        parameters=[{
            'use_sim_time': use_sim_time,
            'waypoints': [1.0, 0.0, 2.0, 1.0, 0.0, 1.0],
            'loop': True,
        }],
        output='screen',
        condition=IfCondition(EqualsSubstitution(mode, 'patrol')),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'mode',
            default_value='patrol',
            description='Autonomous mode: wanderer or patrol',
            choices=['wanderer', 'patrol'],
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock. Set false for hardware.',
        ),
        slam,
        nav2,
        lidar_monitor,
        wanderer,
        patrol,
    ])
