"""T4: Drive command — publish Twist to /cmd_vel; /odom position changes.

Requires sim_bringup.launch.py to be running (headless:=true).

Pass criteria: robot x-position changes by > 0.01 m after 4 s at 0.3 m/s.
"""

import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


def test_drive_moves_robot(rclpy_init):
    node = rclpy.create_node("t4_test_drive")
    positions = []
    node.create_subscription(
        Odometry, "/odom", lambda m: positions.append(m.pose.pose.position.x), 10
    )
    pub = node.create_publisher(Twist, "/cmd_vel", 10)

    # Collect baseline odom for 3 s
    t_end = time.time() + 3.0
    while time.time() < t_end:
        rclpy.spin_once(node, timeout_sec=0.1)

    assert positions, "/odom not received — is sim_bringup running?"
    before = positions[-1]

    # Drive forward for 4 s
    twist = Twist()
    twist.linear.x = 0.3
    t_end = time.time() + 4.0
    while time.time() < t_end:
        pub.publish(twist)
        rclpy.spin_once(node, timeout_sec=0.1)

    # Stop and settle
    twist.linear.x = 0.0
    pub.publish(twist)
    t_end = time.time() + 2.0
    while time.time() < t_end:
        rclpy.spin_once(node, timeout_sec=0.1)

    after = positions[-1]
    node.destroy_node()

    assert abs(after - before) > 0.01, (
        f"/odom did not change after driving: before={before:.3f} after={after:.3f}"
    )
