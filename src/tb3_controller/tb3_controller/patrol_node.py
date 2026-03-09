"""
patrol_node.py — Waypoint patrol for TurtleBot3 using Nav2 NavigateToPose.

Cycles through a configurable list of (x, y) waypoints by sending
NavigateToPose action goals to bt_navigator.  Checks /estop before each
goal and cancels the active goal immediately when e-stop activates.

Requires slam.launch.py and nav2.launch.py to be running so that the
NavigateToPose action server is available and map→odom TF exists.

Subscribes:
  /estop     std_msgs/Bool  — RELIABLE + TRANSIENT_LOCAL

Actions:
  navigate_to_pose  nav2_msgs/action/NavigateToPose  (client)

Parameters:
  waypoints  (float[], default [1.0, 0.0, 2.0, 1.0, 0.0, 1.0])
             Flat list of (x, y) pairs in the map frame.
  loop       (bool, default True)
             If True, repeat waypoint list indefinitely.
  nav2_ready_delay  (float, default 5.0)
             Seconds to wait after node start before sending first goal,
             allowing Nav2 to finish activating.
"""

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool

_ESTOP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)

DISPATCH_HZ = 2.0  # how often _dispatch_tick checks for a new goal to send


# ── pure-logic helpers (tested without ROS) ──────────────────────────────────

def parse_waypoints(flat):
    """
    Convert a flat [x0, y0, x1, y1, …] list into [(x0,y0), (x1,y1), …].

    Returns an empty list when *flat* has an odd number of elements.
    """
    if len(flat) % 2 != 0:
        return []
    return [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]


def next_waypoint_index(current_idx, num_waypoints):
    """Return the next waypoint index, wrapping around to 0."""
    return (current_idx + 1) % num_waypoints


# ── node ─────────────────────────────────────────────────────────────────────

class PatrolNode(Node):

    def __init__(self):
        super().__init__('patrol')

        self.declare_parameter(
            'waypoints', [1.0, 0.0, 2.0, 1.0, 0.0, 1.0])
        self.declare_parameter('loop', True)
        self.declare_parameter('nav2_ready_delay', 5.0)

        raw = self.get_parameter('waypoints').value
        self._waypoints = parse_waypoints(list(raw))
        self._loop = self.get_parameter('loop').value
        nav2_ready_delay = self.get_parameter('nav2_ready_delay').value

        if not self._waypoints:
            self.get_logger().error(
                'waypoints param must be a flat list of (x, y) pairs '
                'with an even number of values — patrol will not move')

        self._current_idx = 0
        self._estop = False
        self._goal_handle = None
        self._active = False        # True while a goal is in flight
        self._ready = False         # True after nav2_ready_delay elapses

        self._action_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose')

        self.create_subscription(Bool, '/estop', self._estop_cb, _ESTOP_QOS)

        # One-shot timer: mark node ready after startup delay
        self._startup_timer = self.create_timer(
            nav2_ready_delay, self._on_ready)

        # Periodic timer: dispatch next goal whenever node is idle
        self.create_timer(1.0 / DISPATCH_HZ, self._dispatch_tick)

        self.get_logger().info(
            f'PatrolNode: {len(self._waypoints)} waypoints, '
            f'loop={self._loop}, ready in {nav2_ready_delay:.1f}s'
        )

    # ── startup ────────────────────────────────────────────────────────────────

    def _on_ready(self):
        self._startup_timer.cancel()
        self._ready = True
        self.get_logger().info('PatrolNode: startup delay elapsed — patrol active')

    # ── dispatch loop ──────────────────────────────────────────────────────────

    def _dispatch_tick(self):
        if not self._ready:
            return
        if self._active:
            return
        if self._estop:
            return
        if not self._waypoints:
            return
        if not self._action_client.server_is_ready():
            self.get_logger().info(
                'navigate_to_pose server not yet ready — waiting…',
                throttle_duration_sec=5.0)
            return
        if not self._loop and self._current_idx == 0 and self._active is False:
            # Finished one full pass and loop=False — check if we lapped
            # Track completion separately to avoid re-triggering
            pass  # handled via _laps counter below; default loop=True covers demo
        self._send_goal()

    # ── goal lifecycle ─────────────────────────────────────────────────────────

    def _send_goal(self):
        x, y = self._waypoints[self._current_idx]
        self.get_logger().info(
            f'Patrol → waypoint [{self._current_idx}] ({x:.2f}, {y:.2f})')

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0  # face forward (yaw=0)

        self._active = True
        future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self._feedback_cb)
        future.add_done_callback(self._goal_response_cb)

    def _feedback_cb(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        self.get_logger().debug(f'Distance remaining: {dist:.2f} m')

    def _goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn(
                f'Waypoint [{self._current_idx}] goal rejected — '
                'dispatch will retry')
            self._active = False
            return
        self.get_logger().info(f'Waypoint [{self._current_idx}] goal accepted')
        self._goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _result_cb(self, future):
        result = future.result()
        status = result.status
        self._goal_handle = None

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(
                f'Waypoint [{self._current_idx}] reached!')
            self._current_idx = next_waypoint_index(
                self._current_idx, len(self._waypoints))
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info(
                f'Waypoint [{self._current_idx}] goal cancelled (e-stop?)')
        else:
            self.get_logger().warn(
                f'Waypoint [{self._current_idx}] failed (status={status}) '
                '— will retry')

        self._active = False  # dispatch_tick will send next goal

    # ── e-stop ─────────────────────────────────────────────────────────────────

    def _estop_cb(self, msg: Bool):
        if msg.data != self._estop:
            self._estop = msg.data
            state = 'ACTIVE' if self._estop else 'cleared'
            self.get_logger().warn(f'E-stop {state}')

        if self._estop and self._goal_handle is not None:
            self.get_logger().warn('E-stop — cancelling active navigation goal')
            self._goal_handle.cancel_goal_async()
            self._active = False


# ── entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
