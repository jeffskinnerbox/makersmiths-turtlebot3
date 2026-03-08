"""Unit tests for launch file structure and argument defaults."""
import os
import ast
import pytest


LAUNCH_DIR = os.path.join(os.path.dirname(__file__), '..', 'launch')


def _read_launch(filename):
    path = os.path.join(LAUNCH_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


def test_sim_bringup_exists():
    assert os.path.isfile(os.path.join(LAUNCH_DIR, 'sim_bringup.launch.py'))


def test_sim_house_exists():
    assert os.path.isfile(os.path.join(LAUNCH_DIR, 'sim_house.launch.py'))


def test_teleop_exists():
    assert os.path.isfile(os.path.join(LAUNCH_DIR, 'teleop.launch.py'))


def test_sim_bringup_has_headless_arg():
    src = _read_launch('sim_bringup.launch.py')
    assert "'headless'" in src or '"headless"' in src


def test_sim_bringup_headless_default_false():
    src = _read_launch('sim_bringup.launch.py')
    assert "'false'" in src or '"false"' in src


def test_sim_house_has_headless_arg():
    src = _read_launch('sim_house.launch.py')
    assert "'headless'" in src or '"headless"' in src


def test_sim_bringup_references_warehouse_world():
    src = _read_launch('sim_bringup.launch.py')
    assert 'tb3_warehouse' in src


def test_sim_house_references_house_world():
    src = _read_launch('sim_house.launch.py')
    assert 'tb3_house' in src


def test_teleop_uses_teleop_twist_keyboard():
    """G11: package= must be teleop_twist_keyboard, not turtlebot3_teleop."""
    src = _read_launch('teleop.launch.py')
    assert "package='teleop_twist_keyboard'" in src or 'package="teleop_twist_keyboard"' in src


def test_sim_bringup_parses_as_valid_python():
    src = _read_launch('sim_bringup.launch.py')
    ast.parse(src)  # raises SyntaxError if invalid


def test_sim_house_parses_as_valid_python():
    src = _read_launch('sim_house.launch.py')
    ast.parse(src)


def test_teleop_parses_as_valid_python():
    src = _read_launch('teleop.launch.py')
    ast.parse(src)
