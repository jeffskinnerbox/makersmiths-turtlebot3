"""
tf2_verifier.py — Verify the map→base_link TF is available and fresh.

Exits 0 if the transform can be looked up and its timestamp is within
max_age seconds of the current clock.  Exits 1 on any failure.

Intended use: test-gate or health-check script.

Usage:
    # Inside container (source both setups first):
    python3 ~/ros2_ws/src/tb3_monitor/tb3_monitor/tf2_verifier.py

    # Or as an installed entry point:
    ros2 run tb3_monitor tf2_verifier

    # With custom parameters:
    ros2 run tb3_monitor tf2_verifier --ros-args -p max_age:=2.0 -p timeout:=8.0

Parameters:
    max_age  (float, default 1.0)  — max seconds between transform stamp and now
    timeout  (float, default 5.0)  — seconds to wait for TF buffer to fill
"""
import sys
import time as _wall_time

import rclpy
from rclpy.node import Node
import tf2_ros


class Tf2Verifier(Node):

    def __init__(self):
        super().__init__('tf2_verifier')
        self.declare_parameter('max_age', 1.0)
        self.declare_parameter('timeout', 5.0)

        self._max_age = self.get_parameter('max_age').value
        self._timeout = self.get_parameter('timeout').value

        self._buffer = tf2_ros.Buffer()
        self._listener = tf2_ros.TransformListener(self._buffer, self)

    def verify(self) -> bool:
        """
        Wait for the TF buffer, look up map→base_link, check freshness.

        Returns True (exit 0) if the transform is available and fresh.
        """
        self.get_logger().info(
            f'Waiting up to {self._timeout:.1f}s for map→base_link TF…')

        # Block until the transform is available or we time out.
        # Use wall clock for the deadline — sim time starts at 0 and may jump
        # past a sim-time deadline before the first /clock message is received.
        deadline = _wall_time.monotonic() + self._timeout
        while _wall_time.monotonic() < deadline:
            if self._buffer.can_transform(
                    'map', 'base_link', rclpy.time.Time()):
                break
            rclpy.spin_once(self, timeout_sec=0.1)
        else:
            self.get_logger().error(
                'map→base_link TF not available after '
                f'{self._timeout:.1f}s — FAIL')
            return False

        # Get the latest transform and check its age
        try:
            t = self._buffer.lookup_transform(
                'map', 'base_link', rclpy.time.Time())
        except tf2_ros.TransformException as exc:
            self.get_logger().error(f'lookup failed: {exc} — FAIL')
            return False

        stamp_ns = (
            t.header.stamp.sec * 1_000_000_000 + t.header.stamp.nanosec)
        now_ns = self.get_clock().now().nanoseconds
        age_sec = abs(now_ns - stamp_ns) / 1e9  # abs handles minor drift

        if age_sec > self._max_age:
            self.get_logger().error(
                f'map→base_link is {age_sec:.2f}s old '
                f'(max_age={self._max_age}s) — FAIL  '
                f'(hint: pass use_sim_time:=true in simulation)')
            return False

        self.get_logger().info(
            f'map→base_link OK — age={age_sec:.3f}s '
            f'(max_age={self._max_age}s) — PASS')
        return True


def main(args=None):
    rclpy.init(args=args)
    node = Tf2Verifier()
    ok = node.verify()
    node.destroy_node()
    rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
