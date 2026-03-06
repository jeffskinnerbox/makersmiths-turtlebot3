"""T7: Autonomous navigation — Nav2 stack active; goal accepted and SUCCEEDED.

Requires nav2_bringup.launch.py to be running (headless:=true).
Allow ~30 s for Nav2 to fully initialize before running this test.

Goal (0.15, 0.10) is within phase6_map bounds:
  map: 12x12 cells @ 0.05 m, origin (-0.319, -0.010)
  x range: [-0.319, 0.281], y range: [-0.010, 0.590]

Pass criteria:
  1. /map published with non-zero dimensions
  2. /amcl_pose published (AMCL localizing)
  3. /navigate_to_pose action server available
  4. Goal (0.15, 0.10) reaches STATUS_SUCCEEDED
"""

import time

import pytest
import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from rclpy.action import ActionClient
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

TRANSIENT_RELIABLE_QOS = QoSProfile(
    depth=1,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    reliability=QoSReliabilityPolicy.RELIABLE,
)
TIMEOUT_S = 60.0
GOAL_X = 0.15
GOAL_Y = 0.10


def _spin_until(condition_fn, node, timeout_s, label):
    deadline = time.time() + timeout_s
    while not condition_fn():
        if time.time() > deadline:
            pytest.fail(f"Timeout ({timeout_s}s) waiting for: {label}")
        rclpy.spin_once(node, timeout_sec=0.5)


def test_map_server_publishing(rclpy_init):
    node = rclpy.create_node("t7_map_check")
    ready = [False]

    def _cb(msg: OccupancyGrid):
        if msg.info.width > 0 and msg.info.height > 0:
            ready[0] = True

    node.create_subscription(OccupancyGrid, "/map", _cb, TRANSIENT_RELIABLE_QOS)
    _spin_until(lambda: ready[0], node, TIMEOUT_S, "/map with non-zero dimensions")
    node.destroy_node()


def test_amcl_localizing(rclpy_init):
    node = rclpy.create_node("t7_amcl_check")
    ready = [False]
    node.create_subscription(
        PoseWithCovarianceStamped,
        "/amcl_pose",
        lambda _: ready.__setitem__(0, True),
        TRANSIENT_RELIABLE_QOS,
    )
    _spin_until(lambda: ready[0], node, TIMEOUT_S, "/amcl_pose published")
    node.destroy_node()


def test_navigate_to_goal(rclpy_init):
    node = rclpy.create_node("t7_nav_check")
    client = ActionClient(node, NavigateToPose, "/navigate_to_pose")

    assert client.wait_for_server(timeout_sec=30.0), (
        "/navigate_to_pose action server not available within 30 s"
    )

    goal = NavigateToPose.Goal()
    goal.pose = PoseStamped()
    goal.pose.header.frame_id = "map"
    goal.pose.header.stamp = node.get_clock().now().to_msg()
    goal.pose.pose.position.x = GOAL_X
    goal.pose.pose.position.y = GOAL_Y
    goal.pose.pose.orientation.w = 1.0

    send_future = client.send_goal_async(goal)
    _spin_until(send_future.done, node, TIMEOUT_S, "goal send response")

    goal_handle = send_future.result()
    assert goal_handle.accepted, "Nav2 rejected the navigation goal"

    result_future = goal_handle.get_result_async()
    _spin_until(result_future.done, node, TIMEOUT_S, "goal result")

    status = result_future.result().status
    node.destroy_node()
    assert status == GoalStatus.STATUS_SUCCEEDED, (
        f"Goal ended with status {status} (expected STATUS_SUCCEEDED={GoalStatus.STATUS_SUCCEEDED})"
    )
