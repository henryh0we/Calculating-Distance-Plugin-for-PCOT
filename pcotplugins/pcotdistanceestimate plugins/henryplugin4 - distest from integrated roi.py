import os
import cv2 as cv
import numpy as np
from pcot.ui.canvas import Canvas
from pcot.ui.tabs import Tab
from pcot.utils.table import Table
from pcot.value import Value
from pcot.sources import nullSourceSet
from PySide2.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QScrollArea, QSplitter, QWidget, QPushButton, QFileDialog, QTextEdit
from PySide2.QtCore import Qt
import json

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

# camera_height = 1.094


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
        # self.focal_length = 2172.176065052148
        # self.focal_length = 1904.422603226366 # diag = 9.125mm USE THIS ONE
        # self.focal_length = 1930.872917160066 # diag = 9mm
        # self.baseline = 0.5

        # LOAD DATA FROM FILE
        file_data_path = 'pcotplugins/pcotdistanceestimate plugins/focal_baseline_height.json'
        self.focal_length = None
        self.baseline = None
        self.camera_height = None

        self.load_json(file_data_path)

        self.all_distances = []
        # self.all_distances_table = None
        self.all_distances_table = Table()

        print(f"Initialized all_distances: {self.all_distances}")
        print(f"Initialized all_distances_table: {self.all_distances_table}")

        self.addInputConnector("left", Datum.IMG)
        self.addInputConnector("right", Datum.IMG)

        self.addOutputConnector("distance", Datum.DATA)

        self.params = TaggedDictType(
            left_img_rois =('Left Image ROIs', list, []),
            right_img_rois =('Right Image ROIs', list, [])
        )

    def load_json(self, file_path):
        """
        Loads the camera data from a file at the given path, and then uses that data to set the focal length, baseline, and camera height of the object.

        Args:
            file_path (str): The path to the file to load from.

        Returns:
            None
        """
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.focal_length = data['focal_length']
                self.baseline = data['baseline']
                self.camera_height = data['camera_height']


    def createTab(self, n, w):
        print(f"Creating tab for node of type: {type(n)}")
        print(f"Node attributes: {dir(n)}")

        return TabDistEstimateRoi(n, w)
    
    def init(self, n):
        # No initialisation required.
        pass

    def perform(self, node):        
        self.all_distances = []
        self.all_distances_table = Table()

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

            crow = self.get_crow(distance)

            storage = self.store_distance_and_rois(distance, crow, left_roi, right_roi)

            self.all_distances.append(storage)
            # region
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
            # endregion

        self.populate_table()

        node.all_distances = self.all_distances
        node.all_distances_table = self.all_distances_table
        node.left_rectified = left_img_datum.get(Datum.IMG)
        node.right_rectified = right_img_datum.get(Datum.IMG)
        node.left_img_datum = left_img_datum
        node.right_img_datum = right_img_datum

        print("Computed distances:", self.all_distances)
        
        if self.all_distances_table:
            node.setOutput(0, Datum(Datum.DATA, str(self.all_distances_table), nullSourceSet))
        else:
            node.setOutput(0, Datum(Datum.DATA, Value(float('nan')), nullSourceSet))

        if node.tabs is not None:
            for tab in node.tabs:
                tab.onNodeChanged()

    def get_crow(self, distance):
        height = self.camera_height
        return (distance**2 - height**2)**0.5
        
    def extract_roi_points(self, roi):
        """Extracts the points from the ROI. Functionally irrelevant now, after 
        switching to useing MultiDot (all ROIs should be ROICircle)

        Args:
            roi (_type_): region of interest

        Returns:
            list: list containing tuple of x and y coordinates
        """
        if isinstance(roi, ROIPoly):
            return roi.points  # List of (x, y) tuples
        elif isinstance(roi, ROIRect):
            return [(roi.x, roi.y), (roi.x + roi.w, roi.y + roi.h)]
        elif isinstance(roi, ROICircle):
            return [(roi.x, roi.y)]  # Center and radius are also attributes
        elif isinstance(roi, ROIPainted):
            return [roi.centroid()]
        else:
            return []

    def estimate_distance(self, left_x, right_x):
        """Estimates the depth of a point given its x coordinates in the left and right images.

        Parameters:
        left_x (float): The x coordinate of the point in the left image.
        right_x (float): The x coordinate of the point in the right image.

        Returns:
        float: The estimated depth of the point.

        Raises:
        ValueError: If the disparity is zero.
        """
        disparity = right_x - left_x

        if disparity == 0:
            raise ValueError("Disparity cannot be zero")
        
        disparity = abs(disparity) #  Always non-negative

        print("SELF FLENGTH", self.focal_length)
        print("SELF BASELINE", self.baseline)

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


    def store_distance_and_rois(self, distance, crow, left_roi, right_roi):
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
            "right_roi": right_roi.to_tagged_dict(),
            "crow": crow
        }
        return storage

    def populate_table(self):        
        """
        Populate the table with the stored distances and ROIs.
        
        Iterates through the stored distances and ROIs, and populates a table with the
        results. The table is sorted by the label of the right ROI.
        """
    
        table = Table()
        for data in self.all_distances:
            # left_label = data['left_roi']['label']
            label = data['right_roi']['label']
            distance = data['distance']
            crow = data['crow']

            table.newRow(label)
            table.add('Label', label)
            table.add('Distance', distance)
            table.add('Crow', crow)

            print(f"Label: {label}, Distance: {distance}, Crow: {crow}")

        self.all_distances_table = table
    
class UnlabeledROIException(Exception):
    pass

class TabDistEstimateRoi(Tab):
    def __init__(self, node, w):
        super().__init__(w, node)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)  # Set the orientation to vertical
        
        self.layout = QVBoxLayout(self.w)
        self.layout.addWidget(self.splitter)
        
        self.canvas_widget = QWidget()
        self.canvas_layout = QHBoxLayout(self.canvas_widget)

        self.left_canvas = Canvas(self)
        self.right_canvas = Canvas(self)

        self.left_canvas.setGraph(node.graph)
        self.right_canvas.setGraph(node.graph)

        self.canvas_layout.addWidget(self.left_canvas)
        self.canvas_layout.addWidget(self.right_canvas)

        self.splitter.addWidget(self.canvas_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.table_widget = QTableWidget()      

        self.scroll_area.setWidget(self.table_widget)
        self.splitter.addWidget(self.scroll_area)

        self.load_buttons()

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        self.table = None

        self.nodeChanged()

    def load_buttons(self):
        self.button_layout = QHBoxLayout()

        # ===== DUMP DATA TO TXT ========
        self.dump_button = QPushButton("Dump Data to TXT")
        self.dump_button.clicked.connect(self.dump_data_to_txt)
        self.button_layout.addWidget(self.dump_button)
        # ================================================

        # ===== DUMP DATA TO CSV ========
        self.csv_button = QPushButton("Dump Data to CSV")
        self.csv_button.clicked.connect(self.dump_data_to_csv)
        self.button_layout.addWidget(self.csv_button)
        # ================================================

        # ===== DUMP DATA TO HTML ========
        self.html_button = QPushButton("Dump Data to HTML")
        self.html_button.clicked.connect(self.dump_data_to_html)
        self.button_layout.addWidget(self.html_button)
        # ================================================

        self.layout.addLayout(self.button_layout)

    def onNodeChanged(self):
        node = self.node
        print(f"Node type: {type(node)}")
        print(f"Node attributes before access: {dir(node)}")

        print(f"Table before update: {node.all_distances_table}") 
        self.update_tab_table(node.all_distances_table)


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

        if self.node.left_img_datum is None:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))
            self.left_canvas.setImg(None)
            return
        if self.node.right_img_datum is None:
            node.setOutput(0, Datum(Datum.NUMBER, Value(float('nan')), nullSourceSet))
            self.right_canvas.setImg(None)
            return

    def update_tab_table(self, distance_table):
        self.table_widget.clear()

        row_count = distance_table.__len__()

        self.table_widget.setRowCount(row_count)
        print(f"Row count: {row_count}")

        headers = distance_table.keys()
        print(f"Headers: {headers}")

        # print(distance_table.__str__())

        self.table_widget.setColumnCount(len(headers))

        self.table_widget.setHorizontalHeaderLabels(headers)

        print(f"Headers: {headers}")
        print(f"Distance table: {distance_table}")

        for row_index, data in enumerate(distance_table):
            print(f"Row {row_index}: {data}")
            for col_index, header in enumerate(headers):
                # header = int(header)
                print(f"Setting item ({row_index}, {col_index}) to {data[col_index]}")
                self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(data[col_index])))

        self.table_widget.resizeColumnsToContents()

    def dump_data_to_txt(self):
        if self.node.all_distances_table is None:
            print("No data to dump TXT")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "distances.txt", "Text Files (*.txt)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                headers = self.node.all_distances_table.keys()
                f.write(", ".join(f'{header}' for header in headers) + "\n")
                for row in self.node.all_distances_table:
                    f.write(", ".join(f'{header}: {row[i]}' for i, header in enumerate(headers)) + "\n")

            print(f"Data dumped to {file_name}")

    def dump_data_to_csv(self):
        if self.node.all_distances_table is None:
            print("No data to dump CSV")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "distances.csv", "CSV Files (*.csv)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                # Write the header
                headers = self.node.all_distances_table.keys()
                for header in headers:
                    f.write(f"{header},")
                f.write("\n")

                for row in self.node.all_distances_table:
                    f.write(",".join(map(str, row)) + "\n")

            print(f"Data dumped to {file_name}")

    def dump_data_to_html(self):
        if self.node.all_distances_table is None:
            print("No data to dump HTML")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "distances.html", "HTML Files (*.html)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                f.write(self.node.all_distances_table.html())
            print(f"Data dumped to {file_name}")