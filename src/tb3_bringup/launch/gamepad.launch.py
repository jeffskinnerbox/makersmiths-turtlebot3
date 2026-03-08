"""
gamepad.launch.py — Logitech F310 gamepad control for TurtleBot3.

Starts:
  - joy_node         (joy)              reads /dev/input/js0 → /joy
  - teleop_node      (teleop_twist_joy) maps /joy → /cmd_vel_raw
  - gamepad_manager  (tb3_controller)   gates /cmd_vel_raw → /cmd_vel; e-stop/restart

Usage:
  ros2 launch tb3_bringup gamepad.launch.py
  ros2 launch tb3_bringup gamepad.launch.py use_sim_time:=false  # hardware
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    tb3_bringup_dir = get_package_share_directory('tb3_bringup')
    joy_config = os.path.join(tb3_bringup_dir, 'config', 'teleop_twist_joy.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'device_id': 0,
            'deadzone': 0.15,
            'autorepeat_rate': 20.0,
            'use_sim_time': False,  # always wall clock — reads physical hardware
        }],
        output='screen',
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[joy_config, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', '/cmd_vel_raw')],  # gated by gamepad_manager
        output='screen',
    )

    gamepad_manager = Node(
        package='tb3_controller',
        executable='gamepad_manager',
        name='gamepad_manager',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock. Set false for hardware.',
        ),
        joy_node,
        teleop_node,
        gamepad_manager,
    ])
