"""Unit tests for bridge_params.yaml structure and correctness."""
import os
import yaml
import pytest


BRIDGE_PARAMS_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'config', 'bridge_params.yaml'
)


@pytest.fixture(scope='module')
def bridge_params():
    with open(BRIDGE_PARAMS_PATH, 'r') as f:
        return yaml.safe_load(f)


def _find_topic(bridge_params, ros_topic):
    return next((e for e in bridge_params if e.get('ros_topic_name') == ros_topic), None)


def test_bridge_params_loads(bridge_params):
    assert isinstance(bridge_params, list)
    assert len(bridge_params) > 0


def test_cmd_vel_uses_twist_not_stamped(bridge_params):
    """G10: /cmd_vel must use Twist, not TwistStamped."""
    entry = _find_topic(bridge_params, '/cmd_vel')
    assert entry is not None, '/cmd_vel entry missing'
    assert entry['ros_type_name'] == 'geometry_msgs/msg/Twist', (
        f"Expected geometry_msgs/msg/Twist, got {entry['ros_type_name']}"
    )


def test_cmd_vel_direction(bridge_params):
    entry = _find_topic(bridge_params, '/cmd_vel')
    assert entry['direction'] == 'ROS_TO_GZ'


def test_clock_present(bridge_params):
    entry = _find_topic(bridge_params, '/clock')
    assert entry is not None
    assert entry['ros_type_name'] == 'rosgraph_msgs/msg/Clock'
    assert entry['direction'] == 'GZ_TO_ROS'


def test_scan_present(bridge_params):
    entry = _find_topic(bridge_params, '/scan')
    assert entry is not None
    assert entry['ros_type_name'] == 'sensor_msgs/msg/LaserScan'
    assert entry['direction'] == 'GZ_TO_ROS'


def test_odom_present(bridge_params):
    entry = _find_topic(bridge_params, '/odom')
    assert entry is not None
    assert entry['ros_type_name'] == 'nav_msgs/msg/Odometry'
    assert entry['direction'] == 'GZ_TO_ROS'


def test_imu_present(bridge_params):
    entry = _find_topic(bridge_params, '/imu')
    assert entry is not None
    assert entry['ros_type_name'] == 'sensor_msgs/msg/Imu'


def test_all_entries_have_required_fields(bridge_params):
    required = {'ros_topic_name', 'gz_topic_name', 'ros_type_name', 'gz_type_name', 'direction'}
    for entry in bridge_params:
        missing = required - entry.keys()
        assert not missing, f"Entry {entry.get('ros_topic_name')} missing fields: {missing}"
