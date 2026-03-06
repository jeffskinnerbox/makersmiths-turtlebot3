"""T1: Container startup — ros2 and gz are available in PATH.

Run inside the simulator container (no stack required):

  docker exec turtlebot3_simulator bash -c "
    source /opt/ros/jazzy/setup.bash &&
    source ~/ros2_ws/install/setup.bash &&
    cd ~/ros2_ws &&
    python3 -m pytest src/tb3_bringup/test/test_t1_container_startup.py -v"

Pass criteria: both ros2 and gz are found in PATH.
"""

import shutil


def test_ros2_available():
    assert shutil.which("ros2") is not None, "ros2 not found in PATH"


def test_gz_available():
    assert shutil.which("gz") is not None, "gz not found in PATH"
