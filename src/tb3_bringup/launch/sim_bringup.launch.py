"""
sim_bringup.launch.py — Phase 4

Starts a TurtleBot3 Burger simulation in Gazebo Harmonic.

Uses a custom world SDF (worlds/tb3_sim.world) that embeds the TB3 model
directly, avoiding the ros_gz_sim spawner which requires the
/world/default/create service that gz-sim 8.10 no longer provides.

Also uses a custom bridge config (config/bridge_params.yaml) that maps
/cmd_vel as geometry_msgs/Twist (not TwistStamped), compatible with
teleop_keyboard, obstacle_avoidance_node, and Nav2.

Components started:
  1. gz sim server   (-r -s) — always; publishes /clock
  2. gz sim client   (-g)    — skipped when headless:=true
  3. robot_state_publisher   — URDF → /tf_static /robot_description
  4. ros_gz_bridge           — Gazebo ↔ ROS 2 topics (our custom config)
  5. rviz2                   — optional; requires display

Usage:
  # Interactive (opens Gazebo GUI + optionally RViz):
  ros2 launch tb3_bringup sim_bringup.launch.py
  ros2 launch tb3_bringup sim_bringup.launch.py use_rviz:=true

  # Headless (for T3/T4 testing via docker exec, no display needed):
  ros2 launch tb3_bringup sim_bringup.launch.py headless:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')

    tb3_bringup_share = get_package_share_directory('tb3_bringup')
    tb3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(tb3_bringup_share, 'worlds', 'tb3_sim.world')
    bridge_params = os.path.join(tb3_bringup_share, 'config', 'bridge_params.yaml')
    rviz_config = os.path.join(tb3_bringup_share, 'rviz', 'teleop.rviz')

    # GZ_SIM_RESOURCE_PATH must include turtlebot3_gazebo/models so gz sim
    # can resolve model://turtlebot3_burger and model://turtlebot3_common.
    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(tb3_gazebo_share, 'models'),
    )

    # --- 1. gz sim server (headless; publishes /clock) -----------------------
    # --headless-rendering: use EGL offscreen rendering; correct for server-only
    # mode regardless of the headless launch arg (server never shows a GUI window)
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -s --headless-rendering -v2 ', world_file],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # --- 2. gz sim client (GUI; skipped in headless mode) --------------------
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': '-g -v2',
            'on_exit_shutdown': 'true',
        }.items(),
        condition=UnlessCondition(headless),
    )

    # --- 3. robot_state_publisher (URDF → /tf_static /robot_description) ----
    robot_state_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                tb3_gazebo_share, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    # --- 4. ros_gz_bridge (Gazebo ↔ ROS 2) ----------------------------------
    # Uses our bridge_params.yaml which maps /cmd_vel as Twist (not TwistStamped).
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=[
            '--ros-args',
            '-p', f'config_file:={bridge_params}',
        ],
        output='screen',
    )

    # --- 5. Optional RViz2 ---------------------------------------------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use Gazebo simulation clock'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Skip gz sim GUI client (use true for docker exec testing)'),
        DeclareLaunchArgument(
            'use_rviz', default_value='false',
            description='Launch RViz2 for visualization'),
        set_gz_resource_path,
        gzserver,
        gzclient,
        robot_state_pub,
        bridge_node,
        rviz_node,
    ])
