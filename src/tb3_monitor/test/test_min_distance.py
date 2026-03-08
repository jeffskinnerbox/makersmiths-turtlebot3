"""
Unit tests for lidar_monitor_node.min_finite_range.

Tests run without a live ROS context — pure Python logic only.
"""
import math
import pytest

from tb3_monitor.lidar_monitor_node import min_finite_range


def test_min_of_valid_ranges():
    assert min_finite_range([1.0, 0.5, 2.0]) == pytest.approx(0.5)


def test_single_range():
    assert min_finite_range([1.5]) == pytest.approx(1.5)


def test_inf_excluded():
    assert min_finite_range([float('inf'), 1.0, 2.0]) == pytest.approx(1.0)


def test_nan_excluded():
    assert min_finite_range([float('nan'), 1.0]) == pytest.approx(1.0)


def test_all_inf_returns_inf():
    assert math.isinf(min_finite_range([float('inf'), float('inf')]))


def test_empty_ranges_returns_inf():
    assert math.isinf(min_finite_range([]))


def test_below_range_min_excluded():
    # range_min=0.1 — readings at 0.05 should be skipped
    assert min_finite_range([0.05, 1.0], range_min=0.1) == pytest.approx(1.0)


def test_exactly_at_range_min_excluded():
    # > range_min is the condition; equal is excluded
    assert min_finite_range([0.1, 1.0], range_min=0.1) == pytest.approx(1.0)


def test_all_below_range_min_returns_inf():
    assert math.isinf(min_finite_range([0.05, 0.03], range_min=0.1))


def test_mixed_valid_and_invalid():
    ranges = [float('inf'), float('nan'), 0.05, 3.0, 1.5]
    # 0.05 is excluded (≤ range_min=0.1); valid = [3.0, 1.5]
    assert min_finite_range(ranges, range_min=0.1) == pytest.approx(1.5)
