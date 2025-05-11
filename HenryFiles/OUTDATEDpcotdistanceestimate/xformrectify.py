# My imports
import cv2 as cv
import numpy as np
import os
import json
from PySide2.QtWidgets import QLabel, QVBoxLayout
from PySide2.QtGui import QPixmap
import pcot.utils.image
from PySide2.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout
from pcot.ui.tabs import Tab
from pcot.datum import Datum
from pcot.ui.canvas import Canvas

# Coppied from other pcot plugins
from pcot.sources import SourceSet
from pcot.xform import XFormType, xformtype
from pcot.xforms.tabdata import TabData
from pcot.imagecube import ImageCube
from pcot.datum import Datum
from pcot.value import Value
from pcot.datumtypes import Type
from PySide2.QtGui import QColor
from pcot.expressions.register import datumfunc


import pcot.config

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

        # Load JSON data
        file_path = 'pcotplugins/pcotdistanceestimate/mtx_dst_rect_proj.json'
        self.load_json(file_path)

        self.left_rectified = None
        self.right_rectified = None

        self.addInputConnector("Left Image", Datum.IMG)
        self.addInputConnector("Right Image", Datum.IMG)

        # self.addInputConnector("Image", Datum.IMG)
        
        self.addOutputConnector("Left Output", Datum.IMG)
        self.addOutputConnector("Right Output", Datum.IMG)

    def createTab(self, n, w):
        return TabImageRectify(n, w)

    def init(self, n):
        # No initialisation required.
        
        pass

    def perform(self, node):
        left_img_datum = node.getInput(0)  # Use index 0 for 'Left Image'
        right_img_datum = node.getInput(1)  # Use index 1 for 'Right Image'

        if left_img_datum is None or right_img_datum is None:
            node.setOutput(0, Datum(Datum.IMG, None))  # Use index 0 for 'Left Output'
            node.setOutput(1, Datum(Datum.IMG, None))  # Use index 1 for 'Right Output'
            return

        left_img_cube = left_img_datum.get(Datum.IMG)
        right_img_cube = right_img_datum.get(Datum.IMG)

        if left_img_cube is None or right_img_cube is None:
            node.setOutput(0, Datum(Datum.IMG, None))  # Use index 0 for 'Left Output'
            node.setOutput(1, Datum(Datum.IMG, None))  # Use index 1 for 'Right Output'
            return

        left_img = left_img_cube.img
        right_img = right_img_cube.img

        if not isinstance(left_img, np.ndarray) or not isinstance(right_img, np.ndarray):
            raise TypeError("Input images must be of type np.ndarray")

        map_left_x, map_left_y = cv.initUndistortRectifyMap(
            self.mtx_left, 
            self.dist_left, 
            self.rect_left, 
            self.proj_left, 
            left_img.shape[:2], 
            cv.CV_32FC1)
        map_right_x, map_right_y = cv.initUndistortRectifyMap(
            self.mtx_right, 
            self.dist_right, 
            self.rect_right, 
            self.proj_right, 
            right_img.shape[:2], 
            cv.CV_32FC1
        )

        left_rectified = cv.remap(left_img, map_left_x, map_left_y, cv.INTER_LINEAR)
        right_rectified = cv.remap(right_img, map_right_x, map_right_y, cv.INTER_LINEAR)

        # Store the rectified images in the node for tab access
        node.left_rectified = left_rectified
        node.right_rectified = right_rectified

        # Wrap numpy arrays into ImageCube objects
        left_rectified_cube = ImageCube(left_rectified)
        right_rectified_cube = ImageCube(right_rectified)

        # Create Datum objects for the outputs
        left_rectified_datum = Datum(Datum.IMG, left_rectified_cube)
        right_rectified_datum = Datum(Datum.IMG, right_rectified_cube)

        # Set the output connectors
        node.setOutput(0, left_rectified_datum)  # Use index 0 for 'Left Output'
        node.setOutput(1, right_rectified_datum)  # Use index 1 for 'Right Output'

    def load_json(self, file_path):

        if os.path.exists(file_path):

            with open(file_path, 'r') as file:
                data = json.load(file)

            self.mtx_left = np.array(data['mtx_left'])
            self.dist_left = np.array(data['dist_left']).reshape(-1,1)
            self.rect_left = np.array(data['rect_left'])
            self.proj_left = np.array(data['proj_left'])

            self.mtx_right = np.array(data['mtx_right'])
            self.dist_right = np.array(data['dist_right']).reshape(-1,1)
            self.rect_right = np.array(data['rect_right'])
            self.proj_right = np.array(data['proj_right'])

class TabImageRectify(Tab):
    def __init__(self, node, window):
        super().__init__(window, node)
        # layout = QVBoxLayout(self.w)
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
        if hasattr(self.node, 'left_rectified') and self.node.left_rectified is not None:
            left_img_cube = ImageCube(self.node.left_rectified)
            self.leftCanvas.display(left_img_cube)
            # self.leftCanvas.display(self.node.left_rectified)

        if hasattr(self.node, 'right_rectified') and self.node.right_rectified is not None:
            right_img_cube = ImageCube(self.node.right_rectified)
            self.rightCanvas.display(right_img_cube)
            #  self.rightCanvas.display(self.node.right_rectified)