import cv2 as cv
import json
import os

import numpy as np
from PySide2.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout

from pcot.datum import Datum
from pcot.imagecube import ImageCube
from pcot.ui.canvas import Canvas
from pcot.ui.tabs import Tab
from pcot.xform import XFormType, xformtype


REQUIRED_CALIBRATION_KEYS = (
    "mtx_left",
    "dist_left",
    "rect_left",
    "proj_left",
    "mtx_right",
    "dist_right",
    "rect_right",
    "proj_right",
)

CALIBRATION_MATRIX_SHAPES = {
    "mtx_left": (3, 3),
    "rect_left": (3, 3),
    "proj_left": (3, 4),
    "mtx_right": (3, 3),
    "rect_right": (3, 3),
    "proj_right": (3, 4),
}


@xformtype
class XFormImageRectify(XFormType):
    """
    A node designed to rectify an image pair

    Author: Henry Howe
    Date: 2025-04-19

    """

    def __init__(self):

        super().__init__("rectify", "processing", "0.0.0")

        # Initialize camera parameters - dont think this is needed atm
        self.mtx_left = None
        self.dist_left = None
        self.rect_left = None
        self.proj_left = None
        self.mtx_right = None
        self.dist_right = None
        self.rect_right = None
        self.proj_right = None
        self.calibration_error = None

        # Load JSON data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'mtx_dst_rect_proj.json')
        self.load_json(file_path)

        self.addInputConnector("Left Image", Datum.IMG)
        self.addInputConnector("Right Image", Datum.IMG)

        self.addOutputConnector("Left Output", Datum.IMG)
        self.addOutputConnector("Right Output", Datum.IMG)

    def createTab(self, n, w):
        return TabImageRectify(n, w)

    def init(self, n):
        n.left_rectified_cube = None
        n.right_rectified_cube = None
        n.status_message = ""
        n._rectify_map_cache = {}

    def clear_node_outputs(self, node, message):
        node.left_rectified_cube = None
        node.right_rectified_cube = None
        node.status_message = message
        node.setOutput(0, Datum(Datum.IMG, None))
        node.setOutput(1, Datum(Datum.IMG, None))

    def perform(self, node):
        if self.calibration_error is not None:
            self.clear_node_outputs(node, self.calibration_error)
            return

        left_img_cube = node.getInput(0, Datum.IMG)
        right_img_cube = node.getInput(1, Datum.IMG)

        if left_img_cube is None or right_img_cube is None:
            self.clear_node_outputs(node, "Left and right image inputs are required.")
            return

        left_img = left_img_cube.img
        right_img = right_img_cube.img

        if not isinstance(left_img, np.ndarray) or not isinstance(right_img, np.ndarray):
            self.clear_node_outputs(node, "Left and right inputs must both contain image arrays.")
            return

        if left_img.ndim not in (2, 3) or right_img.ndim not in (2, 3):
            self.clear_node_outputs(node, "Left and right image arrays must be 2D or 3D.")
            return

        left_size = (left_img.shape[1], left_img.shape[0])
        right_size = (right_img.shape[1], right_img.shape[0])

        try:
            map_left_x, map_left_y = cv.initUndistortRectifyMap(
                self.mtx_left,
                self.dist_left,
                self.rect_left,
                self.proj_left,
                left_size,
                cv.CV_32FC1)
            map_right_x, map_right_y = cv.initUndistortRectifyMap(
                self.mtx_right,
                self.dist_right,
                self.rect_right,
                self.proj_right,
                right_size,
                cv.CV_32FC1
            )

            left_rectified = cv.remap(left_img, map_left_x, map_left_y, cv.INTER_LINEAR)
            right_rectified = cv.remap(right_img, map_right_x, map_right_y, cv.INTER_LINEAR)
        except cv.error as ex:
            self.clear_node_outputs(node, f"Rectification failed: {ex}")
            return
        except ValueError as ex:
            self.clear_node_outputs(node, f"Rectification failed: {ex}")
            return

        # Wrap numpy arrays into ImageCube objects
        left_rectified_cube = ImageCube(left_rectified)
        right_rectified_cube = ImageCube(right_rectified)

        # Store the rectified images in the node for tab access
        node.left_rectified_cube = left_rectified_cube
        node.right_rectified_cube = right_rectified_cube
        node.status_message = "Images rectified."

        # Create Datum objects for the outputs
        left_rectified_datum = Datum(Datum.IMG, left_rectified_cube)
        right_rectified_datum = Datum(Datum.IMG, right_rectified_cube)

        # Set the output connectors
        node.setOutput(0, left_rectified_datum)
        node.setOutput(1, right_rectified_datum)

    def load_json(self, file_path):
        self.clear_calibration()

        if not os.path.exists(file_path):
            self.calibration_error = f"Calibration file not found: {file_path}"
            return

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as ex:
            self.calibration_error = f"Unable to load calibration file: {ex}"
            return

        try:
            calibration = self.parse_calibration(data)
        except ValueError as ex:
            self.calibration_error = f"Invalid calibration file: {ex}"
            return

        self.mtx_left = calibration["mtx_left"]
        self.dist_left = calibration["dist_left"]
        self.rect_left = calibration["rect_left"]
        self.proj_left = calibration["proj_left"]
        self.mtx_right = calibration["mtx_right"]
        self.dist_right = calibration["dist_right"]
        self.rect_right = calibration["rect_right"]
        self.proj_right = calibration["proj_right"]
        self.calibration_error = None

    def clear_calibration(self):
        self.mtx_left = None
        self.dist_left = None
        self.rect_left = None
        self.proj_left = None
        self.mtx_right = None
        self.dist_right = None
        self.rect_right = None
        self.proj_right = None

    def parse_calibration(self, data):
        missing_keys = [key for key in REQUIRED_CALIBRATION_KEYS if key not in data]
        if missing_keys:
            raise ValueError(f"missing keys: {', '.join(missing_keys)}")

        calibration = {}
        for key, expected_shape in CALIBRATION_MATRIX_SHAPES.items():
            calibration[key] = self.parse_matrix(data[key], key, expected_shape)

        calibration["dist_left"] = self.parse_distortion(data["dist_left"], "dist_left")
        calibration["dist_right"] = self.parse_distortion(data["dist_right"], "dist_right")
        return calibration

    def parse_matrix(self, value, key, expected_shape):
        matrix = np.array(value, dtype=np.float64)
        if matrix.shape != expected_shape:
            raise ValueError(f"{key} must have shape {expected_shape}, got {matrix.shape}")
        return matrix

    def parse_distortion(self, value, key):
        distortion = np.array(value, dtype=np.float64)
        if distortion.size == 0:
            raise ValueError(f"{key} must contain at least one coefficient")
        if distortion.ndim > 2 or (distortion.ndim == 2 and 1 not in distortion.shape):
            raise ValueError(f"{key} must be a 1D, row, or column vector, got {distortion.shape}")
        return distortion.reshape(-1, 1)


class TabImageRectify(Tab):
    def __init__(self, node, window):
        super().__init__(window, node)
        layout = QHBoxLayout(self.w)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.leftImageLabel = QLabel("Left Rectified Image")
        self.rightImageLabel = QLabel("Right Rectified Image")

        self.leftCanvas = Canvas(self)
        self.rightCanvas = Canvas(self)

        left_layout.addWidget(self.leftImageLabel)
        left_layout.addWidget(self.leftCanvas)
        right_layout.addWidget(self.rightImageLabel)
        right_layout.addWidget(self.rightCanvas)

        self.leftCanvas.setGraph(node.graph)
        self.rightCanvas.setGraph(node.graph)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.nodeChanged()

    def onNodeChanged(self):
        left_img_cube = getattr(self.node, 'left_rectified_cube', None)
        if left_img_cube is not None:
            self.leftCanvas.display(left_img_cube)
        else:
            self.leftCanvas.setImg(None)

        right_img_cube = getattr(self.node, 'right_rectified_cube', None)
        if right_img_cube is not None:
            self.rightCanvas.display(right_img_cube)
        else:
            self.rightCanvas.setImg(None)
