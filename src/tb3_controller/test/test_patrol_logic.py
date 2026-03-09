"""
Unit tests for patrol_node pure-logic functions.

Tests run without a live ROS context — pure Python only.
"""
import pytest

from tb3_controller.patrol_node import next_waypoint_index, parse_waypoints


# ── parse_waypoints ───────────────────────────────────────────────────────────

def test_parse_empty_list():
    assert parse_waypoints([]) == []


def test_parse_single_waypoint():
    assert parse_waypoints([1.0, 2.0]) == [(1.0, 2.0)]


def test_parse_three_waypoints():
    result = parse_waypoints([1.0, 0.0, 2.0, 1.0, 0.0, 1.0])
    assert result == [(1.0, 0.0), (2.0, 1.0), (0.0, 1.0)]


def test_parse_negative_coords():
    result = parse_waypoints([-1.0, -2.0, 3.0, 4.0])
    assert result == [(-1.0, -2.0), (3.0, 4.0)]


def test_parse_odd_length_returns_empty():
    assert parse_waypoints([1.0, 2.0, 3.0]) == []


def test_parse_single_element_returns_empty():
    assert parse_waypoints([1.0]) == []


def test_parse_preserves_float_precision():
    result = parse_waypoints([0.123456, 0.654321])
    assert result[0][0] == pytest.approx(0.123456)
    assert result[0][1] == pytest.approx(0.654321)


# ── next_waypoint_index ───────────────────────────────────────────────────────

def test_next_advances_index():
    assert next_waypoint_index(0, 3) == 1


def test_next_advances_middle():
    assert next_waypoint_index(1, 3) == 2


def test_next_wraps_last_to_zero():
    assert next_waypoint_index(2, 3) == 0


def test_next_wraps_single_waypoint():
    assert next_waypoint_index(0, 1) == 0


def test_next_wraps_two_waypoints():
    assert next_waypoint_index(1, 2) == 0
    assert next_waypoint_index(0, 2) == 1


def test_next_full_cycle_returns_to_start():
    """Verify cycling through all indices returns to 0."""
    n = 5
    idx = 0
    for _ in range(n):
        idx = next_waypoint_index(idx, n)
    assert idx == 0


def test_next_large_list():
    assert next_waypoint_index(99, 100) == 0
    assert next_waypoint_index(50, 100) == 51
