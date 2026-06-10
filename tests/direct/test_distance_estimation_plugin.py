import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

markdown = types.ModuleType("markdown")
markdown.markdown = lambda text, *args, **kwargs: text
sys.modules.setdefault("markdown", markdown)

from pcotplugins.distance_estimation_plugin.pcotdistanceestimate.distance_calculator import (
    DistanceEstimateException,
    ValidationIssue,
    build_measurement,
    group_rois_by_label,
    validate_roi_pairs,
)

HAS_PYSIDE2 = importlib.util.find_spec("PySide2") is not None

if HAS_PYSIDE2:
    from pcot.datum import Datum
    from pcot.imagecube import ImageCube
    from pcotplugins.distance_estimation_plugin.pcotdistanceestimate import xformrectify as xformrectify_module
    from pcotplugins.distance_estimation_plugin.pcotdistanceestimate.xformdistestimateROI import (
        XFormDistEstimateRoi,
    )
    from pcotplugins.distance_estimation_plugin.pcotdistanceestimate.xformrectify import (
        XFormImageRectify,
    )


class CircleRoi:
    tpname = "circle"

    def __init__(self, x, y, r, label=None):
        self.x = x
        self.y = y
        self.r = r
        self.label = label

    def to_tagged_dict(self):
        return {"type": "circle", "x": self.x, "y": self.y, "r": self.r, "label": self.label}


class RectRoi:
    tpname = "rect"

    def __init__(self, label=None, rect=None):
        self.label = label
        self.rect = rect

    def to_tagged_dict(self):
        return {"type": "rect", "rect": self.rect, "label": self.label}


class FakeRectifyNode:
    def __init__(self):
        self.inputs = [None, None]
        self.outputs = {}
        self.input_requests = []

    def getInput(self, idx, datum_type=None):
        self.input_requests.append((idx, datum_type))
        value = self.inputs[idx]
        if datum_type is not None and hasattr(value, "get"):
            return value.get(datum_type)
        return value

    def setOutput(self, idx, datum):
        self.outputs[idx] = datum


def valid_rectification_calibration():
    return {
        "mtx_left": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "dist_left": [0.0, 0.0, 0.0, 0.0, 0.0],
        "rect_left": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "proj_left": [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        "mtx_right": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "dist_right": [0.0, 0.0, 0.0, 0.0, 0.0],
        "rect_right": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "proj_right": [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
    }


def write_calibration(tmp_path, data):
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def measurement_params():
    return SimpleNamespace(
        minDisparityPx=2.0,
        maxVerticalOffsetPx=2.0,
        mediumQualityMaxVerticalOffsetPx=1.0,
        highQualityMaxVerticalOffsetPx=0.5,
        highQualityMinDisparityPx=20.0,
        mediumQualityMinDisparityPx=8.0,
        pixelErrorPx=1.0,
        highQualityMaxRelUncertainty=0.05,
        mediumQualityMaxRelUncertainty=0.15,
    )


@pytest.fixture
def calibration():
    return SimpleNamespace(
        focal_length=1753.623188405797,
        baseline=0.5,
        camera_height=1.094,
    )


def test_build_measurement_returns_diagnostics_for_valid_circle_pair(measurement_params, calibration):
    left = CircleRoi(741, 783, 10, label="3m")
    right = CircleRoi(459, 783, 10, label="3m")

    measurement = build_measurement(measurement_params, calibration, "3m", left, right)

    assert measurement["label"] == "3m"
    assert measurement["disparity"] == pytest.approx(282.0)
    assert measurement["vertical_offset"] == pytest.approx(0.0)
    assert measurement["depth"] == pytest.approx(
        calibration.focal_length * calibration.baseline / 282.0
    )
    assert measurement["ground_distance"] < measurement["depth"]
    assert measurement["depth_low"] < measurement["depth"] < measurement["depth_high"]
    assert measurement["depth_uncertainty"] > 0
    assert measurement["quality"] == "High"
    assert measurement["status"] == "OK"


def test_group_rois_by_label_reports_unlabelled_rois():
    grouped, issues = group_rois_by_label([CircleRoi(1, 2, 3), CircleRoi(4, 5, 6, label="a")])

    assert list(grouped) == ["a"]
    assert issues == [ValidationIssue("Invalid", "ROIs", "All ROIs must be labelled.")]


def test_validate_roi_pairs_reports_duplicate_labels():
    left = {"a": [CircleRoi(1, 1, 1, label="a"), CircleRoi(2, 2, 1, label="a")]}
    right = {"a": [CircleRoi(0, 1, 1, label="a"), CircleRoi(-1, 2, 1, label="a")]}

    issues = validate_roi_pairs(left, right)

    assert issues == [
        ValidationIssue("Invalid", "a", "Duplicate label on the left image."),
        ValidationIssue("Invalid", "a", "Duplicate label on the right image."),
    ]


def test_validate_roi_pairs_reports_missing_labels():
    left = {"left-only": [CircleRoi(1, 1, 1, label="left-only")]}
    right = {"right-only": [CircleRoi(0, 1, 1, label="right-only")]}

    issues = validate_roi_pairs(left, right)

    assert issues == [
        ValidationIssue("Invalid", "left-only", "Label exists only on the left image."),
        ValidationIssue("Invalid", "right-only", "Label exists only on the right image."),
    ]


def test_build_measurement_rejects_zero_disparity(measurement_params, calibration):
    left = CircleRoi(100, 100, 10, label="same")
    right = CircleRoi(100, 100, 10, label="same")

    with pytest.raises(DistanceEstimateException, match="Disparity cannot be zero"):
        build_measurement(measurement_params, calibration, "same", left, right)


def test_build_measurement_rejects_wrong_sign_disparity(measurement_params, calibration):
    left = CircleRoi(100, 100, 10, label="swapped")
    right = CircleRoi(101, 100, 10, label="swapped")

    with pytest.raises(DistanceEstimateException, match="wrong sign"):
        build_measurement(measurement_params, calibration, "swapped", left, right)


def test_build_measurement_rejects_non_circle_rois(measurement_params, calibration):
    left = RectRoi(label="3m", rect=(741, 783, 10, 10))
    right = CircleRoi(459, 783, 10, label="3m")

    with pytest.raises(DistanceEstimateException, match="must be a circle ROI"):
        build_measurement(measurement_params, calibration, "3m", left, right)


def test_build_measurement_rejects_large_vertical_offset(measurement_params, calibration):
    left = CircleRoi(741, 783, 10, label="3m")
    right = CircleRoi(459, 786, 10, label="3m")

    with pytest.raises(DistanceEstimateException, match="Vertical offset"):
        build_measurement(measurement_params, calibration, "3m", left, right)


def test_build_measurement_rejects_depth_below_camera_height(measurement_params, calibration):
    left = CircleRoi(1000, 100, 10, label="near")
    right = CircleRoi(0, 100, 10, label="near")

    with pytest.raises(DistanceEstimateException, match="smaller than camera height"):
        build_measurement(measurement_params, calibration, "near", left, right)


def test_build_measurement_warns_for_low_quality_measurements(measurement_params, calibration):
    left = CircleRoi(100, 100, 10, label="far")
    right = CircleRoi(93, 101, 10, label="far")

    measurement = build_measurement(measurement_params, calibration, "far", left, right)

    assert measurement["disparity"] == pytest.approx(7.0)
    assert measurement["vertical_offset"] == pytest.approx(1.0)
    assert measurement["quality"] == "Low"
    assert measurement["status"] == "Warning"


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_init_creates_empty_preview_status_and_cache_state():
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()

    rectify_type.init(node)

    assert node.left_rectified_cube is None
    assert node.right_rectified_cube is None
    assert node.status_message == ""
    assert node._rectify_map_cache == {}


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_missing_inputs_clear_outputs_and_stale_preview_state():
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    node.left_rectified_cube = object()
    node.right_rectified_cube = object()
    node.status_message = "old status"

    rectify_type.perform(node)

    assert node.left_rectified_cube is None
    assert node.right_rectified_cube is None
    assert node.status_message == "Left and right image inputs are required."
    assert node.outputs[0].get(Datum.IMG) is None
    assert node.outputs[1].get(Datum.IMG) is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_uses_typed_image_inputs():
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)

    rectify_type.perform(node)

    assert node.input_requests == [(0, Datum.IMG), (1, Datum.IMG)]


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_non_array_inputs_clear_outputs():
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    node.inputs = [
        SimpleNamespace(img="not an array"),
        SimpleNamespace(img=np.zeros((2, 2), dtype=np.float32)),
    ]

    rectify_type.perform(node)

    assert node.status_message == "Left and right inputs must both contain image arrays."
    assert node.outputs[0].get(Datum.IMG) is None
    assert node.outputs[1].get(Datum.IMG) is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_wrong_dimension_arrays_clear_outputs():
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    node.inputs = [
        SimpleNamespace(img=np.zeros((2,), dtype=np.float32)),
        SimpleNamespace(img=np.zeros((2, 2), dtype=np.float32)),
    ]

    rectify_type.perform(node)

    assert node.status_message == "Left and right image arrays must be 2D or 3D."
    assert node.outputs[0].get(Datum.IMG) is None
    assert node.outputs[1].get(Datum.IMG) is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_opencv_failure_clears_outputs(monkeypatch):
    import cv2 as cv

    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    node.left_rectified_cube = object()
    node.right_rectified_cube = object()
    node.inputs = [
        SimpleNamespace(img=np.zeros((2, 2), dtype=np.float32)),
        SimpleNamespace(img=np.zeros((2, 2), dtype=np.float32)),
    ]

    def raise_cv_error(*_args, **_kwargs):
        raise cv.error("map failed")

    monkeypatch.setattr(cv, "initUndistortRectifyMap", raise_cv_error)

    rectify_type.perform(node)

    assert node.left_rectified_cube is None
    assert node.right_rectified_cube is None
    assert node.status_message.startswith("Rectification failed:")
    assert "map failed" in node.status_message
    assert node.outputs[0].get(Datum.IMG) is None
    assert node.outputs[1].get(Datum.IMG) is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_build_cube_preserves_metadata_and_remaps_companion_arrays():
    rectify_type = XFormImageRectify()
    img = np.arange(9, dtype=np.float32).reshape(3, 3)
    uncertainty = (img + 10).astype(np.float32)
    dq = np.arange(9, dtype=np.uint16).reshape(3, 3)
    input_cube = ImageCube(img, uncertainty=uncertainty, dq=dq)
    input_cube.rois = [object()]
    map_x = np.array(
        [
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
        ],
        dtype=np.float32,
    )
    map_y = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
        ],
        dtype=np.float32,
    )

    output_cube = rectify_type.build_rectified_cube(input_cube, img.copy(), map_x, map_y)

    assert output_cube.mapping is input_cube.mapping
    assert output_cube.sources is input_cube.sources
    np.testing.assert_array_equal(output_cube.img, img)
    np.testing.assert_array_equal(output_cube.uncertainty, uncertainty)
    np.testing.assert_array_equal(output_cube.dq, dq)
    assert output_cube.dq.dtype == np.uint16
    assert output_cube.rois == []


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_map_cache_reuses_same_side_and_size(monkeypatch):
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    calls = []

    def fake_init_map(*args):
        calls.append(args)
        marker = len(calls)
        return f"map-x-{marker}", f"map-y-{marker}"

    monkeypatch.setattr(xformrectify_module.cv, "initUndistortRectifyMap", fake_init_map)

    first_maps = rectify_type.get_rectification_maps(node, "left", (3, 2))
    second_maps = rectify_type.get_rectification_maps(node, "left", (3, 2))

    assert first_maps == ("map-x-1", "map-y-1")
    assert second_maps is first_maps
    assert len(calls) == 1


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_map_cache_regenerates_for_different_size(monkeypatch):
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    calls = []

    def fake_init_map(*args):
        calls.append(args)
        marker = len(calls)
        return f"map-x-{marker}", f"map-y-{marker}"

    monkeypatch.setattr(xformrectify_module.cv, "initUndistortRectifyMap", fake_init_map)

    first_maps = rectify_type.get_rectification_maps(node, "left", (3, 2))
    second_maps = rectify_type.get_rectification_maps(node, "left", (4, 2))

    assert first_maps == ("map-x-1", "map-y-1")
    assert second_maps == ("map-x-2", "map-y-2")
    assert len(calls) == 2


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_map_cache_keeps_left_and_right_separate(monkeypatch):
    rectify_type = XFormImageRectify()
    node = FakeRectifyNode()
    rectify_type.init(node)
    calls = []

    def fake_init_map(*args):
        calls.append(args)
        marker = len(calls)
        return f"map-x-{marker}", f"map-y-{marker}"

    monkeypatch.setattr(xformrectify_module.cv, "initUndistortRectifyMap", fake_init_map)

    left_maps = rectify_type.get_rectification_maps(node, "left", (3, 2))
    right_maps = rectify_type.get_rectification_maps(node, "right", (3, 2))

    assert left_maps == ("map-x-1", "map-y-1")
    assert right_maps == ("map-x-2", "map-y-2")
    assert len(calls) == 2


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_map_cache_is_per_node(monkeypatch):
    rectify_type = XFormImageRectify()
    first_node = FakeRectifyNode()
    second_node = FakeRectifyNode()
    rectify_type.init(first_node)
    rectify_type.init(second_node)
    calls = []

    def fake_init_map(*args):
        calls.append(args)
        marker = len(calls)
        return f"map-x-{marker}", f"map-y-{marker}"

    monkeypatch.setattr(xformrectify_module.cv, "initUndistortRectifyMap", fake_init_map)

    first_node_maps = rectify_type.get_rectification_maps(first_node, "left", (3, 2))
    second_node_maps = rectify_type.get_rectification_maps(second_node, "left", (3, 2))

    assert first_node_maps == ("map-x-1", "map-y-1")
    assert second_node_maps == ("map-x-2", "map-y-2")
    assert len(calls) == 2


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_bundled_calibration_loads_successfully():
    rectify_type = XFormImageRectify()

    assert rectify_type.calibration_error is None
    assert rectify_type.mtx_left.shape == (3, 3)
    assert rectify_type.dist_left.shape[1] == 1
    assert rectify_type.rect_left.shape == (3, 3)
    assert rectify_type.proj_left.shape == (3, 4)
    assert rectify_type.mtx_right.shape == (3, 3)
    assert rectify_type.dist_right.shape[1] == 1
    assert rectify_type.rect_right.shape == (3, 3)
    assert rectify_type.proj_right.shape == (3, 4)


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_calibration_missing_key_reports_clear_error(tmp_path):
    rectify_type = XFormImageRectify()
    data = valid_rectification_calibration()
    del data["proj_right"]

    rectify_type.load_json(write_calibration(tmp_path, data))

    assert rectify_type.calibration_error == "Invalid calibration file: missing keys: proj_right"
    assert rectify_type.mtx_left is None
    assert rectify_type.proj_right is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_calibration_invalid_shape_reports_clear_error(tmp_path):
    rectify_type = XFormImageRectify()
    data = valid_rectification_calibration()
    data["mtx_left"] = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]

    rectify_type.load_json(write_calibration(tmp_path, data))

    assert rectify_type.calibration_error == "Invalid calibration file: mtx_left must have shape (3, 3), got (2, 2)"
    assert rectify_type.mtx_left is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_rectify_invalid_calibration_clears_outputs_before_processing(tmp_path):
    rectify_type = XFormImageRectify()
    data = valid_rectification_calibration()
    del data["mtx_left"]
    rectify_type.load_json(write_calibration(tmp_path, data))
    node = FakeRectifyNode()
    rectify_type.init(node)
    node.left_rectified_cube = object()
    node.right_rectified_cube = object()

    rectify_type.perform(node)

    assert node.left_rectified_cube is None
    assert node.right_rectified_cube is None
    assert node.status_message == "Invalid calibration file: missing keys: mtx_left"
    assert node.outputs[0].get(Datum.IMG) is None
    assert node.outputs[1].get(Datum.IMG) is None


@pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")
def test_validate_calibration_consistency_adds_warning_when_focals_drift():
    dist_node = XFormDistEstimateRoi()
    dist_node.focal_length = 1753.623188405797
    dist_node.baseline = 0.5
    dist_node.camera_height = 1.094
    dist_node.rectified_focal_length = dist_node.focal_length * 1.05
    dist_node.validation_issues = []
    params = dist_node.params.create()

    dist_node.validate_calibration_consistency(params)

    assert dist_node.validation_issues == [
        ValidationIssue(
            "Warning",
            "Calibration",
            "Distance focal length differs from rectified projection focal length.",
        )
    ]
