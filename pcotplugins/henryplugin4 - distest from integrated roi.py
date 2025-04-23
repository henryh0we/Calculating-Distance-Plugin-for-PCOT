import cv2 as cv
import numpy as np
from pcot.ui.tabs import Tab
from pcot.value import Value
from pcot.sources import nullSourceSet
from PySide2.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from pcot.parameters.taggedaggregates import TaggedDictType
from pcot.rois import ROICircle, ROIPainted, ROIPoly, ROIRect
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

camera_height = 1.094


@xformtype
class XFormDistEstimateRoi(XFormType):
    """
    A node designed to take the points selected in two rectified images 
    and then calculate the distance to said point
    This version should take the integrated ROIs which are stored within the 
    IMG Datum.

    Author: Henry Howe
    Date:2025-04-22
    """

    def __init__(self):
        
        super().__init__("distestimateROI", "processing", "0.0.0")

        # HARDCODED DATA
        self.focal_length = 2172.176065052148
        self.baseline = 0.5

        self.addInputConnector("left", Datum.IMG)
        self.addInputConnector("right", Datum.IMG)

        self.addOutputConnector("distance", Datum.NUMBER)
        self.addOutputConnector("crow", Datum.NUMBER)

        self.params = TaggedDictType(
            left_img_rois =('Left Image ROIs', list, []),
            right_img_rois =('Right Image ROIs', list, [])
        )


    def createTab(self, n, w):
        return TabDistEstimateRoi(n, w)
    
    def init(self, n):
        # No initialisation required.
        pass

    def perform(self, node):
        left_img_datum = node.getInput(0)  
        right_img_datum = node.getInput(1)  

        if left_img_datum is None or right_img_datum is None:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
            return

        left_img_cube = left_img_datum.get(Datum.IMG)
        right_img_cube = right_img_datum.get(Datum.IMG)

        if left_img_cube is None or right_img_cube is None:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
            return

        left_img_rois = left_img_cube.rois
        right_img_rois = right_img_cube.rois

        if left_img_rois is None or right_img_rois is None:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
            return

        print(left_img_rois)
        print(right_img_rois)

        left_coords = []
        right_coords = []

        for roi in left_img_rois:
            left_coords.extend(self.extract_roi_points(roi))
        for roi2 in right_img_rois:
            right_coords.extend(self.extract_roi_points(roi2))
        # if len(left_coords) > 0 and len(right_coords) > 0:
        #     distance = self.estimate_distance(left_coords[0], right_coords[0])
        
        if not left_coords or not right_coords:
            print("Error: No coordinates extracted from ROIs")
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
            return

        # distance = 10
        try:
            distance = self.estimate_distance(left_coords[0][0], right_coords[0][0])
        except Exception as e:
            print(f"Error in estimate_distance calculation: {e}")
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
            return
        
        # camera_height = 1.094

        try:
            crow_distance = (distance**2 - camera_height**2)**0.5
        except Exception as e:
            print(f"Error in crow distance calculation: {e}")

        distance_datum = Datum(Datum.NUMBER, Value(distance), nullSourceSet)
        crow_datum = Datum(Datum.NUMBER, Value(crow_distance), nullSourceSet)

        node.setOutput(0, distance_datum)
        node.setOutput(1, crow_datum)

        # if node.tab is not None:
        #     node.tab.update()

    def extract_roi_points(self, roi):
        if isinstance(roi, ROIPoly):
            return roi.points  # List of (x, y) tuples
        elif isinstance(roi, ROIRect):
            return [(roi.x, roi.y), (roi.x + roi.w, roi.y + roi.h)]
        elif isinstance(roi, ROICircle):
            return [(roi.x, roi.y)]  # Center and radius are also attributes
        elif isinstance(roi, ROIPainted):
            # mask_points = np.column_stack(np.where(roi.mask))  # Assuming roi.mask is a 2D numpy array
            # return [(int(x), int(y)) for y, x in mask_points]  # Convert to list of (x, y) tuples
            return [roi.centroid()]
        else:
            return []

    def estimate_distance(self, left_x, right_x):
        # left_x = left_coords[0]
        # right_x = right_coords[0]

        disparity = right_x - left_x

        if disparity == 0:
            raise ValueError("Disparity cannot be zero")
        
        disparity = abs(disparity) #  Always non-negative

        depth = self.focal_length * self.baseline / disparity

        return depth

class TabDistEstimateRoi(Tab):
    def __init__(self, node, w):
        super().__init__(w, node)
        # self.layout = QGridLayout(self.w)
        self.layout = QVBoxLayout(self.w)

        self.distance_label = QLabel("Distance: N/A")
        # self.layout.addWidget(self.distance_label, 0, 0)
        self.layout.addWidget(self.distance_label)

        self.crow_label = QLabel("Crow Distance: N/A")
        self.layout.addWidget(self.crow_label)

        self.height_label = QLabel("Height: N/A")
        self.layout.addWidget(self.height_label)

        self.nodeChanged()

    def onNodeChanged(self):
        distance_datum = self.node.getOutput(0)
        crow_datum = self.node.getOutput(1)

        
        # Debugging information
        print(f"distance_datum: {distance_datum}")
        if distance_datum is not None:
            print(f"type of distance_datum: {type(distance_datum)}")
            self.distance_label.setText(f"Distance: {distance_datum}")
        else:
            self.distance_label.setText("Distance: N/A")
        
        if crow_datum is not None:
            print(f"type of crow_datum: {type(crow_datum)}")
            self.crow_label.setText(f"Crow Distance: {crow_datum}")
        else:
            self.crow_label.setText("Crow Distance: N/A")

        self.height_label.setText(f"Height: {camera_height}")

# class DistEstimateRoiTab(QWidget):
#     def __init__(self, node, window):
#         super().__init__()
#         self.node = node
#         self.window = window
#         self.layout = QVBoxLayout()
#         self.distance_label = QLabel("Distance: N/A")
#         self.layout.addWidget(self.distance_label)
#         self.setLayout(self.layout)
#         self.update()

#     def update(self):
#         distance_datum = self.node.getOutput(0)
#         if distance_datum is not None and distance_datum.val is not None:
#             self.distance_label.setText(f"Distance: {distance_datum.val.val}")
#         else:
#             self.distance_label.setText("Distance: N/A")
