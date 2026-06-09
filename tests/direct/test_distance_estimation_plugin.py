import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

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
    from pcotplugins.distance_estimation_plugin.pcotdistanceestimate.xformdistestimateROI import (
        XFormDistEstimateRoi,
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
