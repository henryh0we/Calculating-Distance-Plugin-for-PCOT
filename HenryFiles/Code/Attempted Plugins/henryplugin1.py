import cv2 as cv 
import numpy as np
import os
import json

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

class XFormDistEstimate(XFormType):
    """
    A node designed to estimate the distance to a given object
    that is selected in two images using stereographic principles.

    Author: Henry Howe
    Date: 2025-04-17

    """

    def __init__(self):
        super().__init__("distestimate", "processing", "0.0.0")
        self.addInputConnector("Left Image", Datum.IMG)
        self.addInputConnector("Right Image", Datum.IMG)
        self.addOutputConnector("Distance", Datum.FLOAT)

        # Initialize camera parameters
        self.mtx_left = None
        self.dist_left = None
        self.rect_left = None
        self.proj_left = None
        self.mtx_right = None
        self.dist_right = None
        self.rect_right = None
        self.proj_right = None

        # Load JSON data
        self.load_json()

    def createTab(self, n, w):
        return TabData(n, w)

    def init(self, n):
        # No initialisation required.
        pass

    def perform(self, node):
        left_img = node.getInput("Left Image", Datum.IMG)
        right_img = node.getInput("Right Image", Datum.IMG)

        if left_img is not None and right_img is not None:
            # Perform the distance estimation
            distance = self.estimate_distance(left_img, right_img)

            # Set the output value
            node.out = Datum(Datum.FLOAT, distance)
        else:
            node.out = Datum.null

        node.setOutput("Distance", node.out)

    def estimate_distance(self, left_img, right_img):
        pass

    def load_json(self, data):
        camera_data_file_path = 'HenryFiles/camera_data.json'

        if os.path.exists(camera_data_file_path):

            with open(camera_data_file_path, 'r') as file:
                data = json.load(file)

            self.mtx_left = np.array(data['mtx_left'])
            self.dist_left = np.array(data['dist_left']).reshape(-1,1)
            self.rect_left = np.array(data['rect_left'])
            self.proj_left = np.array(data['proj_left'])

            self.mtx_right = np.array(data['mtx_right'])
            self.dist_right = np.array(data['dist_right']).reshape(-1,1)
            self.rect_right = np.array(data['rect_right'])
            self.proj_right = np.array(data['proj_right'])

    def draw_lines(self, image, lines, color=(0, 0, 255), thickness=1):
        num_lines = 40
        interval = image.shape[0] // num_lines

        for i in range(0, image.shape[0], interval):
            cv.line(image, (0, i), (image.shape[1], i), color, thickness)

        return image