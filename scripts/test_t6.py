"""T6 test: SLAM stack starts and /map publishes; map can be saved.

Run inside the simulator container after slam.launch.py is running:
  ros2 launch tb3_bringup slam.launch.py headless:=true

Pass criteria:
  1. /slam_toolbox node is running
  2. /map topic is publishing data
  3. slam_toolbox/save_map service saves .pgm + .yaml files

Usage:
  python3 ~/ros2_ws/scripts/test_t6.py
"""

import os
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid
from slam_toolbox.srv import SaveMap
from std_msgs.msg import String

MAP_LATCHED_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    depth=1,
)

MAP_SAVE_PATH = '/tmp/t6_test_map'


class T6Tester(Node):
    def __init__(self):
        super().__init__('t6_tester')
        self._map_received = False
        self._map_width = 0
        self._map_height = 0

        self._map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self._map_callback,
            MAP_LATCHED_QOS,
        )
        self._save_map_client = self.create_client(SaveMap, '/slam_toolbox/save_map')

    def _map_callback(self, msg: OccupancyGrid):
        self._map_received = True
        self._map_width = msg.info.width
        self._map_height = msg.info.height

    def wait_for_map(self, timeout=15.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self._map_received:
                return True
        return False

    def save_map(self, path: str, timeout=10.0) -> bool:
        if not self._save_map_client.wait_for_service(timeout_sec=timeout):
            return False
        req = SaveMap.Request()
        req.name = String(data=path)
        future = self._save_map_client.call_async(req)
        deadline = time.time() + timeout
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if future.done():
                return future.result().result == 0
        return False


def main():
    rclpy.init()
    node = T6Tester()
    failures = []

    # --- Check 1: /map publishing ---
    if not node.wait_for_map(timeout=15.0):
        print('T6_FAIL: /map not received after 15 s')
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)
    print(f'PASS: /map publishing ({node._map_width}x{node._map_height} cells)')

    # --- Check 2: save map via slam_toolbox service ---
    # Clean up any previous test files
    for ext in ('.pgm', '.yaml'):
        p = MAP_SAVE_PATH + ext
        if os.path.exists(p):
            os.remove(p)

    if node.save_map(MAP_SAVE_PATH):
        pgm_ok = os.path.exists(MAP_SAVE_PATH + '.pgm')
        yaml_ok = os.path.exists(MAP_SAVE_PATH + '.yaml')
        if pgm_ok and yaml_ok:
            pgm_size = os.path.getsize(MAP_SAVE_PATH + '.pgm')
            print(f'PASS: map saved — {MAP_SAVE_PATH}.pgm ({pgm_size} bytes) + .yaml')
        else:
            failures.append(f'save_map returned OK but files missing: pgm={pgm_ok} yaml={yaml_ok}')
    else:
        failures.append('slam_toolbox/save_map service call failed or timed out')

    node.destroy_node()
    rclpy.shutdown()

    if failures:
        for f in failures:
            print(f'T6_FAIL: {f}')
        sys.exit(1)
    else:
        print('T6_PASS')


if __name__ == '__main__':
    main()
