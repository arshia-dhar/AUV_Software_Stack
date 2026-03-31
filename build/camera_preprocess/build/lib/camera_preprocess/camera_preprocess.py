import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2


class CameraPreprocess(Node):
    def __init__(self):
        super().__init__('camera_preprocess')

        self.bridge = CvBridge()

        # -------- PARAMETERS -------- #
        self.declare_parameter("input_topic", "/camera/image_raw")
        self.declare_parameter("output_topic", "/camera/image_processed")

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value

        # -------- SUBSCRIBE -------- #
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.callback,
            10
        )

        # -------- PUBLISH -------- #
        self.publisher = self.create_publisher(
            Image,
            output_topic,
            10
        )

        self.get_logger().info(f"Subscribed to: {input_topic}")
        self.get_logger().info(f"Publishing to: {output_topic}")

    def callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # ---- PREPROCESSING ---- #

        frame = cv2.resize(frame, (640, 480))

        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        lab = cv2.merge((l, a, b))
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        frame = cv2.GaussianBlur(frame, (5, 5), 0)

        # ------------------------ #

        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.publisher.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraPreprocess()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
