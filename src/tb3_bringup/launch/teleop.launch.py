"""
teleop.launch.py — Phase 4

Drives the robot interactively using teleop_twist_keyboard (publishes Twist).

NOTE: turtlebot3_teleop v2.3.6 hardcodes TwistStamped; our ros_gz_bridge
expects Twist. Use teleop_twist_keyboard instead (publishes Twist directly).

IMPORTANT: requires an interactive TTY.
Run this from an attached terminal, NOT via `docker exec ... bash -c "..."`.

  # Attach to the simulator container first:
  bash scripts/attach_terminal.sh turtlebot3_simulator
  # Then inside the container:
  ros2 launch tb3_bringup teleop.launch.py

  # Or run directly (no launch needed):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Controls: i=forward, ,=backward, j=turn-left, l=turn-right, k=stop

Phase 4: publishes directly to /cmd_vel.
Phase 5+: remap to /cmd_vel_raw (filtered by obstacle_avoidance_node).
  ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
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
