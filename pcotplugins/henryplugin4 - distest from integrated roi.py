import cv2 as cv
import numpy as np
from pcot.ui.canvas import Canvas
from pcot.ui.tabs import Tab
from pcot.value import Value
from pcot.sources import nullSourceSet
from PySide2.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout

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
    This version takes in multiple rois and then returns 
    the distance for all of them.
    The distances are all displayed in a table

    Author: Henry Howe
    Date:2025-04-22
    """

    def __init__(self):
        
        super().__init__("distestimateROI", "processing", "0.0.0")

        # HARDCODED DATA
        self.focal_length = 2172.176065052148
        self.baseline = 0.5

        self.all_distances = []

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
        
        self.all_distances = []

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

        left_rois_sorted = self.extract_and_check_rois(left_img_datum)
        right_rois_sorted = self.extract_and_check_rois(right_img_datum)

        print("Sorted ROIs")
        print(left_rois_sorted)
        print(right_rois_sorted)

        # all_distances = []

        for label in sorted(left_rois_sorted.keys() & right_rois_sorted.keys()):
            print("Processing label:", label)
            left_rois_match = left_rois_sorted[label]
            right_rois_match = right_rois_sorted[label]

            print("Left ROIs Match:", left_rois_match)
            print("Right ROIs Match:", right_rois_match)

            left_coord = self.extract_roi_points(left_rois_match[0])
            right_coord = self.extract_roi_points(right_rois_match[0])

            print("Left Coordinates:", left_coord)
            print("Right Coordinates:", right_coord)

            left_x = left_coord[0][0]
            right_x = right_coord[0][0]

            distance = self.estimate_distance(left_x, right_x)
            print("Estimated Distance:", distance)

            left_roi = left_rois_match[0]
            right_roi = right_rois_match[0]
            storage = self.store_distance_and_rois(distance, left_roi, right_roi)

            self.all_distances.append(storage)
            # left_rois_match = left_rois_sorted[label]
            # right_rois_match = right_rois_sorted[label]

            # left_coord = self.extract_roi_points(left_rois_match[0])
            # right_coord = self.extract_roi_points(right_rois_match[0])

            # left_x = left_coord[0][0]
            # right_x = right_coord[0][0]

            # distance = self.estimate_distance(left_x, right_x) 

            # storage = self.store_distance_and_rois(distance, left_rois_match[0], right_rois_match[0])

            # print(storage)

            # all_distances.append(storage)

        node.all_distances = self.all_distances
        node.left_rectified = left_img_datum.get(Datum.IMG)
        node.right_rectified = right_img_datum.get(Datum.IMG)

        print("Computed distances:", self.all_distances)
        

        if self.all_distances:
            node.setOutput(0, Datum(Datum.NUMBER, Value(self.all_distances[0]['distance']), nullSourceSet))
        else:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))


        if node.tabs is not None:
            for tab in node.tabs:
                tab.onNodeChanged()

        # left_coords = []
        # right_coords = []

        # for roi in left_img_rois:
        #     left_coords.extend(self.extract_roi_points(roi))
        # for roi2 in right_img_rois:
        #     right_coords.extend(self.extract_roi_points(roi2))
        # # if len(left_coords) > 0 and len(right_coords) > 0:
        # #     distance = self.estimate_distance(left_coords[0], right_coords[0])
        
        # if not left_coords or not right_coords:
        #     print("Error: No coordinates extracted from ROIs")
        #     node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
        #     return

        # distance = 10
        # try:
        #     distance = self.estimate_distance(left_coords[0][0], right_coords[0][0])
        # except Exception as e:
        #     print(f"Error in estimate_distance calculation: {e}")
        #     node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))  
        #     return
        
        # # camera_height = 1.094

        # try:
        #     crow_distance = (distance**2 - camera_height**2)**0.5
        # except Exception as e:
        #     print(f"Error in crow distance calculation: {e}")

        # distance_datum = Datum(Datum.NUMBER, Value(distance), nullSourceSet)
        # crow_datum = Datum(Datum.NUMBER, Value(crow_distance), nullSourceSet)

        # node.setOutput(0, distance_datum)
        # node.setOutput(1, crow_datum)

        # if node.tab is not None:
        #     node.tab.update()

    # def getDistanceList(self):
    #     print("Getting distance list")
    #     all_distances = getattr(self, 'all_distances', [])
    #     print(f"Returning {len(distances)} distances")
    #     return distances

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

    def extract_and_check_rois(self, datum):
        """
        Extract ROIs from a Datum object and ensure they are labeled if there are multiple ROIs.

        Parameters:
        datum (Datum): The Datum object to check.

        Returns:
        dict: A dictionary of ROIs keyed by their labels, sorted by label.

        Raises:
        UnlabeledROIException: If multiple ROIs are present and any ROI is unlabeled.
        """
        print(f"Checking datum of type {datum.tp} for ROIs")
        if datum.tp in (Datum.ROI, Datum.IMG, Datum.VARIANT, Datum.ANY):
            rois = None
            if datum.tp == Datum.IMG:
                rois = datum.val.rois if datum.val else None
            elif datum.tp == Datum.ROI:
                rois = [datum.val]
            elif datum.tp in (Datum.VARIANT, Datum.ANY):
                if hasattr(datum.val, 'rois'):
                    rois = datum.val.rois
                elif isinstance(datum.val, list):
                    rois = datum.val

            if rois:
                print(f"Found {len(rois)} ROIs")
                roi_dict = {}
                for roi in rois:
                    print(f"Checking ROI {roi.label if roi.label else 'with no label'}")
                    if not roi.label:
                        if len(rois) > 1:
                            raise UnlabeledROIException("Multiple ROIs must be labeled.")
                    else:
                        if roi.label not in roi_dict:
                            roi_dict[roi.label] = []
                        roi_dict[roi.label].append(roi)
                
                # Sorting ROIs by label
                sorted_rois = {label: roi_dict[label] for label in sorted(roi_dict)}
                print(f"Returning {len(sorted_rois)} labeled ROIs")
                return sorted_rois

        print("No ROIs found")
        return {}

    def store_distance_and_rois(self, distance, left_roi, right_roi):
        """
        Stores the distance and the two ROIs in a dictionary.
        
        Parameters:
        distance (float): The calculated distance.
        left_roi (ROI): The ROI from the left image.
        right_roi (ROI): The ROI from the right image.
        
        Returns:
        dict: A dictionary containing the distance and the ROIs.
        """
        storage = {
            "distance": distance,
            "left_roi": left_roi.to_tagged_dict(),
            "right_roi": right_roi.to_tagged_dict()
        }
        return storage
    

class UnlabeledROIException(Exception):
    pass

# class TabDistanceTable(Tab):
#     def __init__(self, node, w):

class TabDistEstimateRoi(Tab):
    def __init__(self, node, w):
        super().__init__(w, node)

        # self.layout = QVBoxLayout(self.w)
        self.layout = QHBoxLayout(self.w)
        self.canvas_layout = QVBoxLayout(self.w)

        self.left_canvas = Canvas(self)
        self.right_canvas = Canvas(self)

        self.left_canvas.setGraph(node.graph)
        self.right_canvas.setGraph(node.graph)

        self.canvas_layout.addWidget(self.left_canvas)
        self.canvas_layout.addWidget(self.right_canvas)

        self.layout.addLayout(self.canvas_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Left ROI Label", "Right ROI Label", "Distance"])
    
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 250)        
        
        self.layout.addWidget(self.table)
        
        self.nodeChanged()

    def onNodeChanged(self):
        node = self.node
        distance_list = node.all_distances
        # distance_list = node.type.getDistanceList()  # Assume this method returns the all_distances list
        print(distance_list)
        self.populate_table(distance_list)

        if hasattr(node, 'left_rectified') and node.left_rectified is not None:
            print("Left rectified image is available")
            # left_img_cube = ImageCube(node.left_rectified)
            left_img_cube = node.left_rectified

            self.left_canvas.display(left_img_cube)
        else:
            print("Left rectified image is not available")

        if hasattr(node, 'right_rectified') and node.right_rectified is not None:
            print("Right rectified image is available")
            # right_img_cube = ImageCube(node.right_rectified)
            right_img_cube = node.right_rectified
            self.right_canvas.display(right_img_cube)
        else:
            print("Right rectified image is not available")

    def populate_table(self, distance_list):
        print(f"Populating table with {len(distance_list)} entries")
        self.table.setRowCount(len(distance_list))
        for row_index, data in enumerate(distance_list):
            left_label = data['left_roi']['label']
            right_label = data['right_roi']['label']
            distance = data['distance']

            print(f"Row {row_index}: Left label: {left_label}, Right label: {right_label}, Distance: {distance}")

            self.table.setItem(row_index, 0, QTableWidgetItem(left_label))
            self.table.setItem(row_index, 1, QTableWidgetItem(right_label))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(distance)))



# class TabDistEstimateRoi(Tab):
#     def __init__(self, node, w):
#         super().__init__(w, node)
#         # self.layout = QGridLayout(self.w)
#         self.layout = QVBoxLayout(self.w)

#         self.distance_label = QLabel("Distance: N/A")
#         # self.layout.addWidget(self.distance_label, 0, 0)
#         self.layout.addWidget(self.distance_label)

#         self.crow_label = QLabel("Crow Distance: N/A")
#         self.layout.addWidget(self.crow_label)

#         self.height_label = QLabel("Height: N/A")
#         self.layout.addWidget(self.height_label)

#         self.nodeChanged()

#     def onNodeChanged(self):
#         distance_datum = self.node.getOutput(0)
#         crow_datum = self.node.getOutput(1)

        
#         # Debugging information
#         print(f"distance_datum: {distance_datum}")
#         if distance_datum is not None:
#             print(f"type of distance_datum: {type(distance_datum)}")
#             self.distance_label.setText(f"Distance: {distance_datum}")
#         else:
#             self.distance_label.setText("Distance: N/A")
        
#         if crow_datum is not None:
#             print(f"type of crow_datum: {type(crow_datum)}")
#             self.crow_label.setText(f"Crow Distance: {crow_datum}")
#         else:
#             self.crow_label.setText("Crow Distance: N/A")

#         self.height_label.setText(f"Height: {camera_height}")

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
