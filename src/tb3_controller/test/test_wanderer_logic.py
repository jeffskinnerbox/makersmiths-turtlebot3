"""
Unit tests for wanderer_node pure-logic functions.

Tests run without a live ROS context — pure Python only.
"""
import math
import pytest

from tb3_controller.wanderer_node import min_finite_range, select_action


# ── min_finite_range ─────────────────────────────────────────────────────────

def test_min_range_normal():
    assert min_finite_range([1.0, 2.0, 0.5]) == pytest.approx(0.5)


def test_min_range_inf_excluded():
    assert min_finite_range([float('inf'), 1.0]) == pytest.approx(1.0)


def test_min_range_all_inf_returns_inf():
    assert math.isinf(min_finite_range([float('inf'), float('inf')]))


def test_min_range_empty_returns_inf():
    assert math.isinf(min_finite_range([]))


def test_min_range_below_range_min_excluded():
    assert min_finite_range([0.05, 1.0], range_min=0.1) == pytest.approx(1.0)


# ── select_action ─────────────────────────────────────────────────────────────

def test_forward_when_clear():
    assert select_action(1.0, estop=False) == 'forward'


def test_forward_at_obstacle_threshold():
    # exactly at threshold → forward (condition is strictly <)
    assert select_action(0.5, estop=False) == 'forward'


def test_turn_when_obstacle_near():
    assert select_action(0.4, estop=False) == 'turn'


def test_turn_just_above_safety():
    # 0.16 is above safety_threshold (0.15) and below obstacle_threshold (0.5)
    assert select_action(0.16, estop=False) == 'turn'


def test_stop_at_safety_threshold():
    # exactly at safety_threshold (0.15) → still turn (not strictly <)
    assert select_action(0.15, estop=False) == 'turn'


def test_stop_below_safety_threshold():
    assert select_action(0.10, estop=False) == 'stop'


def test_stop_when_very_close():
    assert select_action(0.01, estop=False) == 'stop'


def test_estop_stops_regardless_of_distance():
    assert select_action(5.0, estop=True) == 'stop'


def test_estop_overrides_turn():
    assert select_action(0.3, estop=True) == 'stop'


def test_estop_overrides_forward():
    assert select_action(2.0, estop=True) == 'stop'


def test_custom_thresholds_forward():
    assert select_action(1.5, estop=False, obstacle_threshold=1.0, safety_threshold=0.5) == 'forward'


def test_custom_thresholds_turn():
    assert select_action(0.8, estop=False, obstacle_threshold=1.0, safety_threshold=0.5) == 'turn'


def test_custom_thresholds_stop():
    assert select_action(0.3, estop=False, obstacle_threshold=1.0, safety_threshold=0.5) == 'stop'
