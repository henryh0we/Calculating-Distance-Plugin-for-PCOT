import math
from dataclasses import dataclass


class DistanceEstimateException(Exception):
    pass


@dataclass(frozen=True)
class ValidationIssue:
    status: str
    label: str
    message: str


def group_rois_by_label(rois):
    issues = []
    grouped = {}

    for roi in rois or []:
        if not getattr(roi, "label", None):
            issues.append(ValidationIssue("Invalid", "ROIs", "All ROIs must be labelled."))
            continue

        grouped.setdefault(roi.label, []).append(roi)

    return {label: grouped[label] for label in sorted(grouped)}, issues


def validate_roi_pairs(left_rois, right_rois):
    issues = []
    left_labels = set(left_rois)
    right_labels = set(right_rois)

    for label in sorted(left_labels - right_labels):
        issues.append(ValidationIssue("Invalid", label, "Label exists only on the left image."))
    for label in sorted(right_labels - left_labels):
        issues.append(ValidationIssue("Invalid", label, "Label exists only on the right image."))
    for label, rois in sorted(left_rois.items()):
        if len(rois) > 1:
            issues.append(ValidationIssue("Invalid", label, "Duplicate label on the left image."))
    for label, rois in sorted(right_rois.items()):
        if len(rois) > 1:
            issues.append(ValidationIssue("Invalid", label, "Duplicate label on the right image."))

    return issues


def is_circle_roi(roi):
    return getattr(roi.__class__, "tpname", None) == "circle" or roi.__class__.__name__ == "ROICircle"


def extract_measurement_point(label, roi, side):
    if not is_circle_roi(roi):
        raise DistanceEstimateException(
            f"{side} ROI for label '{label}' must be a circle ROI for measurement."
        )
    return float(roi.x), float(roi.y)


def calculate_disparity(params, left_x, right_x):
    disparity = left_x - right_x

    if disparity == 0:
        raise DistanceEstimateException("Disparity cannot be zero.")
    if disparity < 0:
        raise DistanceEstimateException(
            f"Disparity has the wrong sign ({disparity:.6g}); check image order and ROI pairing."
        )
    if disparity < params.minDisparityPx:
        raise DistanceEstimateException(
            f"Disparity {disparity:.6g} is below the minimum threshold of {params.minDisparityPx:.6g} px."
        )

    return disparity


def estimate_depth(focal_length, baseline, disparity):
    if focal_length is None or baseline is None:
        raise DistanceEstimateException("Focal length and baseline calibration are not loaded.")

    return focal_length * baseline / disparity


def calculate_ground_distance(camera_height, depth):
    if camera_height is None:
        raise DistanceEstimateException("Camera height calibration is not loaded.")
    if depth < camera_height:
        raise DistanceEstimateException(
            f"Depth {depth:.6g} is smaller than camera height {camera_height:.6g}."
        )
    return (depth**2 - camera_height**2) ** 0.5


def estimate_uncertainty(params, focal_length, baseline, disparity, depth):
    disparity_error = params.pixelErrorPx
    lower_disparity = disparity + disparity_error
    upper_disparity = disparity - disparity_error

    if upper_disparity <= 0:
        raise DistanceEstimateException("Disparity is too small for the configured pixel-error model.")

    depth_low = focal_length * baseline / lower_disparity
    depth_high = focal_length * baseline / upper_disparity
    depth_uncertainty = max(abs(depth - depth_low), abs(depth_high - depth))

    return depth_low, depth_high, depth_uncertainty


def classify_quality(params, disparity, vertical_offset, relative_uncertainty):
    if (
        vertical_offset <= params.highQualityMaxVerticalOffsetPx
        and disparity >= params.highQualityMinDisparityPx
        and relative_uncertainty <= params.highQualityMaxRelUncertainty
    ):
        return "High", "OK", "Accepted"

    if (
        vertical_offset <= params.mediumQualityMaxVerticalOffsetPx
        and disparity >= params.mediumQualityMinDisparityPx
        and relative_uncertainty <= params.mediumQualityMaxRelUncertainty
    ):
        return "Medium", "OK", "Accepted"

    return "Low", "Warning", "Accepted with elevated uncertainty."


def build_measurement(params, calibration, label, left_roi, right_roi):
    left_x, left_y = extract_measurement_point(label, left_roi, "Left")
    right_x, right_y = extract_measurement_point(label, right_roi, "Right")
    disparity = calculate_disparity(params, left_x, right_x)
    vertical_offset = abs(left_y - right_y)

    if vertical_offset > params.maxVerticalOffsetPx:
        raise DistanceEstimateException(
            f"Vertical offset {vertical_offset:.6g} px exceeds the maximum of {params.maxVerticalOffsetPx:.6g} px."
        )

    depth = estimate_depth(calibration.focal_length, calibration.baseline, disparity)
    ground_distance = calculate_ground_distance(calibration.camera_height, depth)
    depth_low, depth_high, depth_uncertainty = estimate_uncertainty(
        params, calibration.focal_length, calibration.baseline, disparity, depth
    )
    relative_uncertainty = depth_uncertainty / depth if depth != 0 else math.inf
    quality, status, message = classify_quality(params, disparity, vertical_offset, relative_uncertainty)

    return {
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
