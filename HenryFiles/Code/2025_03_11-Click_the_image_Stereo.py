import numpy as np
import cv2 as cv
import glob
import os
import math

# from Camera_Calibration.Tutorial.opencv_calibrate_camera_function import calibrate_camera



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

left_matrix = np.array([
    [1.93479347e+03, 0.00000000e+00, 4.94465690e+02], 
    [0.00000000e+00, 1.92439346e+03, 4.16565813e+02], 
    [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
    ], )

left_dist = np.array([
    [-4.92069166e-02, -8.97949590e-01, -1.33405070e-02, -4.44237271e-03, 2.39096813e+01]
    ], )

f_x_left = left_matrix[0][0]
f_y_left = left_matrix[1][1]
c_x_left = left_matrix[0][2]
c_y_left = left_matrix[1][2]

right_matrix = np.array([
    [1.93490723e+03, 0.00000000e+00, 5.26855083e+02],
    [0.00000000e+00, 1.92810886e+03, 5.05013225e+02],
    [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
 ], )

right_dist = np.array([
    [-1.49167371e-01, 1.24309868e+00, -4.14581848e-04, -3.06654869e-03, -7.74292242e+00]
    ], )

f_x_right = right_matrix[0][0]
f_y_right = right_matrix[1][1]
c_x_right = right_matrix[0][2]
c_y_right = right_matrix[1][2]

focal_length_mm = 12
sensor_width_mm = 8.8
image_width_pixels = 1024
img_size = (1024, 1024)


camera_rotation = 2.8 # Inwards rotation of the cameras in degrees
total_camera_rotation = camera_rotation * 2
tcr_radians = np.deg2rad(total_camera_rotation)
# tcr_radians = np.deg2rad(camera_rotation)
print("tcr_radians: ", tcr_radians)

R_left = np.array([
    [np.cos(tcr_radians), 0, np.sin(tcr_radians)],
    [0, 1, 0],
    [-np.sin(tcr_radians), 0, np.cos(tcr_radians)]
], dtype=np.float32)

R_right = np.array([
    [np.cos(-tcr_radians), 0, np.sin(-tcr_radians)],
    [0, 1, 0],
    [-np.sin(-tcr_radians), 0, np.cos(-tcr_radians)]
], dtype=np.float32)

R = np.matmul(R_right, R_left.T)
# R = R_right @ np.linalg.inv(R_left)

# R = np.array([
#     [math.cos(tcr_radians), 0, math.sin(tcr_radians)],
#     [0, 1, 0],
#     [-math.sin(tcr_radians), 0, math.cos(tcr_radians)]
# ])

baseline = 500  # Distance between the two cameras in mm
toe_in_angle = baseline * math.tan(tcr_radians)
print("toe in: ", toe_in_angle)

T = np.array([
    [baseline], [0], 
    # [toe_in_angle]
    [0]
], dtype=np.float32)

# , dtype=np.float32

# R_vec, _ = cv.Rodrigues(R)
# print(left_matrix)
# print(left_dist)
# print(right_matrix)
# print(right_dist)

# print(R)
# print(T)

# left_matrix = np.float32(left_matrix)
# left_dist = np.float32(left_dist)
# right_matrix = np.float32(right_matrix)
# right_dist = np.float32(right_dist)
# R = np.float32(R)
# T = np.float32(T)

left_matrix = np.asarray(left_matrix, dtype=np.float64)
left_dist = np.asarray(left_dist, dtype=np.float64)
right_matrix = np.asarray(right_matrix, dtype=np.float64)
right_dist = np.asarray(right_dist, dtype=np.float64)
R = np.asarray(R, dtype=np.float64)
T = np.asarray(T, dtype=np.float64)

img_size = (int(img_size[0]), int(img_size[1]))


print(left_matrix)
print(left_dist)
print(right_matrix)
print(right_dist)

print(R)
print(T)

print("left_matrix:", left_matrix.dtype)
print("left_dist:", left_dist.dtype)
print("right_matrix:", right_matrix.dtype)
print("right_dist:", right_dist.dtype)
print("R:", R.dtype)
print("T:", T.dtype)

print("left_matrix shape:", left_matrix.shape)
print("left_dist shape:", left_dist.shape)
print("right_matrix shape:", right_matrix.shape)
print("right_dist shape:", right_dist.shape)
print("R shape:", R.shape)
print("T shape:", T.shape)

LR, RR, p1, p2, q, roi1, roi2 = cv.stereoRectify(
    left_matrix, left_dist, 
    right_matrix, right_dist, 
    img_size, 
    R, T)

left_map1, left_map2 = cv.initUndistortRectifyMap(
    left_matrix, left_dist, LR, p1, img_size, cv.CV_32FC1)
right_map1, right_map2 = cv.initUndistortRectifyMap(
    right_matrix, right_dist, RR, p2, img_size, cv.CV_32FC1)

left_rectified = cv.remap(imgL, left_map1, left_map2, cv.INTER_LINEAR)
right_rectified = cv.remap(imgR, right_map1, right_map2, cv.INTER_LINEAR)

combined_image = np.hstack((left_rectified, right_rectified))

# line_color = (0, 255, 0)  
# line_thickness = 1
# num_lines = 20  
# spacing = combined_image.shape[0] // num_lines

# for i in range(0, combined_image.shape[0], spacing):
#     cv.line(combined_image, (0, i), (combined_image.shape[1], i), line_color, line_thickness)

cv.namedWindow("Rectified Images", cv.WINDOW_NORMAL)
cv.resizeWindow("Rectified Images", 1200, 600)
cv.imshow("Rectified Images", combined_image)
cv.waitKey(0)
cv.destroyAllWindows()

# cv.imshow("Left Rectified", left_rectified)
# cv.imshow("Right Rectified", right_rectified)
# cv.waitKey(0)
# cv.destroyAllWindows()

# left_point = None
# right_point = None

# def click_event_left(event, x, y, flags, param):
#     global left_point
#     if event == cv.EVENT_LBUTTONDOWN:
#         left_point = (x, y)
#         cv.circle(imgL, left_point, 5, (255, 0, 0), -1)
#         cv.imshow('Left Image', imgL)

# def click_event_right(event, x, y, flags, param):
#     global right_point
#     if event == cv.EVENT_LBUTTONDOWN:
#         right_point = (x, y)
#         cv.circle(imgR, right_point, 5, (255, 0, 0), -1)
#         cv.imshow('Right Image', imgR)

# # Display images and set mouse callbacks
# cv.imshow('Left Image', imgL)
# cv.imshow('Right Image', imgR)
# cv.setMouseCallback('Left Image', click_event_left)
# cv.setMouseCallback('Right Image', click_event_right)

# cv.waitKey(0)
# cv.destroyAllWindows()

