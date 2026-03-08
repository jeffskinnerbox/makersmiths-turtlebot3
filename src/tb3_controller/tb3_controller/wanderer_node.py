"""
wanderer_node.py — Obstacle-avoiding wanderer for TurtleBot3.

Drives forward when the path is clear; turns when an obstacle is within
obstacle_threshold; stops completely when within safety_threshold or when
the e-stop is active.  Turn direction alternates each time a new turn
phase begins to avoid getting stuck in corners.

Subscribes:
  /scan          sensor_msgs/LaserScan  — LiDAR readings
  /estop         std_msgs/Bool          — RELIABLE + TRANSIENT_LOCAL
                                          (set by gamepad_manager or any
                                          safety node; absent → not estopped)

Publishes:
  /cmd_vel       geometry_msgs/Twist    — motion commands at 10 Hz

Parameters:
  obstacle_threshold  (float, default 0.5)   — turn when min range < this (m)
  safety_threshold    (float, default 0.15)  — stop when min range < this (m)
  linear_speed        (float, default 0.22)  — m/s forward speed
  angular_speed       (float, default 0.5)   — rad/s turn speed
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

_ESTOP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)

CONTROL_HZ = 10.0


def min_finite_range(ranges, range_min=0.0):
    """Return min finite range > range_min, or inf when no valid reading."""
    valid = [r for r in ranges if math.isfinite(r) and r > range_min]
    return min(valid) if valid else float('inf')


def select_action(min_dist, estop, obstacle_threshold=0.5, safety_threshold=0.15):
    """
    Decide the wanderer action from distance and e-stop state.

    Returns one of: 'stop', 'turn', 'forward'
    """
    if estop or min_dist < safety_threshold:
        return 'stop'
    if min_dist < obstacle_threshold:
        return 'turn'
    return 'forward'


class WandererNode(Node):

    def __init__(self):
        super().__init__('wanderer')
        self.declare_parameter('obstacle_threshold', 0.5)
        self.declare_parameter('safety_threshold', 0.15)
        self.declare_parameter('linear_speed', 0.22)
        self.declare_parameter('angular_speed', 0.5)

        self._obstacle_threshold = self.get_parameter('obstacle_threshold').value
        self._safety_threshold = self.get_parameter('safety_threshold').value
        self._linear_speed = self.get_parameter('linear_speed').value
        self._angular_speed = self.get_parameter('angular_speed').value

        self._estop = False
        self._min_dist = float('inf')
        self._range_min = 0.0
        self._prev_action = 'forward'
        self._turn_sign = 1.0   # +1 = left, -1 = right; alternates on new turn

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.create_subscription(LaserScan, '/scan', self._scan_cb, 10)
        self.create_subscription(Bool, '/estop', self._estop_cb, _ESTOP_QOS)

        self.create_timer(1.0 / CONTROL_HZ, self._control_tick)

        self.get_logger().info(
            f'WandererNode ready — obstacle={self._obstacle_threshold}m '
            f'safety={self._safety_threshold}m '
            f'v={self._linear_speed}m/s w={self._angular_speed}rad/s'
        )

    # ── callbacks ──────────────────────────────────────────────────────────────

    def _scan_cb(self, msg: LaserScan):
        self._range_min = msg.range_min
        self._min_dist = min_finite_range(msg.ranges, msg.range_min)

    def _estop_cb(self, msg: Bool):
        if msg.data != self._estop:
            self._estop = msg.data
            state = 'ACTIVE' if self._estop else 'cleared'
            self.get_logger().warn(f'E-stop {state}')

    # ── control loop ───────────────────────────────────────────────────────────

    def _control_tick(self):
        action = select_action(
            self._min_dist,
            self._estop,
            self._obstacle_threshold,
            self._safety_threshold,
        )

        # Flip turn direction each time we newly enter turn state
        if action == 'turn' and self._prev_action != 'turn':
            self._turn_sign *= -1.0

        twist = Twist()
        if action == 'forward':
            twist.linear.x = self._linear_speed
        elif action == 'turn':
            twist.angular.z = self._angular_speed * self._turn_sign
        # 'stop' → zero twist (default)

        self._cmd_pub.publish(twist)
        self._prev_action = action


def main(args=None):
    rclpy.init(args=args)
    node = WandererNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
