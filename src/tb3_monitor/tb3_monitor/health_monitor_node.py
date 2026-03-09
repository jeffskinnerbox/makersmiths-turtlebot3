"""
health_monitor_node.py — System health monitor for TurtleBot3.

Subscribes to /battery_state and /imu, logging both at 1 Hz.
When topics are not publishing (e.g. in simulation), the node logs
"no data" warnings until data arrives.

For simulation use, run the mock battery publisher entry point
in a separate terminal:
    ros2 run tb3_monitor mock_battery

Subscribes:
  /battery_state  sensor_msgs/BatteryState  — voltage + charge %
  /imu            sensor_msgs/Imu           — orientation + angular vel

Parameters:
  log_rate  (float, default 1.0) — Hz for health log output
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu

_NO_DATA = '(no data)'


def _yaw_from_quat(q):
    """Extract yaw (radians) from a geometry_msgs Quaternion."""
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


class HealthMonitorNode(Node):

    def __init__(self):
        super().__init__('health_monitor')
        self.declare_parameter('log_rate', 1.0)
        rate = self.get_parameter('log_rate').value

        self._battery: BatteryState | None = None
        self._imu: Imu | None = None

        self.create_subscription(
            BatteryState, '/battery_state', self._battery_cb, 10)
        self.create_subscription(Imu, '/imu', self._imu_cb, 10)
        self.create_timer(1.0 / rate, self._log_tick)

        self.get_logger().info(
            f'HealthMonitorNode ready — logging at {rate} Hz')

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _battery_cb(self, msg: BatteryState):
        self._battery = msg

    def _imu_cb(self, msg: Imu):
        self._imu = msg

    # ── log loop ──────────────────────────────────────────────────────────────

    def _log_tick(self):
        bat_str = self._fmt_battery()
        imu_str = self._fmt_imu()
        self.get_logger().info(f'battery: {bat_str} | imu: {imu_str}')

    def _fmt_battery(self):
        if self._battery is None:
            return _NO_DATA
        b = self._battery
        pct = f'{b.percentage * 100:.0f}%' if b.percentage >= 0.0 else '?%'
        return f'{b.voltage:.2f}V  {pct}'

    def _fmt_imu(self):
        if self._imu is None:
            return _NO_DATA
        yaw = math.degrees(_yaw_from_quat(self._imu.orientation))
        wx = self._imu.angular_velocity.x
        wy = self._imu.angular_velocity.y
        wz = self._imu.angular_velocity.z
        return f'yaw={yaw:.1f}°  ω=({wx:.2f},{wy:.2f},{wz:.2f})rad/s'


def main(args=None):
    rclpy.init(args=args)
    node = HealthMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


# ── Mock battery publisher (for simulation) ───────────────────────────────────

class MockBatteryPublisher(Node):
    """Publishes a fake /battery_state at 1 Hz for use in simulation."""

    VOLTAGE = 12.0        # V — nominal 3S LiPo
    PERCENTAGE = 0.75     # 75 %

    def __init__(self):
        super().__init__('mock_battery')
        self._pub = self.create_publisher(BatteryState, '/battery_state', 10)
        self.create_timer(1.0, self._publish)
        self.get_logger().info(
            f'MockBatteryPublisher: /battery_state @ '
            f'{self.VOLTAGE}V / {self.PERCENTAGE * 100:.0f}%')

    def _publish(self):
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.voltage = self.VOLTAGE
        msg.percentage = self.PERCENTAGE
        msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        msg.present = True
        self._pub.publish(msg)


def mock_battery_main(args=None):
    rclpy.init(args=args)
    node = MockBatteryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
