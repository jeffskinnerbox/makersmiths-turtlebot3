"""Shared pytest fixtures for tb3_bringup integration tests.

Session-scoped rclpy init/shutdown so that rclpy.init() is called exactly
once per pytest process (rclpy does not support re-initialization).
"""

import pytest
import rclpy


@pytest.fixture(scope="session", autouse=True)
def rclpy_init():
    rclpy.init()
    yield
    rclpy.shutdown()
