"""T6: SLAM map building — /map publishes and can be saved via slam_toolbox service.

Requires slam.launch.py to be running (headless:=true).

Pass criteria:
  1. /map topic publishes an OccupancyGrid message
  2. /slam_toolbox/save_map service saves .pgm + .yaml files
"""

import os
import time

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from slam_toolbox.srv import SaveMap
from std_msgs.msg import String

MAP_LATCHED_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    depth=1,
)
MAP_SAVE_PATH = "/tmp/t6_pytest_map"


def test_map_publishing(rclpy_init):
    node = rclpy.create_node("t6_map_check")
    received = [False]

    def _cb(msg: OccupancyGrid):
        received[0] = True

    node.create_subscription(OccupancyGrid, "/map", _cb, MAP_LATCHED_QOS)

    deadline = time.time() + 15.0
    while not received[0] and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()
    assert received[0], "/map not received within 15 s — is slam.launch.py running?"


def test_map_can_be_saved(rclpy_init):
    node = rclpy.create_node("t6_save_check")
    client = node.create_client(SaveMap, "/slam_toolbox/save_map")

    assert client.wait_for_service(timeout_sec=10.0), (
        "/slam_toolbox/save_map service not available"
    )

    for ext in (".pgm", ".yaml"):
        p = MAP_SAVE_PATH + ext
        if os.path.exists(p):
            os.remove(p)

    req = SaveMap.Request()
    req.name = String(data=MAP_SAVE_PATH)
    future = client.call_async(req)

    deadline = time.time() + 10.0
    while not future.done() and time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    assert future.done(), "save_map service call timed out"
    assert future.result().result == 0, (
        f"save_map returned error code: {future.result().result}"
    )
    assert os.path.exists(MAP_SAVE_PATH + ".pgm"), f"{MAP_SAVE_PATH}.pgm not created"
    assert os.path.exists(MAP_SAVE_PATH + ".yaml"), f"{MAP_SAVE_PATH}.yaml not created"
