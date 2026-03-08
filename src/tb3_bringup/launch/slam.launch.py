"""
slam.launch.py — SLAM mapping for TurtleBot3 using slam_toolbox online_async.

Starts:
  - async_slam_toolbox_node (slam_toolbox, lifecycle-managed) — subscribes /scan,
    publishes /map and map→odom TF

Delegates lifecycle management to slam_toolbox's online_async_launch.py, which
handles CONFIGURE → ACTIVATE transitions automatically (autostart=true).

Intended to run alongside sim_bringup.launch.py or a hardware bringup.
Run the wanderer alongside to actively build the map.

Usage:
  ros2 launch tb3_bringup slam.launch.py
  ros2 launch tb3_bringup slam.launch.py use_sim_time:=false  # hardware

Save map (G18 — do NOT use map_saver_cli):
  ros2 service call /slam_toolbox/save_map \\
    slam_toolbox/srv/SaveMap '{name: {data: "/tmp/my_map"}}'
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    tb3_bringup_dir = get_package_share_directory('tb3_bringup')
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')

    slam_params = os.path.join(tb3_bringup_dir, 'config', 'slam_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Use slam_toolbox's own launch which handles LifecycleNode CONFIGURE→ACTIVATE.
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam_params_file': slam_params,
            'autostart': 'true',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock. Set false for hardware.',
        ),
        slam_launch,
    ])
