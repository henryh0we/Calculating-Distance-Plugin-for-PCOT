import numpy as np
import cv2 as cv
import glob
import os

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
    ])

f_x_left = left_matrix[0][0]
f_y_left = left_matrix[1][1]
c_x_left = left_matrix[0][2]
c_y_left = left_matrix[1][2]

right_matrix = np.array([
    [1.93490723e+03, 0.00000000e+00, 5.26855083e+02],
    [0.00000000e+00, 1.92810886e+03, 5.05013225e+02],
    [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
 ])

f_x_right = right_matrix[0][0]
f_y_right = right_matrix[1][1]
c_x_right = right_matrix[0][2]
c_y_right = right_matrix[1][2]

focal_length_mm = 12
sensor_width_mm = 8.8
image_width_pixels = 1024

baseline = 0.5  # Distance between the two cameras in meters

left_point = None
right_point = None

def click_event_left(event, x, y, flags, param):
    global left_point
    if event == cv.EVENT_LBUTTONDOWN:
        left_point = (x, y)
        cv.circle(imgL, left_point, 5, (255, 0, 0), -1)
        cv.imshow('Left Image', imgL)

def click_event_right(event, x, y, flags, param):
    global right_point
    if event == cv.EVENT_LBUTTONDOWN:
        right_point = (x, y)
        cv.circle(imgR, right_point, 5, (255, 0, 0), -1)
        cv.imshow('Right Image', imgR)

# Display images and set mouse callbacks
cv.imshow('Left Image', imgL)
cv.imshow('Right Image', imgR)
cv.setMouseCallback('Left Image', click_event_left)
cv.setMouseCallback('Right Image', click_event_right)

cv.waitKey(0)
cv.destroyAllWindows()

