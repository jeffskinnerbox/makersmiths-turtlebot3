"""T5 test: obstacle_avoidance_node blocks forward motion when obstacle detected.

Run inside the simulator container after:
  - sim_bringup.launch.py is running (headless:=true)
  - obstacle_avoidance.launch.py is running

Pass criteria:
  1. /scan is publishing
  2. When we publish forward velocity to /cmd_vel_raw:
     a. If an obstacle is within threshold in the forward arc → /cmd_vel.linear.x == 0
     b. If path is clear → /cmd_vel.linear.x > 0
  3. Reverse velocity always passes through regardless of obstacles

Usage:
  python3 ~/ros2_ws/scripts/test_t5.py
"""

import math
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


OBSTACLE_THRESHOLD = 0.35
FRONT_ARC_DEG = 30.0
BEST_EFFORT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    depth=10,
)


def min_front_range(msg: LaserScan) -> float:
    n = len(msg.ranges)
    arc_rad = math.radians(FRONT_ARC_DEG)
    half_span = int(arc_rad / msg.angle_increment) if msg.angle_increment != 0 else 0
    indices = list(range(0, half_span + 1)) + list(range(n - half_span, n))
    valid = [
        msg.ranges[i]
        for i in indices
        if msg.range_min <= msg.ranges[i] <= msg.range_max
    ]
    return min(valid) if valid else float('inf')


class T5Tester(Node):
    def __init__(self):
        super().__init__('t5_tester')
        self._latest_scan = None
        self._latest_cmd_vel = None

        self._scan_sub = self.create_subscription(
            LaserScan, '/scan', lambda m: setattr(self, '_latest_scan', m), BEST_EFFORT_QOS
        )
        self._cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', lambda m: setattr(self, '_latest_cmd_vel', m), 10
        )
        self._cmd_vel_raw_pub = self.create_publisher(Twist, '/cmd_vel_raw', 10)

    def wait_for_scan(self, timeout=10.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self._latest_scan is not None:
                return True
        return False

    def publish_and_read_cmd_vel(self, linear_x: float, timeout=3.0) -> float | None:
        self._latest_cmd_vel = None
        msg = Twist()
        msg.linear.x = linear_x
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._cmd_vel_raw_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.05)
            if self._latest_cmd_vel is not None:
                return self._latest_cmd_vel.linear.x
        return None


def main():
    rclpy.init()
    node = T5Tester()
    failures = []

    # --- Check 1: /scan publishing ---
    if not node.wait_for_scan(timeout=10.0):
        print('T5_FAIL: /scan not publishing after 10 s')
        sys.exit(1)
    print(f'PASS: /scan publishing (seq frame={node._latest_scan.header.frame_id})')

    front_m = min_front_range(node._latest_scan)
    obstacle_present = front_m < OBSTACLE_THRESHOLD
    print(f'INFO: min front range = {front_m:.2f} m  (threshold={OBSTACLE_THRESHOLD} m) → '
          f'{"OBSTACLE" if obstacle_present else "CLEAR"}')

    # --- Check 2: forward velocity blocked / passed based on scan ---
    out_fwd = node.publish_and_read_cmd_vel(0.2)
    if out_fwd is None:
        failures.append('/cmd_vel not received after publishing to /cmd_vel_raw')
    else:
        if obstacle_present:
            if out_fwd == 0.0:
                print(f'PASS: obstacle present → /cmd_vel.linear.x blocked (got {out_fwd})')
            else:
                failures.append(
                    f'obstacle present but /cmd_vel.linear.x={out_fwd:.3f} (expected 0.0)'
                )
        else:
            if out_fwd > 0.0:
                print(f'PASS: path clear → /cmd_vel.linear.x passed through (got {out_fwd:.3f})')
            else:
                failures.append(
                    f'path clear but /cmd_vel.linear.x={out_fwd:.3f} (expected >0)'
                )

    # --- Check 3: reverse always passes through ---
    out_rev = node.publish_and_read_cmd_vel(-0.1)
    if out_rev is None:
        failures.append('/cmd_vel not received for reverse command')
    elif out_rev < 0.0:
        print(f'PASS: reverse always passes through (got {out_rev:.3f})')
    else:
        failures.append(f'reverse cmd blocked: /cmd_vel.linear.x={out_rev:.3f} (expected <0)')

    node.destroy_node()
    rclpy.shutdown()

    if failures:
        for f in failures:
            print(f'T5_FAIL: {f}')
        sys.exit(1)
    else:
        print('T5_PASS')


if __name__ == '__main__':
    main()
