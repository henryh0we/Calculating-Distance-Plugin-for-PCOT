import numpy as np
import cv2 as cv
import os
# from HenryFiles.Code.2025_03_25-reading_camera_data_from_txt import read_camera_data

type_data = np.float64
camera_rotation = 2.8
baseline = 500 # baseline in mm (distance between two cameras)
img_size = (1024,1024)

def read_camera_data():
    """
    Read the camera calibration data from the text file 'camera_data.txt'
    and return the camera matrices and distortion coefficients.
    """
    # Read the entire file and split into lines
    with open('camera_data.txt', 'r') as file:
        lines = file.readlines()

    # Remove any empty lines and strip newline characters
    lines = [line.strip() for line in lines if line.strip() != '']

    # Parse Left Camera Matrix (Lines 0 to 2)
    left_camera_matrix = [list(map(float, lines[i].split())) for i in range(3)]
    left_camera_matrix = np.array(left_camera_matrix)

    # Parse Left Camera Distortion Coefficients (Line 3)
    left_camera_dist = list(map(float, lines[3].split()))
    left_camera_dist = np.array(left_camera_dist).reshape(-1, 1)  # Reshape

    # Parse Right Camera Matrix (Lines 4 to 6)
    right_camera_matrix = [list(map(float, lines[i].split())) for i in range(4, 7)]
    right_camera_matrix = np.array(right_camera_matrix)

    # Parse Right Camera Distortion Coefficients (Line 7)
    right_camera_dist = list(map(float, lines[7].split()))
    right_camera_dist = np.array(right_camera_dist).reshape(-1, 1)  # Reshape

    # Return the results
    return left_camera_matrix, left_camera_dist, right_camera_matrix, right_camera_dist

# Load the images
imgL_path = r'AUPE Images/distance/pctset-1m-8bit/distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png'
imgR_path = r'AUPE Images/distance/pctset-1m-8bit/distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png'

# Check if the files exist
if not os.path.exists(imgL_path) or not os.path.exists(imgR_path):
    print("One or both image files not found. Please check the file paths.")
    exit()

imgL = cv.imread(imgL_path, 0)
imgR = cv.imread(imgR_path, 0)

if imgL is None or imgR is None:
    print("One or both images could not be loaded. Please check the file paths and file integrity.")
    exit()

# Camera parameters
left_matrix, left_dist, right_matrix, right_dist = read_camera_data()
# print(left_matrix)
# print(left_dist)
# print(right_matrix)
# print(right_dist)

# Rotation
# So we know that both cameras are pointed in by 2.8 degrees

rot_rad = np.deg2rad(camera_rotation)

R_right = np.array([0, rot_rad, 0])

R_left = np.array([0, -rot_rad, 0])

# This now represents the rotation of both cameras
# as pointing inwards. 
# Right to the left by 2.8 degrees
# Left to the right by 2.8 degrees

# OpenCV's function for stereoRectify however takes values as 
# relative to the first camera.
# This means that the left camera is positioned at the origin, 
# facing forwards.
# And the right camera is pointed in further, and also slightly further forwards, and pointed inwards.

# Therefore, we need to adjust the rotation of the right camera.

total_rot = rot_rad * 2

R_total = np.array([0, total_rot, 0])
Rot_total_matrix, _ = cv.Rodrigues(R_total)

print("R_total: ", R_total) 
print("R_total_matrix: ")
print(Rot_total_matrix)

# This is the total rotation of both cameras

# Now to calculate the position of the right camera relative to the origin
# (the left camera)
# some trig must be done

adjacent = baseline * np.cos(total_rot)
opposite = baseline * np.sin(total_rot)

print("adjacent: ", adjacent)
print("opposite: ", opposite)

# The adjacent refers to the horizontal distance between the two cameras
# The opposite refers to the forward distance between the two cameras

# therefore adjacent = x
# y stays the same as the cameras are on the same plane
# opposite = z

T = np.array([
    [adjacent], [0], [opposite]
])

# Now we need to generate the camera matrices.
# There are two methods: getOptmalNewCameraMatrix and getDefaultNewCameraMatrix

# getOptimalNewCameraMatrix

left_opt_matrix, lroi = cv.getOptimalNewCameraMatrix(left_matrix, left_dist, img_size, 1, img_size)
right_opt_matrix, rroi = cv.getOptimalNewCameraMatrix(right_matrix, right_dist, img_size, 1, img_size)

# getDefaultNewCameraMatrix

left_def_matrix = cv.getDefaultNewCameraMatrix(left_matrix, img_size)
right_def_matrix = cv.getDefaultNewCameraMatrix(right_matrix, img_size)

# # ======================================
# # USING OPTIMAL MATRIX for stereoRectify
# # ======================================

# opt_LR, opt_RR, opt_p1, opt_p2, opt_q, opt_roi1, opt_roi2 = cv.stereoRectify(
#     left_opt_matrix, left_dist, 
#     right_opt_matrix, right_dist, 
#     img_size, 
#     R_total_matrix, T
# )

# # ======================================
# # USING DEFAULT MATRIX for stereoRectify
# # ======================================

# def_LR, def_RR, def_p1, def_p2, def_q, def_roi1, def_roi2 = cv.stereoRectify(
#     left_def_matrix, left_dist, 
#     right_def_matrix, right_dist, 
#     img_size, 
#     R_total_matrix, T
# )

# # ================================================
# # Using OPTIMAL MATRIX for initUndistortRectifyMap
# # ================================================

# left_opt_map1, left_opt_map2 = cv.initUndistortRectifyMap(
#     left_opt_matrix, left_dist, 
#     opt_LR, 
#     # None,
#     opt_p1, img_size, cv.CV_32FC1)

# right_opt_map1, right_opt_map2 = cv.initUndistortRectifyMap(
#     right_opt_matrix, right_dist, 
#     opt_RR, 
#     # None,
#     opt_p2, img_size, cv.CV_32FC1)

# # ================================================
# # Using DEFAULT MATRIX for initUndistortRectifyMap
# # ================================================

# left_def_map1, left_def_map2 = cv.initUndistortRectifyMap(
#     left_def_matrix, left_dist, 
#     def_LR, 
#     # None,
#     def_p1, img_size, cv.CV_32FC1)

# right_def_map1, right_def_map2 = cv.initUndistortRectifyMap(
#     right_def_matrix, right_dist, 
#     def_RR, 
#     # None,
#     def_p2, img_size, cv.CV_32FC1)

def testing_matrices(L_test_matrix, R_test_matrix):
    LR, RR, p1, p2, q, roi1, roi2 = cv.stereoRectify(
        L_test_matrix, left_dist, 
        R_test_matrix, right_dist, 
        img_size, 
        Rot_total_matrix, T
    )

    left_map1, left_map2 = cv.initUndistortRectifyMap(
        L_test_matrix, left_dist, 
        LR, 
        # None,
        p1, img_size, cv.CV_32FC1)
    right_map1, right_map2 = cv.initUndistortRectifyMap(
        R_test_matrix, right_dist, 
        RR, 
        # None,
        p2, img_size, cv.CV_32FC1)

    left_rectified = cv.remap(imgL, left_map1, left_map2, cv.INTER_LINEAR)
    right_rectified = cv.remap(imgR, right_map1, right_map2, cv.INTER_LINEAR)

    combined_image = np.hstack((left_rectified, right_rectified))

    return combined_image
    # cv.namedWindow("combined", 
    # cv.WINDOW_NORMAL
    # )
    # cv.imshow("combined", combined_image)
    # cv.waitKey(0)
    # cv.destroyAllWindows()

opt = testing_matrices(left_opt_matrix, right_opt_matrix)

default = testing_matrices(left_def_matrix, right_def_matrix)

cv.namedWindow("opt", 
    cv.WINDOW_NORMAL
    )
cv.imshow("opt", opt)

cv.namedWindow("default", 
    cv.WINDOW_NORMAL
    )
cv.imshow("default", default)

cv.waitKey(0)
cv.destroyAllWindows()