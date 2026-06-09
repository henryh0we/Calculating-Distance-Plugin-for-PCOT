import math
import os
from pcot.ui.canvas import Canvas
from pcot.ui.tabs import Tab
from pcot.utils.table import Table
from pcot.sources import nullSourceSet
from PySide2.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QScrollArea, QSplitter, QWidget, QPushButton, QFileDialog
from PySide2.QtCore import Qt
import json

from pcot.parameters.taggedaggregates import TaggedDictType
from pcot.rois import ROICircle
from pcot.xform import XFormType, xformtype
from pcot.datum import Datum

# camera_height = 1.094


@xformtype
class XFormDistEstimateRoi(XFormType):
    """
    A node designed to take the points selected in two rectified images 
    and then calculate the distance to said point
    This version takes in multiple rois and then returns 
    the distance for all of them.
    The depths are all displayed in a table

    Author: Henry Howe
    Date:2025-04-22
    """

    MIN_DISPARITY_PX = 2.0
    MAX_VERTICAL_OFFSET_PX = 2.0
    MEDIUM_QUALITY_MAX_VERTICAL_OFFSET_PX = 1.0
    HIGH_QUALITY_MAX_VERTICAL_OFFSET_PX = 0.5
    HIGH_QUALITY_MIN_DISPARITY_PX = 20.0
    MEDIUM_QUALITY_MIN_DISPARITY_PX = 8.0
    PIXEL_ERROR_PX = 1.0
    HIGH_QUALITY_MAX_REL_UNCERTAINTY = 0.05
    MEDIUM_QUALITY_MAX_REL_UNCERTAINTY = 0.15
    CALIBRATION_FOCAL_TOLERANCE_RATIO = 0.01

    def __init__(self):
        
        super().__init__("distestimateROI", "processing", "0.0.0")

        # LOAD DATA FROM FILE
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_data_path = os.path.join(script_dir, 'focal_baseline_height.json')

        self.focal_length = None
        self.baseline = None
        self.camera_height = None
        self.rectified_focal_length = None

        self.load_json(file_data_path)
        self.load_rectification_json(os.path.join(script_dir, 'mtx_dst_rect_proj.json'))

        self.all_depths = []
        self.all_depths_table = Table()
        self.validation_issues = []

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
        return TabDistEstimateRoi(n, w)
    
    def init(self, n):
        self.initialise_node_state(n)

    def initialise_node_state(self, node):
        node.all_depths = []
        node.all_depths_table = Table()
        node.validation_issues = []
        node.left_rectified = None
        node.right_rectified = None
        node.left_img_datum = None
        node.right_img_datum = None

    def perform(self, node):
        self.all_depths = []
        self.all_depths_table = Table()
        self.validation_issues = []

        left_img_datum = node.getInput(0)  
        right_img_datum = node.getInput(1)  
        node.left_img_datum = left_img_datum
        node.right_img_datum = right_img_datum
        node.left_rectified = None
        node.right_rectified = None

        self.validate_calibration_consistency()

        if left_img_datum is None or right_img_datum is None:
            self.add_validation_issue("Invalid", "Inputs", "Left and right image inputs are required.")
            self.finish_node(node)
            return

        left_img_cube = left_img_datum.get(Datum.IMG)
        right_img_cube = right_img_datum.get(Datum.IMG)

        if left_img_cube is None or right_img_cube is None:
            self.add_validation_issue("Invalid", "Inputs", "Left and right image inputs must both be images.")
            self.finish_node(node)
            return

        left_img_rois = left_img_cube.rois
        right_img_rois = right_img_cube.rois

        node.left_rectified = left_img_cube
        node.right_rectified = right_img_cube

        if not left_img_rois or not right_img_rois:
            self.add_validation_issue("Invalid", "ROIs", "Both images must contain labelled circle ROIs.")
            self.finish_node(node)
            return

        left_rois_sorted = self.extract_and_check_rois(left_img_datum)
        right_rois_sorted = self.extract_and_check_rois(right_img_datum)

        self.validate_roi_pairs(left_rois_sorted, right_rois_sorted)

        for label in sorted(left_rois_sorted.keys() & right_rois_sorted.keys()):
            left_rois_match = left_rois_sorted[label]
            right_rois_match = right_rois_sorted[label]

            if len(left_rois_match) != 1 or len(right_rois_match) != 1:
                continue

            try:
                storage = self.build_measurement(label, left_rois_match[0], right_rois_match[0])
            except DistanceEstimateException as ex:
                self.add_validation_issue("Invalid", label, str(ex))
                continue

            self.all_depths.append(storage)

        if not self.all_depths and not self.validation_issues:
            self.add_validation_issue("Invalid", "ROIs", "No matching labelled ROI pairs were found.")

        self.finish_node(node)

    def finish_node(self, node):
        self.populate_table()

        node.all_depths = self.all_depths
        node.all_depths_table = self.all_depths_table
        node.validation_issues = self.validation_issues

        node.setOutput(0, Datum(Datum.DATA, str(self.all_depths_table), nullSourceSet))

        if hasattr(node, 'tabs') and node.tabs is not None:
            for tab in node.tabs:
                tab.onNodeChanged()

    def get_crow(self, depth):
        height = self.camera_height
        if height is None:
            raise DistanceEstimateException("Camera height calibration is not loaded.")
        if depth < height:
            raise DistanceEstimateException(
                f"Depth {depth:.6g} is smaller than camera height {height:.6g}."
            )
        return (depth**2 - height**2)**0.5

    def load_rectification_json(self, file_path):
        if not os.path.exists(file_path):
            return

        with open(file_path, 'r') as file:
            data = json.load(file)

        focal_terms = []
        for key in ('proj_left', 'proj_right'):
            proj = data.get(key)
            if proj is None:
                continue
            focal_terms.extend([proj[0][0], proj[1][1]])

        if focal_terms:
            self.rectified_focal_length = sum(focal_terms) / len(focal_terms)

    def validate_calibration_consistency(self):
        if self.focal_length is None or self.rectified_focal_length is None:
            return

        diff_ratio = abs(self.rectified_focal_length - self.focal_length) / self.rectified_focal_length
        if diff_ratio > self.CALIBRATION_FOCAL_TOLERANCE_RATIO:
            self.add_validation_issue(
                "Warning",
                "Calibration",
                "Distance focal length differs from rectified projection focal length."
            )

    def extract_measurement_point(self, label, roi, side):
        if not isinstance(roi, ROICircle):
            raise DistanceEstimateException(
                f"{side} ROI for label '{label}' must be a circle ROI for measurement."
            )
        return float(roi.x), float(roi.y)

    def estimate_depth(self, left_x, right_x):
        """Estimates the depth of a point given its x coordinates in the left and right images.

        Parameters:
        left_x (float): The x coordinate of the point in the left image.
        right_x (float): The x coordinate of the point in the right image.

        Returns:
        float: The estimated depth of the point.

        Raises:
        ValueError: If the disparity is zero.
        """
        if self.focal_length is None or self.baseline is None:
            raise DistanceEstimateException("Focal length and baseline calibration are not loaded.")

        disparity = left_x - right_x

        if disparity == 0:
            raise DistanceEstimateException("Disparity cannot be zero.")
        if disparity < 0:
            raise DistanceEstimateException(
                f"Disparity has the wrong sign ({disparity:.6g}); check image order and ROI pairing."
            )
        if disparity < self.MIN_DISPARITY_PX:
            raise DistanceEstimateException(
                f"Disparity {disparity:.6g} is below the minimum threshold of {self.MIN_DISPARITY_PX:.6g} px."
            )

        depth = self.focal_length * self.baseline / disparity

        return depth

    def estimate_uncertainty(self, disparity, depth):
        disparity_error = self.PIXEL_ERROR_PX
        lower_disparity = disparity + disparity_error
        upper_disparity = disparity - disparity_error

        if upper_disparity <= 0:
            raise DistanceEstimateException("Disparity is too small for the configured pixel-error model.")

        depth_low = self.focal_length * self.baseline / lower_disparity
        depth_high = self.focal_length * self.baseline / upper_disparity
        depth_uncertainty = max(abs(depth - depth_low), abs(depth_high - depth))

        return depth_low, depth_high, depth_uncertainty

    def classify_quality(self, disparity, vertical_offset, relative_uncertainty):
        if (
            vertical_offset <= self.HIGH_QUALITY_MAX_VERTICAL_OFFSET_PX
            and disparity >= self.HIGH_QUALITY_MIN_DISPARITY_PX
            and relative_uncertainty <= self.HIGH_QUALITY_MAX_REL_UNCERTAINTY
        ):
            return "High", "OK", "Accepted"

        if (
            vertical_offset <= self.MEDIUM_QUALITY_MAX_VERTICAL_OFFSET_PX
            and disparity >= self.MEDIUM_QUALITY_MIN_DISPARITY_PX
            and relative_uncertainty <= self.MEDIUM_QUALITY_MAX_REL_UNCERTAINTY
        ):
            return "Medium", "OK", "Accepted"

        return "Low", "Warning", "Accepted with elevated uncertainty."

    def build_measurement(self, label, left_roi, right_roi):
        left_x, left_y = self.extract_measurement_point(label, left_roi, "Left")
        right_x, right_y = self.extract_measurement_point(label, right_roi, "Right")
        disparity = left_x - right_x
        vertical_offset = abs(left_y - right_y)

        if vertical_offset > self.MAX_VERTICAL_OFFSET_PX:
            raise DistanceEstimateException(
                f"Vertical offset {vertical_offset:.6g} px exceeds the maximum of {self.MAX_VERTICAL_OFFSET_PX:.6g} px."
            )

        depth = self.estimate_depth(left_x, right_x)
        ground_distance = self.get_crow(depth)
        depth_low, depth_high, depth_uncertainty = self.estimate_uncertainty(disparity, depth)
        relative_uncertainty = depth_uncertainty / depth if depth != 0 else math.inf
        quality, status, message = self.classify_quality(disparity, vertical_offset, relative_uncertainty)

        return self.store_depth_and_rois(
            label,
            depth,
            ground_distance,
            disparity,
            vertical_offset,
            depth_low,
            depth_high,
            depth_uncertainty,
            quality,
            status,
            message,
            left_roi,
            right_roi
        )

    def extract_and_check_rois(self, datum):
        """
        Extract ROIs from a Datum object and ensure they are labeled if there are multiple ROIs.

        Parameters:
        datum (Datum): The Datum object to check.

        Returns:
        dict: A dictionary of ROIs keyed by their labels, sorted by label.

        """
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
                roi_dict = {}
                for roi in rois:
                    if not roi.label:
                        self.add_validation_issue("Invalid", "ROIs", "All ROIs must be labelled.")
                    else:
                        if roi.label not in roi_dict:
                            roi_dict[roi.label] = []
                        roi_dict[roi.label].append(roi)
                
                # Sorting ROIs by label
                sorted_rois = {label: roi_dict[label] for label in sorted(roi_dict)}
                return sorted_rois

        return {}

    def validate_roi_pairs(self, left_rois, right_rois):
        left_labels = set(left_rois)
        right_labels = set(right_rois)

        for label in sorted(left_labels - right_labels):
            self.add_validation_issue("Invalid", label, "Label exists only on the left image.")
        for label in sorted(right_labels - left_labels):
            self.add_validation_issue("Invalid", label, "Label exists only on the right image.")
        for label, rois in sorted(left_rois.items()):
            if len(rois) > 1:
                self.add_validation_issue("Invalid", label, "Duplicate label on the left image.")
        for label, rois in sorted(right_rois.items()):
            if len(rois) > 1:
                self.add_validation_issue("Invalid", label, "Duplicate label on the right image.")

    def add_validation_issue(self, status, label, message):
        self.validation_issues.append({"status": status, "label": label, "message": message})

    def store_depth_and_rois(
        self,
        label,
        depth,
        ground_distance,
        disparity,
        vertical_offset,
        depth_low,
        depth_high,
        depth_uncertainty,
        quality,
        status,
        message,
        left_roi,
        right_roi
    ):
        """
        Stores the depth and the two ROIs in a dictionary.
        
        Parameters:
        depth (float): The calculated depth.
        crow (float): The calculated crow distance.
        left_roi (ROI): The ROI from the left image.
        right_roi (ROI): The ROI from the right image.
        
        Returns:
        dict: A dictionary containing the depth, crow and the ROIs.
        """
        storage = {
            "label": label,
            "depth": depth,
            "ground_distance": ground_distance,
            "disparity": disparity,
            "vertical_offset": vertical_offset,
            "depth_low": depth_low,
            "depth_high": depth_high,
            "depth_uncertainty": depth_uncertainty,
            "quality": quality,
            "status": status,
            "message": message,
            "left_roi": left_roi.to_tagged_dict(),
            "right_roi": right_roi.to_tagged_dict(),
        }
        return storage

    def format_number(self, value):
        return f"{value:.3f}"

    def populate_table(self):        
        """
        Populate the table with the stored depths and ROIs.
        
        Iterates through the stored depths and ROIs, and populates a table with the
        results. The table is sorted by the label of the right ROI.
        """
    
        table = Table()

        for data in self.all_depths:
            table.newRow(data['label'])
            table.add('Label', data['label'])
            table.add('Depth (m)', self.format_number(data['depth']))
            table.add('Ground Distance (m)', self.format_number(data['ground_distance']))
            table.add('Disparity (px)', self.format_number(data['disparity']))
            table.add('Vertical Offset (px)', self.format_number(data['vertical_offset']))
            table.add('Depth Low (m)', self.format_number(data['depth_low']))
            table.add('Depth High (m)', self.format_number(data['depth_high']))
            table.add('Depth Uncertainty (m)', self.format_number(data['depth_uncertainty']))
            table.add('Quality', data['quality'])
            table.add('Status', data['status'])
            table.add('Message', data['message'])

        for idx, issue in enumerate(self.validation_issues):
            table.newRow(f"issue:{idx}:{issue['label']}")
            table.add('Label', issue['label'])
            table.add('Depth (m)', '')
            table.add('Ground Distance (m)', '')
            table.add('Disparity (px)', '')
            table.add('Vertical Offset (px)', '')
            table.add('Depth Low (m)', '')
            table.add('Depth High (m)', '')
            table.add('Depth Uncertainty (m)', '')
            table.add('Quality', '')
            table.add('Status', issue['status'])
            table.add('Message', issue['message'])

        self.all_depths_table = table
    
class DistanceEstimateException(Exception):
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
        self.update_tab_table(getattr(node, 'all_depths_table', Table()))


        if hasattr(node, 'left_rectified') and node.left_rectified is not None:
            # left_img_cube = ImageCube(node.left_rectified)
            left_img_cube = node.left_rectified

            self.left_canvas.display(left_img_cube)
        else:
            self.left_canvas.setImg(None)

        if hasattr(node, 'right_rectified') and node.right_rectified is not None:
            # right_img_cube = ImageCube(node.right_rectified)
            right_img_cube = node.right_rectified
            self.right_canvas.display(right_img_cube)
        else:
            self.right_canvas.setImg(None)

        if getattr(self.node, 'left_img_datum', None) is None:
            self.left_canvas.setImg(None)
            return
        if getattr(self.node, 'right_img_datum', None) is None:
            self.right_canvas.setImg(None)
            return

    def update_tab_table(self, depth_table):
        self.table_widget.clear()

        row_count = depth_table.__len__()

        self.table_widget.setRowCount(row_count)

        headers = depth_table.keys()

        # print(distance_table.__str__())

        self.table_widget.setColumnCount(len(headers))

        self.table_widget.setHorizontalHeaderLabels(headers)

        for row_index, data in enumerate(depth_table):
            for col_index, header in enumerate(headers):
                # header = int(header)
                self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(data[col_index])))

        self.table_widget.resizeColumnsToContents()

    def dump_data_to_txt(self):
        if self.node.all_depths_table is None:
            print("No data to dump TXT")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "depths.txt", "Text Files (*.txt);;All files (*.*)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                headers = self.node.all_depths_table.keys()
                f.write(", ".join(f'{header}' for header in headers) + "\n")
                for row in self.node.all_depths_table:
                    f.write(", ".join(f'{header}: {row[i]}' for i, header in enumerate(headers)) + "\n")

            print(f"Data dumped to {file_name}")

    def dump_data_to_csv(self):
        if self.node.all_depths_table is None:
            print("No data to dump CSV")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "depths.csv", "CSV Files (*.csv);;All files (*.*)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                # Write the header
                headers = self.node.all_depths_table.keys()
                for header in headers:
                    f.write(f"{header},")
                f.write("\n")

                for row in self.node.all_depths_table:
                    f.write(",".join(map(str, row)) + "\n")

            print(f"Data dumped to {file_name}")

    def dump_data_to_html(self):
        if self.node.all_depths_table is None:
            print("No data to dump HTML")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "depths.html", "HTML Files (*.html);;All files (*.*)", options=options)
        if file_name:
            with open(file_name, "w") as f:
                f.write(self.node.all_depths_table.html())
            print(f"Data dumped to {file_name}")
