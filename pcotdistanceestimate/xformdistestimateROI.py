import importlib.util
import os
import sys
from types import SimpleNamespace
from pcot.ui.canvas import Canvas
from pcot.ui.tabs import Tab
from pcot.utils.table import Table
from pcot.sources import nullSourceSet
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from PySide2.QtCore import Qt
import json

from pcot.parameters.taggedaggregates import TaggedDictType
from pcot.xform import XFormType, xformtype
from pcot.datum import Datum

try:
    from distance_calculator import (
        DistanceEstimateException,
        ValidationIssue,
        build_measurement,
        group_rois_by_label,
        validate_roi_pairs,
    )
except ModuleNotFoundError:
    calculator_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distance_calculator.py")
    spec = importlib.util.spec_from_file_location("distance_calculator", calculator_path)
    calculator = importlib.util.module_from_spec(spec)
    sys.modules["distance_calculator"] = calculator
    spec.loader.exec_module(calculator)
    DistanceEstimateException = calculator.DistanceEstimateException
    ValidationIssue = calculator.ValidationIssue
    build_measurement = calculator.build_measurement
    group_rois_by_label = calculator.group_rois_by_label
    validate_roi_pairs = calculator.validate_roi_pairs

# camera_height = 1.094

MEASUREMENT_PARAM_FIELDS = [
    (
        "cameraHeightM",
        "Camera Height (m)",
        "Height of the camera above the ground plane. The default/current loaded value is the height of the AUPE Camera System.",
    ),
    (
        "minDisparityPx",
        "Min Disparity (px)",
        "Minimum positive horizontal pixel difference required before a stereo measurement is accepted.",
    ),
    (
        "maxVerticalOffsetPx",
        "Max Vertical Offset (px)",
        "Largest allowed vertical difference between left and right ROI centres after rectification.",
    ),
    (
        "mediumQualityMaxVerticalOffsetPx",
        "Medium Quality Max Vertical Offset (px)",
        "Maximum vertical offset allowed for a measurement to be classed as medium quality.",
    ),
    (
        "highQualityMaxVerticalOffsetPx",
        "High Quality Max Vertical Offset (px)",
        "Maximum vertical offset allowed for a measurement to be classed as high quality.",
    ),
    (
        "highQualityMinDisparityPx",
        "High Quality Min Disparity (px)",
        "Minimum disparity required for a measurement to be classed as high quality.",
    ),
    (
        "mediumQualityMinDisparityPx",
        "Medium Quality Min Disparity (px)",
        "Minimum disparity required for a measurement to be classed as medium quality.",
    ),
    (
        "pixelErrorPx",
        "Pixel Error (px)",
        "Assumed disparity error in pixels used to estimate the depth uncertainty range.",
    ),
    (
        "highQualityMaxRelUncertainty",
        "High Quality Max Relative Uncertainty",
        "Maximum relative depth uncertainty allowed for a measurement to be classed as high quality.",
    ),
    (
        "mediumQualityMaxRelUncertainty",
        "Medium Quality Max Relative Uncertainty",
        "Maximum relative depth uncertainty allowed for a measurement to be classed as medium quality.",
    ),
    (
        "calibrationFocalToleranceRatio",
        "Calibration Focal Tolerance Ratio",
        "Relative difference allowed between the depth focal value and the rectified projection focal before a warning is shown.",
    ),
]

MEASUREMENT_PARAM_SPINBOX_CONFIG = {
    "cameraHeightM": {"decimals": 4, "step": 0.001},
    "minDisparityPx": {"decimals": 2, "step": 0.1},
    "maxVerticalOffsetPx": {"decimals": 2, "step": 0.1},
    "mediumQualityMaxVerticalOffsetPx": {"decimals": 2, "step": 0.1},
    "highQualityMaxVerticalOffsetPx": {"decimals": 2, "step": 0.1},
    "highQualityMinDisparityPx": {"decimals": 2, "step": 0.5},
    "mediumQualityMinDisparityPx": {"decimals": 2, "step": 0.5},
    "pixelErrorPx": {"decimals": 2, "step": 0.1},
    "highQualityMaxRelUncertainty": {"decimals": 4, "step": 0.01},
    "mediumQualityMaxRelUncertainty": {"decimals": 4, "step": 0.01},
    "calibrationFocalToleranceRatio": {"decimals": 4, "step": 0.001},
}


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
            cameraHeightM=("Camera height above the ground plane in metres", float, self.camera_height or 1.094),
            minDisparityPx=("Minimum positive disparity accepted for distance estimation", float, 2.0),
            maxVerticalOffsetPx=("Maximum vertical offset allowed between matched circle centres", float, 2.0),
            mediumQualityMaxVerticalOffsetPx=("Maximum vertical offset for medium quality classification", float, 1.0),
            highQualityMaxVerticalOffsetPx=("Maximum vertical offset for high quality classification", float, 0.5),
            highQualityMinDisparityPx=("Minimum disparity for high quality classification", float, 20.0),
            mediumQualityMinDisparityPx=("Minimum disparity for medium quality classification", float, 8.0),
            pixelErrorPx=("Disparity error used for uncertainty estimation", float, 1.0),
            highQualityMaxRelUncertainty=("Maximum relative uncertainty for high quality classification", float, 0.05),
            mediumQualityMaxRelUncertainty=("Maximum relative uncertainty for medium quality classification", float, 0.15),
            calibrationFocalToleranceRatio=("Maximum allowed focal drift ratio before warning", float, 0.01),
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
        node.left_image_cube = None
        node.right_image_cube = None
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
        node.left_image_cube = None
        node.right_image_cube = None

        self.validate_calibration_consistency(node.params)

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

        node.left_image_cube = left_img_cube
        node.right_image_cube = right_img_cube

        if not left_img_cube.rois or not right_img_cube.rois:
            self.add_validation_issue("Invalid", "ROIs", "Both images must contain labelled circle ROIs.")
            self.finish_node(node)
            return

        left_rois_sorted, left_issues = group_rois_by_label(left_img_cube.rois)
        right_rois_sorted, right_issues = group_rois_by_label(right_img_cube.rois)
        self.validation_issues.extend(left_issues)
        self.validation_issues.extend(right_issues)

        self.validation_issues.extend(validate_roi_pairs(left_rois_sorted, right_rois_sorted))

        for label in sorted(left_rois_sorted.keys() & right_rois_sorted.keys()):
            left_rois_match = left_rois_sorted[label]
            right_rois_match = right_rois_sorted[label]

            if len(left_rois_match) != 1 or len(right_rois_match) != 1:
                continue

            try:
                calibration = SimpleNamespace(
                    focal_length=self.focal_length,
                    baseline=self.baseline,
                    camera_height=node.params.cameraHeightM,
                )
                storage = build_measurement(node.params, calibration, label, left_rois_match[0], right_rois_match[0])
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

    def validate_calibration_consistency(self, params):
        if self.focal_length is None or self.rectified_focal_length is None:
            return

        diff_ratio = abs(self.rectified_focal_length - self.focal_length) / self.rectified_focal_length
        if diff_ratio > params.calibrationFocalToleranceRatio:
            self.add_validation_issue(
                "Warning",
                "Calibration",
                "Distance focal length differs from rectified projection focal length."
            )

    def add_validation_issue(self, status, label, message):
        self.validation_issues.append(ValidationIssue(status, label, message))

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
            table.newRow(f"issue:{idx}:{issue.label}")
            table.add('Label', issue.label)
            table.add('Depth (m)', '')
            table.add('Ground Distance (m)', '')
            table.add('Disparity (px)', '')
            table.add('Vertical Offset (px)', '')
            table.add('Depth Low (m)', '')
            table.add('Depth High (m)', '')
            table.add('Depth Uncertainty (m)', '')
            table.add('Quality', '')
            table.add('Status', issue.status)
            table.add('Message', issue.message)

        self.all_depths_table = table


class MeasurementSettingsDialog(QDialog):
    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.original_values = {
            key: getattr(node.params, key)
            for key, _, _ in MEASUREMENT_PARAM_FIELDS
        }
        self.inputs = {}

        self.setWindowTitle("Measurement Settings")

        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)

        for row, (key, label, help_text) in enumerate(MEASUREMENT_PARAM_FIELDS):
            label_widget = QLabel(label)
            grid.addWidget(label_widget, row, 0)

            info_button = QToolButton()
            info_button.setText("info")
            info_button.setAutoRaise(True)
            info_button.setCursor(Qt.PointingHandCursor)
            info_button.setStyleSheet(
                "QToolButton { color: #0057b8; text-decoration: underline; padding: 0px; }"
            )
            info_button.clicked.connect(
                lambda _checked=False, button=info_button, text=help_text: self.show_help_popup(button, text)
            )
            grid.addWidget(info_button, row, 1, alignment=Qt.AlignLeft)

            config = MEASUREMENT_PARAM_SPINBOX_CONFIG[key]
            spin = QDoubleSpinBox()
            spin.setDecimals(config["decimals"])
            spin.setSingleStep(config["step"])
            spin.setRange(0.0001, 1_000_000.0)
            spin.setValue(float(self.original_values[key]))
            self.inputs[key] = spin
            grid.addWidget(spin, row, 2)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.try_save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(grid)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def show_help_popup(self, button, text):
        QToolTip.showText(button.mapToGlobal(button.rect().bottomLeft()), text, button)

    def try_save(self):
        parsed = self.parse_values()
        if parsed is None:
            return

        if not self.has_changes(parsed):
            self.accept()
            return

        response = QMessageBox.question(
            self,
            "Save Measurement Settings",
            "Are you sure you want to save the changed measurement settings?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if response != QMessageBox.Yes:
            return

        for key, value in parsed.items():
            setattr(self.node.params, key, value)
        self.accept()

    def parse_values(self):
        parsed = {}
        for key, _, _ in MEASUREMENT_PARAM_FIELDS:
            parsed[key] = float(self.inputs[key].value())

        for key, label, _ in MEASUREMENT_PARAM_FIELDS:
            if parsed[key] <= 0:
                QMessageBox.warning(self, "Invalid Value", f"{label} must be greater than zero.")
                return None

        if parsed["highQualityMaxVerticalOffsetPx"] > parsed["mediumQualityMaxVerticalOffsetPx"]:
            QMessageBox.warning(
                self,
                "Invalid Value",
                "High quality max vertical offset must be less than or equal to medium quality max vertical offset."
            )
            return None

        if parsed["highQualityMinDisparityPx"] < parsed["mediumQualityMinDisparityPx"]:
            QMessageBox.warning(
                self,
                "Invalid Value",
                "High quality min disparity must be greater than or equal to medium quality min disparity."
            )
            return None

        if parsed["highQualityMaxRelUncertainty"] > parsed["mediumQualityMaxRelUncertainty"]:
            QMessageBox.warning(
                self,
                "Invalid Value",
                "High quality max relative uncertainty must be less than or equal to medium quality max relative uncertainty."
            )
            return None

        return parsed

    def has_changes(self, parsed):
        for key, value in parsed.items():
            if value != self.original_values[key]:
                return True
        return False

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

        self.settings_button = QPushButton("Measurement Settings...")
        self.settings_button.clicked.connect(self.open_measurement_settings)
        self.button_layout.addWidget(self.settings_button)

        self.layout.addLayout(self.button_layout)

    def open_measurement_settings(self):
        dialog = MeasurementSettingsDialog(self.node, self)
        if dialog.exec_():
            self.changed()

    def onNodeChanged(self):
        node = self.node
        self.update_tab_table(getattr(node, 'all_depths_table', Table()))


        if hasattr(node, 'left_image_cube') and node.left_image_cube is not None:
            left_img_cube = node.left_image_cube
            self.left_canvas.display(left_img_cube)
        else:
            self.left_canvas.setImg(None)

        if hasattr(node, 'right_image_cube') and node.right_image_cube is not None:
            right_img_cube = node.right_image_cube
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
