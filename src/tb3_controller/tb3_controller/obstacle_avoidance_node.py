"""Obstacle avoidance node — sits between teleop and the robot.

Subscribes to /cmd_vel_raw (teleop output) and /scan (LiDAR).
Publishes to /cmd_vel (robot input).

When any range in the forward arc is below obstacle_threshold_m,
forward motion is zeroed out (robot stops); lateral/rotation commands
are passed through unchanged so the operator can back up or turn away.
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


BEST_EFFORT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    depth=10,
)


class ObstacleAvoidanceNode(Node):

    def __init__(self):
        super().__init__('obstacle_avoidance_node')

        self.declare_parameter('obstacle_threshold_m', 0.35)
        self.declare_parameter('front_arc_deg', 30.0)
        self.declare_parameter('cmd_vel_raw_topic', '/cmd_vel_raw')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')

        self._threshold = self.get_parameter('obstacle_threshold_m').value
        self._arc_deg = self.get_parameter('front_arc_deg').value
        cmd_vel_raw = self.get_parameter('cmd_vel_raw_topic').value
        cmd_vel_out = self.get_parameter('cmd_vel_topic').value

        self._latest_scan: LaserScan | None = None
        self._obstacle_ahead = False

        self._scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self._scan_callback,
            BEST_EFFORT_QOS,
        )
        self._cmd_vel_raw_sub = self.create_subscription(
            Twist,
            cmd_vel_raw,
            self._cmd_vel_callback,
            10,
        )
        self._cmd_vel_pub = self.create_publisher(Twist, cmd_vel_out, 10)

        self.get_logger().info(
            f'obstacle_avoidance_node ready — threshold={self._threshold} m, '
            f'arc=±{self._arc_deg}°, '
            f'in={cmd_vel_raw}, out={cmd_vel_out}'
        )

    # ------------------------------------------------------------------
    def _scan_callback(self, msg: LaserScan):
        self._latest_scan = msg
        min_front = self._min_front_range(msg)
        was_blocked = self._obstacle_ahead
        self._obstacle_ahead = min_front < self._threshold
        if self._obstacle_ahead != was_blocked:
            if self._obstacle_ahead:
                self.get_logger().warning(
                    f'Obstacle detected at {min_front:.2f} m — blocking forward motion'
                )
            else:
                self.get_logger().info('Path clear — forward motion restored')

    def _cmd_vel_callback(self, msg: Twist):
        out = Twist()
        out.angular = msg.angular
        if self._obstacle_ahead and msg.linear.x > 0.0:
            out.linear.x = 0.0
            out.linear.y = 0.0
            out.linear.z = 0.0
        else:
            out.linear = msg.linear
        self._cmd_vel_pub.publish(out)

    # ------------------------------------------------------------------
    def _min_front_range(self, msg: LaserScan) -> float:
        """Return the minimum range in the forward arc, ignoring invalid readings."""
        if not msg.ranges:
            return float('inf')

        n = len(msg.ranges)
        arc_rad = math.radians(self._arc_deg)
        # Number of indices that span the arc on each side
        indices_per_rad = 1.0 / msg.angle_increment if msg.angle_increment != 0 else 0
        half_span = int(arc_rad * indices_per_rad)

        # Collect indices covering ±arc_deg around index 0 (forward)
        indices = list(range(0, half_span + 1)) + list(range(n - half_span, n))

        valid = [
            msg.ranges[i]
            for i in indices
            if msg.range_min <= msg.ranges[i] <= msg.range_max
        ]
        return min(valid) if valid else float('inf')


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
