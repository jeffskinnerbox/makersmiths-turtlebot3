"""
lidar_monitor_node.py — LiDAR proximity monitor for TurtleBot3.

Subscribes to /scan (sensor_msgs/LaserScan), computes the minimum valid
range reading, and publishes /closest_obstacle (std_msgs/Float32) at a
configurable rate (default 5 Hz).  Infinite / NaN / sub-range_min readings
are excluded from the minimum calculation.

Parameters:
  publish_rate  (float, default 5.0) — Hz for /closest_obstacle output
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32


def min_finite_range(ranges, range_min=0.0):
    """Return min finite range > range_min, or inf if no valid reading."""
    valid = [r for r in ranges if math.isfinite(r) and r > range_min]
    return min(valid) if valid else float('inf')


class LidarMonitorNode(Node):

    def __init__(self):
        super().__init__('lidar_monitor')
        self.declare_parameter('publish_rate', 5.0)
        rate = self.get_parameter('publish_rate').value

        self._min_dist = float('inf')
        self._range_min = 0.0   # updated from first scan message

        self._pub = self.create_publisher(Float32, '/closest_obstacle', 10)
        self.create_subscription(LaserScan, '/scan', self._scan_cb, 10)
        self.create_timer(1.0 / rate, self._publish_cb)

        self.get_logger().info(
            f'LidarMonitorNode ready — /closest_obstacle @ {rate} Hz'
        )

    def _scan_cb(self, msg: LaserScan):
        self._range_min = msg.range_min
        self._min_dist = min_finite_range(msg.ranges, msg.range_min)

    def _publish_cb(self):
        out = Float32()
        # Publish 0.0 when no valid reading to signal "unknown / too close"
        out.data = float(self._min_dist) if math.isfinite(self._min_dist) else 0.0
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = LidarMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
