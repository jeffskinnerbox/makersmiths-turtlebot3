"""
nav2.launch.py — Nav2 navigation stack for TurtleBot3.

Starts the full Nav2 navigation stack (without map_server/AMCL — map is
provided by slam_toolbox via slam.launch.py):
  - controller_server   (DWB local planner)
  - smoother_server
  - planner_server      (NavFn global planner)
  - behavior_server     (spin, backup, etc.)
  - bt_navigator        (NavigateToPose / NavigateThroughPoses)
  - waypoint_follower
  - velocity_smoother
  - lifecycle_manager   (manages all nav2 nodes)

Intended to run alongside sim_bringup.launch.py + slam.launch.py.
For autonomous patrol, run patrol_node (Phase 3.3) which sends
NavigateToPose goals to bt_navigator.

Usage:
  ros2 launch tb3_bringup nav2.launch.py
  ros2 launch tb3_bringup nav2.launch.py use_sim_time:=false  # hardware

Verify robot_radius (T3.2e):
  ros2 param get /local_costmap/local_costmap robot_radius
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    tb3_bringup_dir = get_package_share_directory('tb3_bringup')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    nav2_params = os.path.join(tb3_bringup_dir, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    # navigation_launch.py starts the nav2 stack without map_server/amcl.
    # slam_toolbox (slam.launch.py) provides the map→odom TF and /map topic.
    nav2_navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock. Set false for hardware.',
        ),
        nav2_navigation,
    ])
