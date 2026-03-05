#!/usr/bin/env python3
"""T4 test: publish /cmd_vel, verify /odom position changes."""
import sys
import time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

rclpy.init()
node = rclpy.create_node('t4_test')
positions = []

def odom_cb(msg):
    positions.append(msg.pose.pose.position.x)

sub = node.create_subscription(Odometry, '/odom', odom_cb, 10)
pub = node.create_publisher(Twist, '/cmd_vel', 10)

# Collect baseline odom for 3 s
t_end = time.time() + 3
while time.time() < t_end:
    rclpy.spin_once(node, timeout_sec=0.1)

before = positions[-1] if positions else None
print('before_x=' + str(before) + ' samples=' + str(len(positions)))

# Drive forward for 4 s
twist = Twist()
twist.linear.x = 0.3
t_end = time.time() + 4
while time.time() < t_end:
    pub.publish(twist)
    rclpy.spin_once(node, timeout_sec=0.1)

# Stop and collect final odom
twist.linear.x = 0.0
pub.publish(twist)
t_end = time.time() + 2
while time.time() < t_end:
    rclpy.spin_once(node, timeout_sec=0.1)

after = positions[-1] if positions else None
print('after_x=' + str(after) + ' total_samples=' + str(len(positions)))

if before is None or after is None:
    print('T4_INCONCLUSIVE_no_odom')
    sys.exit(1)
elif abs(after - before) > 0.01:
    print('T4_PASS')
    sys.exit(0)
else:
    print('T4_FAIL_no_movement before=' + str(before) + ' after=' + str(after))
    sys.exit(1)

node.destroy_node()
rclpy.shutdown()
