"""Launch obstacle_avoidance_node with its parameter file.

Typical use (Phase 5):
  1. Start sim:   ros2 launch tb3_bringup sim_bringup.launch.py headless:=true
  2. Start avoidance node (this file)
  3. Start teleop remapped: ros2 launch tb3_bringup teleop.launch.py cmd_vel_topic:=/cmd_vel_raw
"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory('tb3_controller'),
        'config',
        'obstacle_params.yaml',
    )

    obstacle_node = Node(
        package='tb3_controller',
        executable='obstacle_avoidance_node',
        name='obstacle_avoidance_node',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}],
    )

    return LaunchDescription([obstacle_node])
