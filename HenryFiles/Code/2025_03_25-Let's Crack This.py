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
    with open('HenryFiles/camera_data.txt', 'r') as file:
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
imgL_path = r'HenryFiles/AUPE Images/distance/pctset-1m-8bit/distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png'
imgR_path = r'HenryFiles/AUPE Images/distance/pctset-1m-8bit/distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png'

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
print("Rot_total_matrix: ")
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

# T = np.array([
#     [adjacent], [0], [opposite]
# ])

T = np.array([
    adjacent, 0, opposite
])

# T = np.array([
#     [500], [0], [0]
# ])

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

# opt = testing_matrices(left_opt_matrix, right_opt_matrix)

# default = testing_matrices(left_def_matrix, right_def_matrix)

# cv.namedWindow("opt", 
#     cv.WINDOW_NORMAL
#     )
# cv.imshow("opt", opt)

# cv.namedWindow("default", 
#     cv.WINDOW_NORMAL
#     )
# cv.imshow("default", default)

# cv.waitKey(0)
# cv.destroyAllWindows()

# look at using cv.fundamentalFromEssential()

def calculate_fundamental_matrix(left_intrinsic, right_intrinsic, R, t):
    """
    Calculate F from calibration parameters
    K1, K2: Camera intrinsic matrices
    R: Rotation matrix between cameras
    t: Translation vector between cameras
    """
    t_x = np.array([
        [0, -t[2], t[1]],
        [t[2], 0, -t[0]],
        [-t[1], t[0], 0]        
    ])

    E = t_x @ R

    F = np.linalg.inv(right_intrinsic) @ E @ np.linalg.inv(left_intrinsic)

    return F


opt_F = calculate_fundamental_matrix(left_opt_matrix, right_opt_matrix, Rot_total_matrix, T)
def_F = calculate_fundamental_matrix(left_def_matrix, right_def_matrix, Rot_total_matrix, T)

print("opt_F: \n", opt_F)
print("def_F: \n", def_F)

# _, l_opt, r_opt = cv.stereoRectifyUncalibrated(
#     imgL, imgR, 
#     opt_F, img_size, 
#     # Rot_total_matrix, T
# )

# _, l_def, r_def = cv.stereoRectifyUncalibrated(
#     imgL, imgR, 
#     def_F, img_size, 
#     # Rot_total_matrix, T
# )

# opt_rec1 = cv.warpPerspective(imgL, l_opt, img_size)
# opt_rec2 = cv.warpPerspective(imgR, r_opt, img_size)

# def_rec1 = cv.warpPerspective(imgL, l_def, img_size)
# def_rec2 = cv.warpPerspective(imgR, r_def, img_size)

# opt_rectified = np.hstack((opt_rec1, opt_rec2))
# def_rectified = np.hstack((def_rec1, def_rec2))

# cv.namedWindow("opt_rectified", 
#     cv.WINDOW_NORMAL
#     )
# cv.imshow("opt_rectified", opt_rectified)

# cv.namedWindow("def_rectified", 
#     cv.WINDOW_NORMAL
#     )
# cv.imshow("def_rectified", def_rectified)

# cv.waitKey(0)
# cv.destroyAllWindows()

# def rectify_images_from_F(img1, img2, F):
#     # Get image dimensions
#     h1, w1 = img1.shape[:2]
#     h2, w2 = img2.shape[:2]
    
#     # Create artificial grid of points
#     step = 20  # Controls density of points
#     x = np.arange(0, w1, step)
#     y = np.arange(0, h1, step)
#     xx, yy = np.meshgrid(x, y)
#     points1 = np.vstack((xx.flatten(), yy.flatten())).T
    
#     # Find corresponding epipolar lines in second image
#     lines2 = cv.computeCorrespondEpilines(points1.reshape(-1, 1, 2), 1, F)
#     lines2 = lines2.reshape(-1, 3)
    
#     # Generate matching points in second image
#     points2 = []
#     for pt1, line in zip(points1, lines2):
#         # Find a point on the epipolar line
#         x0, y0 = 0, int(-line[2] / line[1]) if line[1] != 0 else 0
#         x1, y1 = w2-1, int(-(line[2] + line[0]*(w2-1)) / line[1]) if line[1] != 0 else 0
        
#         # Use the middle of the line segment as the corresponding point
#         points2.append([(x0 + x1) // 2, (y0 + y1) // 2])
    
#     points2 = np.array(points2)
    
#     # Filter out points outside image boundaries
#     valid = (points2[:, 0] >= 0) & (points2[:, 0] < w2) & (points2[:, 1] >= 0) & (points2[:, 1] < h2)
#     points1 = points1[valid]
#     points2 = points2[valid]
    
#     # Compute rectification transforms
#     ret, H1, H2 = cv.stereoRectifyUncalibrated(
#         np.float32(points1).reshape(-1, 1, 2), 
#         np.float32(points2).reshape(-1, 1, 2),
#         F, (w1, h1)
#     )

#     if not ret:
#         print("stereoRectifyUncalibrated failed")
#         return img1, img2, np.eye(3), np.eye(3)
    
#     # Apply rectification transforms
#     rectified1 = cv.warpPerspective(img1, H1, (w1, h1))
#     rectified2 = cv.warpPerspective(img2, H2, (w2, h2))
    
#     return rectified1, rectified2, H1, H2

def rectify_images_from_F(img1, img2, F):
    # Get image dimensions
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
    # Create a grid of points in the first image
    step = 50
    x_range = np.linspace(0, w1-1, num=step)
    y_range = np.linspace(0, h1-1, num=step)
    xx, yy = np.meshgrid(x_range, y_range)
    pts1 = np.float32(np.column_stack((xx.flatten(), yy.flatten())))
    
    # Reshape for OpenCV
    pts1_reshaped = pts1.reshape(-1, 1, 2)
    
    # Find corresponding epipolar lines in the second image
    lines2 = cv.computeCorrespondEpilines(pts1_reshaped, 1, F)
    
    # For each point in the first image, find a point on its epipolar line in the second image
    pts2 = []
    for i, line in enumerate(lines2):
        a, b, c = line[0]
        # Choose x coordinate in the valid range
        x = w2 // 2  # middle of the image
        # Calculate corresponding y
        if abs(b) > 1e-5:  # avoid division by zero
            y = (-a * x - c) / b
            if 0 <= y < h2:
                pts2.append([x, y])
                continue
        
        # If the point isn't valid, try another x
        x = w2 // 4
        if abs(b) > 1e-5:
            y = (-a * x - c) / b
            if 0 <= y < h2:
                pts2.append([x, y])
                continue
                
        # If still not valid, use a default point
        pts2.append([w2//2, h2//2])
    
    pts2 = np.float32(pts2)
    
    # Make sure we have the same number of points
    min_len = min(len(pts1), len(pts2))
    pts1 = pts1[:min_len]
    pts2 = pts2[:min_len]
    
    # Debug print
    print(f"Points shape: pts1 {pts1.shape}, pts2 {pts2.shape}")
    
    # Make sure points are within image boundaries
    pts1 = np.clip(pts1, [0, 0], [w1-1, h1-1])
    pts2 = np.clip(pts2, [0, 0], [w2-1, h2-1])
    
    # Reshape for stereoRectifyUncalibrated
    pts1_reshaped = pts1.reshape(-1, 1, 2)
    pts2_reshaped = pts2.reshape(-1, 1, 2)
    
    try:
        ret, H1, H2 = cv.stereoRectifyUncalibrated(
            pts1_reshaped, pts2_reshaped, F, (w1, h1)
        )
        
        if not ret:
            print("stereoRectifyUncalibrated failed")
            return img1, img2, np.eye(3), np.eye(3)
        
        # Apply rectification transforms
        rectified1 = cv.warpPerspective(img1, H1, (w1, h1))
        rectified2 = cv.warpPerspective(img2, H2, (w2, h2))
        
        return rectified1, rectified2, H1, H2
    
    except cv.error as e:
        print(f"OpenCV error: {e}")
        # Return original images and identity matrices as fallback
        return img1, img2, np.eye(3), np.eye(3)

opt_rectified1, opt_rectified2, opt_H1, opt_H2 = rectify_images_from_F(imgL, imgR, opt_F)
def_rectified1, def_rectified2, def_H1, def_H2 = rectify_images_from_F(imgL, imgR, def_F)

opt_rectified = np.hstack((opt_rectified1, opt_rectified2))
def_rectified = np.hstack((def_rectified1, def_rectified2))

cv.namedWindow("opt_rectified", 
    cv.WINDOW_NORMAL
    )
cv.imshow("opt_rectified", opt_rectified)

cv.namedWindow("def_rectified", 
    cv.WINDOW_NORMAL
    )