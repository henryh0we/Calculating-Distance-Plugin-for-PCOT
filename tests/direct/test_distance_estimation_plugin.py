import importlib.util
import sys
import types

import pytest

HAS_PYSIDE2 = importlib.util.find_spec("PySide2") is not None
pytestmark = pytest.mark.skipif(not HAS_PYSIDE2, reason="PySide2 not installed")

markdown = types.ModuleType("markdown")
markdown.markdown = lambda text, *args, **kwargs: text
sys.modules.setdefault("markdown", markdown)

if HAS_PYSIDE2:
    from pcot.rois import ROICircle, ROIRect
    from pcotplugins.distance_estimation_plugin.pcotdistanceestimate.xformdistestimateROI import (
        DistanceEstimateException,
        XFormDistEstimateRoi,
    )


@pytest.fixture
def dist_node():
    node = XFormDistEstimateRoi()
    node.focal_length = 1753.623188405797
    node.baseline = 0.5
    node.camera_height = 1.094
    node.rectified_focal_length = node.focal_length
    return node


def test_build_measurement_returns_diagnostics_for_valid_circle_pair(dist_node):
    left = ROICircle(741, 783, 10, label="3m")
    right = ROICircle(459, 783, 10, label="3m")

    measurement = dist_node.build_measurement("3m", left, right)

    assert measurement["label"] == "3m"
    assert measurement["disparity"] == pytest.approx(282.0)
    assert measurement["vertical_offset"] == pytest.approx(0.0)
    assert measurement["depth"] == pytest.approx(
        dist_node.focal_length * dist_node.baseline / 282.0
    )
    assert measurement["ground_distance"] < measurement["depth"]
    assert measurement["depth_low"] < measurement["depth"] < measurement["depth_high"]
    assert measurement["depth_uncertainty"] > 0
    assert measurement["quality"] == "High"
    assert measurement["status"] == "OK"


def test_build_measurement_rejects_non_circle_rois(dist_node):
    left = ROIRect(label="3m", rect=(741, 783, 10, 10))
    right = ROICircle(459, 783, 10, label="3m")

    with pytest.raises(DistanceEstimateException, match="must be a circle ROI"):
        dist_node.build_measurement("3m", left, right)


def test_build_measurement_rejects_large_vertical_offset(dist_node):
    left = ROICircle(741, 783, 10, label="3m")
    right = ROICircle(459, 786, 10, label="3m")

    with pytest.raises(DistanceEstimateException, match="Vertical offset"):
        dist_node.build_measurement("3m", left, right)


def test_build_measurement_warns_for_low_quality_measurements(dist_node):
    left = ROICircle(100, 100, 10, label="far")
    right = ROICircle(91, 101, 10, label="far")

    measurement = dist_node.build_measurement("far", left, right)

    assert measurement["disparity"] == pytest.approx(9.0)
    assert measurement["vertical_offset"] == pytest.approx(1.0)
    assert measurement["quality"] == "Low"
    assert measurement["status"] == "Warning"


def test_validate_calibration_consistency_adds_warning_when_focals_drift(dist_node):
    dist_node.rectified_focal_length = dist_node.focal_length * 1.05
    dist_node.validation_issues = []

    dist_node.validate_calibration_consistency()

    assert dist_node.validation_issues == [
        {
            "status": "Warning",
            "label": "Calibration",
            "message": "Distance focal length differs from rectified projection focal length.",
        }
    ]
