"""T5: Obstacle avoidance — node blocks forward motion when obstacle detected.

Requires sim_bringup.launch.py AND obstacle_avoidance.launch.py to be running.

Pass criteria:
  1. /scan is publishing
  2. Forward velocity on /cmd_vel_raw is blocked (zeroed) when obstacle is present,
     or passed through when path is clear
  3. Reverse velocity always passes through regardless of obstacles
"""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan

OBSTACLE_THRESHOLD = 0.35
FRONT_ARC_DEG = 30.0
BEST_EFFORT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    depth=10,
)


def _min_front_range(msg: LaserScan) -> float:
    n = len(msg.ranges)
    arc_rad = math.radians(FRONT_ARC_DEG)
    half_span = int(arc_rad / msg.angle_increment) if msg.angle_increment != 0 else 0
    indices = list(range(0, half_span + 1)) + list(range(n - half_span, n))
    valid = [
        msg.ranges[i]
        for i in indices
        if msg.range_min <= msg.ranges[i] <= msg.range_max
    ]
    return min(valid) if valid else float("inf")


def _wait_scan(node, timeout=10.0):
    received = [None]
    sub = node.create_subscription(
        LaserScan, "/scan", lambda m: received.__setitem__(0, m), BEST_EFFORT_QOS
    )
    deadline = time.time() + timeout
    while received[0] is None and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_subscription(sub)
    return received[0]


def test_scan_publishing(rclpy_init):
    node = rclpy.create_node("t5_scan_check")
    scan = _wait_scan(node)
    node.destroy_node()
    assert scan is not None, "/scan not published within 10 s — is sim_bringup running?"


def test_forward_velocity_gated_by_obstacle(rclpy_init):
    node = rclpy.create_node("t5_fwd_check")
    latest_scan = [None]
    latest_cmd = [None]
    node.create_subscription(
        LaserScan, "/scan", lambda m: latest_scan.__setitem__(0, m), BEST_EFFORT_QOS
    )
    node.create_subscription(
        Twist, "/cmd_vel", lambda m: latest_cmd.__setitem__(0, m), 10
    )
    pub = node.create_publisher(Twist, "/cmd_vel_raw", 10)

    # Wait for scan
    deadline = time.time() + 10.0
    while latest_scan[0] is None and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    assert latest_scan[0] is not None, "/scan not received"

    front_m = _min_front_range(latest_scan[0])
    obstacle_present = front_m < OBSTACLE_THRESHOLD

    # Publish forward and read output
    latest_cmd[0] = None
    fwd = Twist()
    fwd.linear.x = 0.2
    deadline = time.time() + 3.0
    while latest_cmd[0] is None and time.time() < deadline:
        pub.publish(fwd)
        rclpy.spin_once(node, timeout_sec=0.05)

    node.destroy_node()
    assert latest_cmd[0] is not None, (
        "/cmd_vel not received — is obstacle_avoidance_node running?"
    )

    out_fwd = latest_cmd[0].linear.x
    if obstacle_present:
        assert out_fwd == 0.0, (
            f"obstacle present (front={front_m:.2f} m) but forward not blocked: got {out_fwd}"
        )
    else:
        assert out_fwd > 0.0, (
            f"path clear (front={front_m:.2f} m) but forward blocked: got {out_fwd}"
        )


def test_reverse_always_passes(rclpy_init):
    node = rclpy.create_node("t5_rev_check")
    latest_scan = [None]
    latest_cmd = [None]
    node.create_subscription(
        LaserScan, "/scan", lambda m: latest_scan.__setitem__(0, m), BEST_EFFORT_QOS
    )
    node.create_subscription(
        Twist, "/cmd_vel", lambda m: latest_cmd.__setitem__(0, m), 10
    )
    pub = node.create_publisher(Twist, "/cmd_vel_raw", 10)

    # Wait for scan
    deadline = time.time() + 10.0
    while latest_scan[0] is None and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    assert latest_scan[0] is not None, "/scan not received"

    # Publish reverse and collect output
    latest_cmd[0] = None
    rev = Twist()
    rev.linear.x = -0.1
    deadline = time.time() + 3.0
    while latest_cmd[0] is None and time.time() < deadline:
        pub.publish(rev)
        rclpy.spin_once(node, timeout_sec=0.05)

    node.destroy_node()
    assert latest_cmd[0] is not None, "/cmd_vel not received after reverse command"
    assert latest_cmd[0].linear.x < 0.0, (
        f"reverse command blocked: /cmd_vel.linear.x={latest_cmd[0].linear.x:.3f}"
    )
