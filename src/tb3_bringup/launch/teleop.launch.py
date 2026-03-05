"""
teleop.launch.py — Phase 4

Starts turtlebot3_teleop_keyboard for driving the robot with WASD/arrow keys.

IMPORTANT: turtlebot3_teleop_keyboard requires an interactive TTY.
Run this from an attached terminal, NOT via `docker exec ... bash -c "..."`.

  # Attach to the simulator container first:
  bash scripts/attach_terminal.sh turtlebot3_simulator
  # Then inside the container:
  ros2 launch tb3_bringup teleop.launch.py

Phase 4: publishes directly to /cmd_vel.
Phase 5+: will remap to /cmd_vel_raw (filtered by obstacle_avoidance_node).
  ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    teleop_node = Node(
        package='turtlebot3_teleop',
        executable='teleop_keyboard',
        name='teleop_keyboard',
        output='screen',
        remappings=[('/cmd_vel', cmd_vel_topic)],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/cmd_vel',
            description='Target cmd_vel topic. Use /cmd_vel_raw in Phase 5+ '
                        'when obstacle_avoidance_node is active.',
        ),
        teleop_node,
    ])
