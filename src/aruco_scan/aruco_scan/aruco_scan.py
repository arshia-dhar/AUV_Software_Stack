import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np


class ArucoScanner(Node):
    def __init__(self):
        super().__init__('aruco_scanner')

        self.bridge = CvBridge()

        # -------- PARAMETERS -------- #
        self.declare_parameter("image_topic", "/camera/image_processed")
        image_topic = self.get_parameter("image_topic").value

        # -------- SUBSCRIBE -------- #
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )

        # -------- PUBLISH -------- #
        self.publisher = self.create_publisher(
            Image,
            '/aruco/image',
            10
        )

        # -------- ARUCO SETUP -------- #
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_50
        )

        self.parameters = cv2.aruco.DetectorParameters_create()

        self.get_logger().info(f"Subscribed to: {image_topic}")
        self.get_logger().info("Aruco Scanner Node Started")

    def image_callback(self, msg):
        # Convert ROS → OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # -------- DETECTION -------- #
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray,
            self.aruco_dict,
            parameters=self.parameters
        )

        # -------- DRAW + LOG -------- #
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            for i, marker_id in enumerate(ids):
                self.get_logger().info(
                    f"Detected ID: {marker_id[0]}",
                    throttle_duration_sec=1.0
                )

                # Center
                c = corners[i][0]
                center_x = int(np.mean(c[:, 0]))
                center_y = int(np.mean(c[:, 1]))

                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

        # -------- PUBLISH -------- #
        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.publisher.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoScanner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
