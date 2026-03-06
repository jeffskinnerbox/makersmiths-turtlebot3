"""T3: Gazebo launch — /clock is active within 10 s.

Requires sim_bringup.launch.py to be running (headless:=true).

Pass criteria: /clock topic publishes at least one message.
"""

import time

import rclpy
from rosgraph_msgs.msg import Clock


def test_clock_publishing(rclpy_init):
    node = rclpy.create_node("t3_test_clock")
    received = [False]
    node.create_subscription(
        Clock, "/clock", lambda _: received.__setitem__(0, True), 10
    )

    deadline = time.time() + 10.0
    while not received[0] and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()
    assert received[0], "/clock not published within 10 s — is sim_bringup running?"
