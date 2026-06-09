#!/usr/bin/env python3
"""
Rotate a PointCloud2 by +90 deg around the Z-axis.

  input : /registered_scan         (sensor_msgs/PointCloud2)
  output: /registered_scan_rot90   (sensor_msgs/PointCloud2)

Add this file to a Python-based ROS 2 package, list it in
setup.py’s entry_points, then:

    ros2 run <your_pkg> scan_rotator.py
"""
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2          # ROS 2 helper
import numpy as np

# 90° rotation matrix about +Z
ROT_Z_POS90 = np.array([[ 0., -1., 0.],
                        [ 1.,  0., 0.],
                        [ 0.,  0., 1.]], dtype=np.float32)


class ScanRotator(Node):
    """Subscribe to /registered_scan, publish a +90 deg-rotated cloud."""

    def __init__(self):
        super().__init__('scan_rotator')
        qos = 10
        self.sub = self.create_subscription(
            PointCloud2, '/registered_scan', self.cb_scan, qos)
        self.pub = self.create_publisher(
            PointCloud2, '/registered_scan_rot90', qos)
        self.get_logger().info('Listening on /registered_scan')

    # --------------------------------------------------------------------- #
    def cb_scan(self, msg: PointCloud2):
        # 1. Grab xyz as plain floats
        xyz = np.array(
            [(p[0], p[1], p[2])                     # x, y, z
            for p in pc2.read_points(msg,
                                    field_names=('x', 'y', 'z'),
                                    skip_nans=True)],
            dtype=np.float32
        )
        if xyz.size == 0:
            return                                  # empty cloud

        # 2. Rotate (+90° about Z)
        xyz_rot = xyz @ ROT_Z_POS90.T

        # 3. Convert each original record → tuple so we can splice
        full_pts = [tuple(p) for p in pc2.read_points(msg, skip_nans=True)]

        for i in range(len(full_pts)):
            full_pts[i] = (xyz_rot[i, 0], xyz_rot[i, 1], xyz_rot[i, 2]) \
                        + full_pts[i][3:]         # keep intensity, etc.

        # 4. Publish
        out = pc2.create_cloud(msg.header, msg.fields, full_pts)
        self.pub.publish(out)

    # --------------------------------------------------------------------- #


def main(args=None):
    rclpy.init(args=args)
    node = ScanRotator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
