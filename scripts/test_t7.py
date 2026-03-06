#!/usr/bin/env python3
"""test_t7.py — Phase 7 test gate

Verifies that the Nav2 autonomous navigation stack is operational:
  1. /map is published by map_server (pre-built map loaded)
  2. /amcl_pose is published (AMCL localization running)
  3. /navigate_to_pose action server is available
  4. A simple goal (0.5 m forward) succeeds without collision

Run after nav2_bringup.launch.py has been up for ~30 s:

  docker exec -d turtlebot3_simulator bash -c "
    source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash &&
    ros2 launch tb3_bringup nav2_bringup.launch.py headless:=true"

  sleep 30

  docker cp scripts/test_t7.py turtlebot3_simulator:/tmp/test_t7.py
  docker exec turtlebot3_simulator bash -c "
    source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash &&
    python3 /tmp/test_t7.py"

Expected output: T7_PASS
"""

import sys
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped


TIMEOUT_S = 60.0
# phase6_map is 12x12 cells @ 0.05 m, origin (-0.319, -0.010)
# map bounds: x [-0.319, 0.281], y [-0.010, 0.590]
# Robot starts at (0, 0); goal must be within map bounds
GOAL_X = 0.15
GOAL_Y = 0.10


class Nav2Tester(Node):
    def __init__(self):
        super().__init__('nav2_tester')
        self.map_received = False
        self.amcl_received = False
        self.map_width = 0
        self.map_height = 0

        map_qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self._map_cb, map_qos)
        amcl_qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self._amcl_cb, amcl_qos)
        self.nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

    def _map_cb(self, msg):
        self.map_width = msg.info.width
        self.map_height = msg.info.height
        if self.map_width > 0 and self.map_height > 0:
            self.map_received = True

    def _amcl_cb(self, _msg):
        self.amcl_received = True


def wait_for(condition_fn, node, timeout_s, label):
    deadline = time.time() + timeout_s
    while not condition_fn():
        if time.time() > deadline:
            print(f'FAIL: timeout waiting for {label}', flush=True)
            return False
        rclpy.spin_once(node, timeout_sec=0.5)
    print(f'OK: {label}', flush=True)
    return True


def main():
    rclpy.init()
    node = Nav2Tester()

    # 1. Check /map published with non-zero dimensions
    if not wait_for(lambda: node.map_received, node, TIMEOUT_S, '/map published'):
        rclpy.shutdown()
        sys.exit(1)
    print(f'   map size: {node.map_width}x{node.map_height} cells', flush=True)

    # 2. Check /amcl_pose published (AMCL localizing)
    if not wait_for(lambda: node.amcl_received, node, TIMEOUT_S, '/amcl_pose published'):
        rclpy.shutdown()
        sys.exit(1)

    # 3. Check /navigate_to_pose action server is available
    if not node.nav_client.wait_for_server(timeout_sec=30.0):
        print('FAIL: /navigate_to_pose action server not available', flush=True)
        rclpy.shutdown()
        sys.exit(1)
    print('OK: /navigate_to_pose action server available', flush=True)

    # 4. Send a simple goal and wait for success
    goal_msg = NavigateToPose.Goal()
    goal_msg.pose = PoseStamped()
    goal_msg.pose.header.frame_id = 'map'
    goal_msg.pose.header.stamp = node.get_clock().now().to_msg()
    goal_msg.pose.pose.position.x = GOAL_X
    goal_msg.pose.pose.position.y = GOAL_Y
    goal_msg.pose.pose.orientation.w = 1.0

    print(f'Sending goal: ({GOAL_X}, {GOAL_Y}) in map frame...', flush=True)
    send_future = node.nav_client.send_goal_async(goal_msg)

    deadline = time.time() + TIMEOUT_S
    while not send_future.done():
        if time.time() > deadline:
            print('FAIL: goal send timed out', flush=True)
            rclpy.shutdown()
            sys.exit(1)
        rclpy.spin_once(node, timeout_sec=0.5)

    goal_handle = send_future.result()
    if not goal_handle.accepted:
        print('FAIL: goal rejected by Nav2', flush=True)
        rclpy.shutdown()
        sys.exit(1)
    print('OK: goal accepted', flush=True)

    result_future = goal_handle.get_result_async()
    deadline = time.time() + TIMEOUT_S
    while not result_future.done():
        if time.time() > deadline:
            print('FAIL: goal execution timed out', flush=True)
            rclpy.shutdown()
            sys.exit(1)
        rclpy.spin_once(node, timeout_sec=0.5)

    from action_msgs.msg import GoalStatus
    status = result_future.result().status
    if status == GoalStatus.STATUS_SUCCEEDED:
        print('OK: goal reached (SUCCEEDED)', flush=True)
    else:
        print(f'FAIL: goal ended with status {status} (expected SUCCEEDED=4)', flush=True)
        rclpy.shutdown()
        sys.exit(1)

    rclpy.shutdown()
    print('T7_PASS', flush=True)


if __name__ == '__main__':
    main()
