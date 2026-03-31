from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        # ---------- FRONT CAMERA ----------
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='front_camera',
            parameters=[{
                'video_device': '/dev/video0'
            }],
            remappings=[
                ('/image_raw', '/camera/front/image_raw')
            ]
        ),

        # ---------- DOWN CAMERA ----------
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='down_camera',
            parameters=[{
                'video_device': '/dev/video2'
            }],
            remappings=[
                ('/image_raw', '/camera/down/image_raw')
            ]
        ),

        # ---------- PREPROCESS FRONT ----------
        Node(
            package='camera_preprocess',
            executable='preprocess_node',
            name='preprocess_front',
            parameters=[{
                'image_topic': '/camera/front/image_raw',
                'output_topic': '/camera/front/image_processed'
            }]
        ),

        # ---------- PREPROCESS DOWN ----------
        Node(
            package='camera_preprocess',
            executable='preprocess_node',
            name='preprocess_down',
            parameters=[{
                'image_topic': '/camera/down/image_raw',
                'output_topic': '/camera/down/image_processed'
            }]
        ),

        # ---------- ARUCO (FRONT CAMERA) ----------
        Node(
            package='aruco_scan',
            executable='aruco_node',
            name='aruco_front',
            parameters=[{
                'image_topic': '/camera/down/image_processed'
            }]
        ),

    ])
