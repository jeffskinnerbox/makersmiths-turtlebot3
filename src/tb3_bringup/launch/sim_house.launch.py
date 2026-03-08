"""
sim_house.launch.py — Gazebo simulation bringup using the TurtleBot3 House world.

Indoor house environment with rooms and corridors.  Good for SLAM mapping demos
and Nav2 point-to-point navigation since the layout has distinct rooms.

Starts:
  - Gazebo server (always)
  - Gazebo GUI client (only when headless:=false)
  - ros_gz_bridge (topics: /clock, /scan, /odom, /cmd_vel, /imu, /tf, /joint_states)
  - robot_state_publisher (URDF → /tf static transforms)

Usage:
  ros2 launch tb3_bringup sim_house.launch.py             # with GUI
  ros2 launch tb3_bringup sim_house.launch.py headless:=true  # headless (CI/tests)

See also: sim_bringup.launch.py (uses tb3_warehouse / turtlebot3_world environment)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    tb3_bringup_dir = get_package_share_directory('tb3_bringup')
    tb3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')

    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')

    world_file = os.path.join(tb3_bringup_dir, 'worlds', 'tb3_house.world')
    bridge_params = os.path.join(tb3_bringup_dir, 'config', 'bridge_params.yaml')
    urdf_file = os.path.join(tb3_gazebo_dir, 'urdf', 'turtlebot3_burger.urdf')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(tb3_gazebo_dir, 'models'),
    )

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', world_file],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    gz_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': '-g -v2',
            'on_exit_shutdown': 'true',
        }.items(),
        condition=UnlessCondition(headless),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_params,
            'use_sim_time': use_sim_time,
        }],
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Set true to run Gazebo server only (no GUI). Required for CI/tests.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock from /clock topic.',
        ),
        set_gz_resource_path,
        gz_server,
        gz_client,
        bridge,
        robot_state_publisher,
    ])
