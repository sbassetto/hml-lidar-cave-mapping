import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import (
    QoSProfile, qos_profile_sensor_data,
    ReliabilityPolicy, HistoryPolicy, DurabilityPolicy)

# QoS for the publisher (reliable, depth 10)
pub_qos = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE)

class ScanRelay(Node):
    def __init__(self):
        super().__init__('scan_relay')

        # BEST_EFFORT subscriber
        self.sub = self.create_subscription(
            LaserScan, '/scan', self.pub_cb, qos_profile_sensor_data)

        # RELIABLE publisher for MAVROS
        self.pub = self.create_publisher(
            LaserScan, '/mavros/obstacle/send', pub_qos)

        self.get_logger().info(
            'Relay running: /scan (BEST_EFFORT) → /mavros/obstacle/send (RELIABLE)')
    def pub_cb(self, msg):
            self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ScanRelay())
