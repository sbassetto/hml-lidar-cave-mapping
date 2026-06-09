#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from mavros_msgs.srv import SetMavFrame
from quadrotor_msgs.msg import PositionCommand

class VelocityCommander(Node):
    def __init__(self):
        super().__init__('velocity_commander')

        self.vx = self.vy = self.vz = None  # Initialize velocities
        # 2) publisher to cmd_vel_unstamped
        self.pub = self.create_publisher(Twist,
                                         '/mavros/setpoint_velocity/cmd_vel_unstamped',
                                        5)
        
        self.sub = self.create_subscription(
            PositionCommand,            # message type
            '/drone_0_planning/pos_cmd',  # topic name (change to whatever your topic is)
            self.command_callback,              # callback function
            5                          # QoS depth
        )

        # 3) publish at 10 Hz
        self.timer = self.create_timer(0.05, self.command_publisher)
        self.info_timer = self.create_timer(1.0, self.publish_info)

    def publish_info(self):
        if self.vx is not None:
            self.get_logger().info(f"Sending command : vx={self.vx}, vy={self.vy}, vz={self.vz}")

    def command_callback(self, msg):
        self.vx = msg.velocity.x #E
        self.vy = msg.velocity.y #N
        self.vz = msg.velocity.z #U
        

    def command_publisher(self):
        if self.vx is None:
            self.get_logger().warn("Velocity command not received yet, skipping publish.")
            return
        msg = Twist()
        msg.linear.x  = float(self.vx) #E
        msg.linear.y  = float(self.vy) #N
        msg.linear.z  = float(self.vz) #U
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = VelocityCommander()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
