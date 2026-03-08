"""
gamepad_manager_node.py — Gamepad e-stop, restart, and /cmd_vel gating.

Subscribes to /joy and /cmd_vel_raw (teleop output); publishes gated /cmd_vel.

Button mapping (F310 D-mode, confirmed D5 2026-03-08):
  A (btn 0) — green  — clear e-stop / restart
  B (btn 1) — red    — emergency stop
  Y (btn 3) — yellow — shutdown gamepad nodes (reboot: Phase 5)

E-stop state machine:
  RUNNING  → B pressed → STOPPED  (zero /cmd_vel, /estop=true)
  STOPPED  → A pressed → RUNNING  (/estop=false, motion resumes)
  RUNNING  → Y pressed → shutdown all gamepad nodes

/estop QoS: RELIABLE + TRANSIENT_LOCAL so late subscribers get current state.
"""
import signal
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

_ESTOP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class GamepadManagerNode(Node):

    BTN_A = 0   # green  — clear e-stop
    BTN_B = 1   # red    — emergency stop
    BTN_Y = 3   # yellow — shutdown / reboot

    def __init__(self):
        super().__init__('gamepad_manager')
        self._estop = False
        self._prev_buttons = []

        # Gate: subscribe to teleop output, republish to real /cmd_vel
        self.create_subscription(Twist, '/cmd_vel_raw', self._cmd_vel_cb, 10)
        self._cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # E-stop status topic (latched so monitors always get current state)
        self._estop_pub = self.create_publisher(Bool, '/estop', _ESTOP_QOS)

        self.create_subscription(Joy, '/joy', self._joy_cb, 10)

        # Publish initial state
        self._publish_estop()
        self.get_logger().info('GamepadManagerNode ready. B=estop  A=clear  Y=shutdown')

    # ── cmd_vel relay ────────────────────────────────────────────────────────

    def _cmd_vel_cb(self, msg: Twist):
        if self._estop:
            self._cmd_vel_pub.publish(Twist())   # zero velocity while stopped
        else:
            self._cmd_vel_pub.publish(msg)

    # ── joy handler ──────────────────────────────────────────────────────────

    def _joy_cb(self, msg: Joy):
        buttons = list(msg.buttons)
        prev = self._prev_buttons if self._prev_buttons else [0] * len(buttons)

        def pressed(idx):
            return len(buttons) > idx and buttons[idx] == 1 and (
                len(prev) <= idx or prev[idx] == 0)

        if pressed(self.BTN_B):
            self._activate_estop()

        elif pressed(self.BTN_A):
            self._clear_estop()

        elif pressed(self.BTN_Y):
            self._shutdown_requested()

        self._prev_buttons = buttons

    # ── state transitions ────────────────────────────────────────────────────

    def _activate_estop(self):
        if not self._estop:
            self._estop = True
            self._cmd_vel_pub.publish(Twist())   # immediate zero
            self._publish_estop()
            self.get_logger().warn('E-STOP activated (B). Press A to clear.')

    def _clear_estop(self):
        if self._estop:
            self._estop = False
            self._publish_estop()
            self.get_logger().info('E-stop cleared (A). Motion resumed.')

    def _shutdown_requested(self):
        self.get_logger().warn('Shutdown requested (Y). Stopping motion and exiting.')
        self._estop = True
        self._cmd_vel_pub.publish(Twist())
        self._publish_estop()
        # Signal the entire process group so launch shuts down all nodes
        os.kill(os.getpgid(0), signal.SIGINT)

    def _publish_estop(self):
        msg = Bool()
        msg.data = self._estop
        self._estop_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = GamepadManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
