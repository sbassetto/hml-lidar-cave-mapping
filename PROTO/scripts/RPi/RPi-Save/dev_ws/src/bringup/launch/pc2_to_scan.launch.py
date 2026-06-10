from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_scan = LaunchConfiguration('use_scan', default='true')

    return LaunchDescription([

        # allow turning scan on/off
        DeclareLaunchArgument(
            'use_scan',
            default_value='true',
            description='Whether to launch the pointcloud_to_laserscan node'
        ),

        Node(
            package    = 'tf2_ros',
            executable = 'static_transform_publisher',
            name       = 'static_sensor_to_base_link',
            # each CLI token **must** be its own string
            arguments  = [
                '0.0', '0.0', '0.05',          # x y z
                '-1.570796',   '0.0',   '0.0',     # yaw pitch roll
                'sensor', 'base_link'          # parent  child
            ],
            output = 'screen',                 # optional: pipe logs to terminal
            # arguments += ['--period', '0.05']  # uncomment → re-broadcast at 20 Hz
        ),


        Node(
            package='py_avoid',
            executable='odom',      # same token you use with ros2 run
            name='odom',
            output='screen',
            # parameters=[...]                # add params if the node accepts any
        ),

        Node(
            package='py_avoid',
            executable='scan_rotator',      # same token you use with ros2 run
            name='scan_rotator',
            output='screen',
            # parameters=[...]                # add params if the node accepts any
        ),

        Node(
            package='py_avoid',
            executable='scan_to_mavlink',      # same token you use with ros2 run
            name='scan_to_mavlink',
            output='screen',
            # parameters=[...]                # add params if the node accepts any
        ),


        # pointcloud_to_laserscan, only if use_scan == true
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            condition=IfCondition(use_scan),
            remappings=[
                ('cloud_in', '/registered_scan'),
                ('scan',    '/scan'),
            ],
            parameters=[{
                'target_frame':       'sensor',
                'transform_tolerance': 0.1,
                'min_height':         0.0,
                'max_height':         0.1,
                'angle_min':         -3.141592,
                'angle_max':          3.141592,
                'angle_increment':    0.0087,
                'scan_time':          0.2,
                'range_min':          0.3,
                'range_max':          20.0,
                'use_inf':            True,
                'inf_epsilon':        1.0,
            }],
        ),

    ])
