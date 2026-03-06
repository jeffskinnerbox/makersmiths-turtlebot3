#!/usr/bin/env python3
"""Drive robot in a circle to build up SLAM map, then stop."""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

rclpy.init()
node = Node("map_driver")
pub = node.create_publisher(Twist, "/cmd_vel", 10)
time.sleep(1)

msg = Twist()
msg.linear.x = 0.15
msg.angular.z = 0.5
start = time.time()
while time.time() - start < 15.0:
    pub.publish(msg)
    time.sleep(0.1)

msg.linear.x = 0.0
msg.angular.z = 0.0
pub.publish(msg)
time.sleep(0.5)
node.destroy_node()
rclpy.shutdown()
print("DONE")
