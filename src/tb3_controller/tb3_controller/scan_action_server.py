"""
scan_action_server.py — 360° rotation action server for TurtleBot3.

Implements a ROS 2 action server on /tb3_scan_360 using the
nav2_msgs/action/Spin type.  Accepts a target_yaw (radians) goal,
rotates the robot by that amount using /cmd_vel, and publishes
angular_distance_traveled feedback at 10 Hz.

Uses /odom to track actual rotation (yaw delta from start).
Requires a MultiThreadedExecutor so the odom subscription can
fire while execute_callback is blocking.

Action:
  /tb3_scan_360  nav2_msgs/action/Spin

Subscribes:
  /odom   nav_msgs/Odometry — used to track yaw progress

Publishes:
  /cmd_vel  geometry_msgs/Twist — rotation commands

Parameters:
  angular_speed  (float, default 1.0)  — rad/s rotation speed
"""
import math
import threading
import time as _time

from builtin_interfaces.msg import Duration
from geometry_msgs.msg import Twist
from nav2_msgs.action import Spin
from nav_msgs.msg import Odometry
import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

FEEDBACK_HZ = 10.0
TWO_PI = 2.0 * math.pi


def _yaw_from_odom(msg: Odometry) -> float:
    """Extract yaw (radians) from an Odometry message quaternion."""
    q = msg.pose.pose.orientation
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def _yaw_delta(prev: float, curr: float) -> float:
    """Signed shortest-path delta from prev to curr yaw (wraps ±π)."""
    d = curr - prev
    if d > math.pi:
        d -= TWO_PI
    elif d < -math.pi:
        d += TWO_PI
    return d


class ScanActionServer(Node):

    def __init__(self):
        super().__init__('scan_action_server')
        self.declare_parameter('angular_speed', 1.0)
        self._angular_speed = self.get_parameter('angular_speed').value

        self._odom_lock = threading.Lock()
        self._current_yaw: float | None = None

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self._odom_cb, 10)

        self._action_server = ActionServer(
            self,
            Spin,
            'tb3_scan_360',
            execute_callback=self._execute_cb,
            goal_callback=self._goal_cb,
            cancel_callback=self._cancel_cb,
        )

        self.get_logger().info(
            f'ScanActionServer ready on /tb3_scan_360 '
            f'(angular_speed={self._angular_speed:.2f} rad/s)')

    # ── odom ──────────────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry):
        with self._odom_lock:
            self._current_yaw = _yaw_from_odom(msg)

    # ── action server callbacks ────────────────────────────────────────────────

    def _goal_cb(self, goal_request):
        self.get_logger().info(
            f'Goal received: target_yaw={goal_request.target_yaw:.3f} rad')
        return GoalResponse.ACCEPT

    def _cancel_cb(self, goal_handle):
        self.get_logger().info('Cancel requested')
        return CancelResponse.ACCEPT

    def _execute_cb(self, goal_handle):
        target = abs(goal_handle.request.target_yaw)
        if target < 1e-4:
            target = TWO_PI   # default: full 360°
        direction = (
            1.0 if goal_handle.request.target_yaw >= 0.0 else -1.0)

        self.get_logger().info(
            f'Executing: {math.degrees(target):.1f}° '
            f'({"CCW" if direction > 0 else "CW"})')

        # Wait for first odom reading
        deadline = _time.monotonic() + 5.0
        while _time.monotonic() < deadline:
            with self._odom_lock:
                if self._current_yaw is not None:
                    break
            _time.sleep(0.05)
        else:
            self.get_logger().error('No /odom data — aborting')
            goal_handle.abort()
            return Spin.Result()

        with self._odom_lock:
            start_yaw = self._current_yaw
            prev_yaw = self._current_yaw
        accumulated = 0.0

        cmd = Twist()
        cmd.angular.z = self._angular_speed * direction

        start_time = _time.monotonic()
        period = 1.0 / FEEDBACK_HZ

        while True:
            if goal_handle.is_cancel_requested:
                self._stop()
                goal_handle.canceled()
                return Spin.Result()

            self._cmd_pub.publish(cmd)

            with self._odom_lock:
                curr = self._current_yaw
            delta = _yaw_delta(prev_yaw, curr)
            # Only accumulate rotation in the commanded direction
            if direction * delta > 0:
                accumulated += abs(delta)
            prev_yaw = curr

            # Publish feedback
            fb = Spin.Feedback()
            fb.angular_distance_traveled = accumulated
            goal_handle.publish_feedback(fb)

            if accumulated >= target:
                break

            _time.sleep(period)

        self._stop()
        elapsed = _time.monotonic() - start_time

        self.get_logger().info(
            f'Rotation complete: {math.degrees(accumulated):.1f}° '
            f'in {elapsed:.2f}s')

        goal_handle.succeed()
        result = Spin.Result()
        result.total_elapsed_time = Duration(
            sec=int(elapsed), nanosec=int((elapsed % 1) * 1e9))
        return result

    def _stop(self):
        self._cmd_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = ScanActionServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
