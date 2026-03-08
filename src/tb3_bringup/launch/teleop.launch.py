"""
teleop.launch.py — Keyboard teleoperation for TurtleBot3.

G11: teleop_twist_keyboard (NOT turtlebot3_teleop which hardcodes TwistStamped).
G12: teleop_twist_keyboard requires a TTY — MUST be run from an attached terminal:
       bash scripts/attach_terminal.sh turtlebot3_simulator
       ros2 launch tb3_bringup teleop.launch.py

Keys: i=forward, ,=backward, j=turn-left, l=turn-right, k=stop
Hold key to keep moving (key-repeat sends continuous commands).
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_twist_keyboard',
            output='screen',
            remappings=[('/cmd_vel', '/cmd_vel')],
        ),
    ])
