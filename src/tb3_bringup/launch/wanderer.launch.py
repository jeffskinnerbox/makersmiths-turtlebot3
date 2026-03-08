"""
wanderer.launch.py — Autonomous wanderer + LiDAR monitor for TurtleBot3.

Starts:
  - lidar_monitor  (tb3_monitor)    subscribes /scan → publishes /closest_obstacle
  - wanderer       (tb3_controller) subscribes /scan + /estop → publishes /cmd_vel

Intended to run alongside sim_bringup.launch.py or a hardware bringup.

Usage:
  ros2 launch tb3_bringup wanderer.launch.py
  ros2 launch tb3_bringup wanderer.launch.py use_sim_time:=false  # hardware
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    lidar_monitor = Node(
        package='tb3_monitor',
        executable='lidar_monitor',
        name='lidar_monitor',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    wanderer = Node(
        package='tb3_controller',
        executable='wanderer',
        name='wanderer',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock. Set false for hardware.',
        ),
        lidar_monitor,
        wanderer,
    ])
