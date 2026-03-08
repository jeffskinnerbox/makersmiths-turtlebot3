"""
Unit tests for GamepadManagerNode e-stop state machine.

Tests run without a live ROS context — logic extracted for pure-python testing.
"""
import pytest


# ── Minimal stub to test state machine logic without rclpy ───────────────────

class _FakePub:
    def __init__(self):
        self.msgs = []

    def publish(self, msg):
        self.msgs.append(msg)


class _FakeTwist:
    def __init__(self, lx=0.0):
        self.linear = type('L', (), {'x': lx, 'y': 0.0, 'z': 0.0})()
        self.angular = type('A', (), {'x': 0.0, 'y': 0.0, 'z': 0.0})()


class _FakeBool:
    def __init__(self, data=False):
        self.data = data


class _FakeJoy:
    def __init__(self, buttons):
        self.buttons = buttons


class GamepadManagerLogic:
    """Pure-python copy of the state machine for unit testing."""

    BTN_A = 0
    BTN_B = 1
    BTN_Y = 3

    def __init__(self, cmd_pub, estop_pub):
        self._estop = False
        self._prev_buttons = []
        self._cmd_pub = cmd_pub
        self._estop_pub = estop_pub
        self._shutdown_called = False
        self._publish_estop()

    def _publish_estop(self):
        msg = _FakeBool(self._estop)
        self._estop_pub.publish(msg)

    def cmd_vel_cb(self, twist):
        if self._estop:
            self._cmd_pub.publish(_FakeTwist(0.0))
        else:
            self._cmd_pub.publish(twist)

    def joy_cb(self, joy):
        buttons = list(joy.buttons)
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

    def _activate_estop(self):
        if not self._estop:
            self._estop = True
            self._cmd_pub.publish(_FakeTwist(0.0))
            self._publish_estop()

    def _clear_estop(self):
        if self._estop:
            self._estop = False
            self._publish_estop()

    def _shutdown_requested(self):
        self._estop = True
        self._cmd_pub.publish(_FakeTwist(0.0))
        self._publish_estop()
        self._shutdown_called = True


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def manager():
    cmd_pub = _FakePub()
    estop_pub = _FakePub()
    m = GamepadManagerLogic(cmd_pub, estop_pub)
    return m, cmd_pub, estop_pub


def _joy(buttons):
    return _FakeJoy(buttons)


# ── Button index mapping ──────────────────────────────────────────────────────

def test_button_indices():
    assert GamepadManagerLogic.BTN_A == 0   # green
    assert GamepadManagerLogic.BTN_B == 1   # red / estop
    assert GamepadManagerLogic.BTN_Y == 3   # yellow / reboot


# ── Initial state ─────────────────────────────────────────────────────────────

def test_initial_estop_false(manager):
    m, _, estop_pub = manager
    assert m._estop is False
    assert estop_pub.msgs[-1].data is False


def test_initial_cmd_vel_passes_through(manager):
    m, cmd_pub, _ = manager
    m.cmd_vel_cb(_FakeTwist(0.5))
    assert cmd_pub.msgs[-1].linear.x == 0.5


# ── E-stop activation (B button) ─────────────────────────────────────────────

def test_b_activates_estop(manager):
    m, _, estop_pub = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B pressed
    assert m._estop is True
    assert estop_pub.msgs[-1].data is True


def test_b_publishes_zero_velocity(manager):
    m, cmd_pub, _ = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    assert cmd_pub.msgs[-1].linear.x == 0.0


def test_estop_suppresses_cmd_vel(manager):
    m, cmd_pub, _ = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B
    m.cmd_vel_cb(_FakeTwist(0.5))                         # teleop sends velocity
    assert cmd_pub.msgs[-1].linear.x == 0.0               # blocked


def test_b_idempotent_when_already_stopped(manager):
    m, _, estop_pub = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    count_before = len(estop_pub.msgs)
    m._prev_buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # simulate release
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))     # B again
    assert len(estop_pub.msgs) == count_before              # no duplicate publish


# ── E-stop clear (A button) ───────────────────────────────────────────────────

def test_a_clears_estop(manager):
    m, _, estop_pub = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B
    m._prev_buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    m.joy_cb(_joy([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # A
    assert m._estop is False
    assert estop_pub.msgs[-1].data is False


def test_a_resumes_cmd_vel(manager):
    m, cmd_pub, _ = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B
    m._prev_buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    m.joy_cb(_joy([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # A
    m.cmd_vel_cb(_FakeTwist(0.3))
    assert cmd_pub.msgs[-1].linear.x == 0.3


def test_a_noop_when_not_estopped(manager):
    m, _, estop_pub = manager
    count_before = len(estop_pub.msgs)
    m.joy_cb(_joy([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # A without prior B
    assert len(estop_pub.msgs) == count_before


# ── Shutdown (Y button) ───────────────────────────────────────────────────────

def test_y_sets_estop_and_requests_shutdown(manager):
    m, cmd_pub, estop_pub = manager
    m.joy_cb(_joy([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]))   # Y
    assert m._estop is True
    assert estop_pub.msgs[-1].data is True
    assert cmd_pub.msgs[-1].linear.x == 0.0
    assert m._shutdown_called is True


# ── Edge detection (no re-trigger on hold) ────────────────────────────────────

def test_b_held_does_not_re_trigger(manager):
    m, _, estop_pub = manager
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B press
    count_after_press = len(estop_pub.msgs)
    m.joy_cb(_joy([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]))   # B held
    assert len(estop_pub.msgs) == count_after_press        # no extra publish
