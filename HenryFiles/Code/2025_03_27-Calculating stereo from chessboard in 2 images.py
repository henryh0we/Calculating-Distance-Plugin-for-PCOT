import cv2 as cv
import numpy as np
import glob
import os
import json

# Chessboard parameters
chessboard_size = (9, 6)  # Number of inner corners
square_size = 1.0  # Size of a square in your preferred unit
img_size = (1024, 1024)

# Prepare object points (0,0,0), (1,0,0), (2,0,0) ... (8,5,0)
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
objp *= square_size  # Scale by square size

criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Arrays to store object points and image points
objpoints = []  # 3D points in real world space
imgpoints_left = []  # 2D points in left image plane
imgpoints_right = []  # 2D points in right image plane

# Get image pairs 
duo_left_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/in both images/left images duo', '*.png'))
duo_right_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/in both images/right images duo', '*.png'))

non_left_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/left images', '*.png'))
non_right_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/right images', '*.png'))

def calibrate_duo_image(left_images, right_images):
    count = 0

    for left_img_path, right_img_path in zip(left_images, right_images):
        left_img = cv.imread(left_img_path)
        right_img = cv.imread(right_img_path)
        
        gray_left = cv.cvtColor(left_img, cv.COLOR_BGR2GRAY)
        gray_right = cv.cvtColor(right_img, cv.COLOR_BGR2GRAY)
        
        # Find chessboard corners
        ret_left, corners_left = cv.findChessboardCorners(gray_left, chessboard_size, None)
        ret_right, corners_right = cv.findChessboardCorners(gray_right, chessboard_size, None)
        
        if ret_left and ret_right:
            # Refine corner positions
            corners_left = cv.cornerSubPix(gray_left, corners_left, (11, 11), (-1, -1), criteria)
            corners_right = cv.cornerSubPix(gray_right, corners_right, (11, 11), (-1, -1), criteria)
            
            # Store the points
            objpoints.append(objp)
            imgpoints_left.append(corners_left)
            imgpoints_right.append(corners_right)
            
            # Draw and display the corners (optional)
            cv.drawChessboardCorners(left_img, chessboard_size, corners_left, ret_left)
            cv.drawChessboardCorners(right_img, chessboard_size, corners_right, ret_right)
            # cv.imshow('Left Corners', left_img)
            # cv.imshow('Right Corners', right_img)
            # cv.waitKey(1)

            count += 1
            print('[{0}/{1}]'.format(count, len(left_images)))
    cv.destroyAllWindows()
    return objpoints, imgpoints_left, imgpoints_right

def old_calibrate_non_duo(images):
    count = 0
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    # List storing the camera calibration matrices
    camera_mats = []
    camera_dists = []

    if not images:
        raise ValueError("No images found")

    # Loop through the images
    for fname in images:
        # Load the image
        img = cv.imread(fname)
        #  Convert to grayscale
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
        if ret == True:

            # If found, add object points, these are the points (corners of the chessboard squares)
            # in real world space
            objpoints.append(objp)

            # Refine the corner location by subpixel accuracy
            # This works by taking each corner, taking a small window around it
            # checking the gradient of brightness of the window
            # the subpixel will then be represented by a floating point average, 
            # rather than a set pixel position.
            corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            # Add these new image points to imgpoints
            imgpoints.append(corners2)
    
            # Draw and display the corners
            # cv.drawChessboardCorners(img, chessboard_size, corners2, ret)
            # cv.imshow('Original', img)
            # cv.waitKey(500)

            count += 1
            print('[{0}/{1}]'.format(count, len(images)))
            
            # Calibrate the camera
            # This is achieved by comparing the placement of the chessboard corners in the image
            # to those of the real world.
            # The discrepency between the two is used to calculate the camera matrix
    
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, img_size, None, None)
    
    # Add the camera matrix to a list
    camera_mats.append(mtx)
    camera_dists.append(dist)

            # Get the height and width of the image
            # h,  w = img.shape[:2]

            # getOptimalNewCameraMatrix creates a matrix which is specifically useful for 
            # undistorting the image.
            # newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
            
            # # Undistorting the image
            # dst = cv.undistort(img, mtx, dist, None, newcameramtx)

            # # Crops the image
            # x, y, w, h = roi
            # dst = dst[y:y+h, x:x+w]

            # Shows the image
            # cv.imshow('Result', dst)
            # cv.waitKey(500)
            

    # cv.destroyAllWindows()

    # # Generate the average camera matrix
    # average_camera_matrix = np.mean(np.array(camera_mats), axis=0)
    # # print(average_camera_matrix)

    # average_camera_dist = np.mean(np.array(camera_dists), axis=0)
    # return average_camera_matrix, average_camera_dist

    return camera_mats, camera_dists

def calibrate_non_duo(images):
    count = 0
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    # List storing the camera calibration matrices
    camera_mats = []
    camera_dists = []

    if not images:
        raise ValueError("No images found")

    # Loop through the images
    for fname in images:
        # Load the image
        img = cv.imread(fname)
        #  Convert to grayscale
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
        if ret == True:

            # If found, add object points, these are the points (corners of the chessboard squares)
            # in real world space
            objpoints.append(objp)

            # Refine the corner location by subpixel accuracy
            # This works by taking each corner, taking a small window around it
            # checking the gradient of brightness of the window
            # the subpixel will then be represented by a floating point average, 
            # rather than a set pixel position.
            corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            # Add these new image points to imgpoints
            imgpoints.append(corners2)
    
            # Draw and display the corners
            # cv.drawChessboardCorners(img, chessboard_size, corners2, ret)
            # cv.imshow('Original', img)
            # cv.waitKey(500)

            count += 1
            print('[{0}/{1}]'.format(count, len(images)))
            # print(gray.shape[::-1])
            
            # Calibrate the camera
            # This is achieved by comparing the placement of the chessboard corners in the image
            # to those of the real world.
            # The discrepency between the two is used to calculate the camera matrix
    
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, img_size, None, None)

    # Add the camera matrix to a list
    camera_mats.append(mtx)
    camera_dists.append(dist)

    return camera_mats, camera_dists

camera_data_file_path = 'HenryFiles/camera_data_filler.json'

if os.path.exists(camera_data_file_path):

    with open(camera_data_file_path, 'r') as file:
        data = json.load(file)

    mtx_left = np.array(data['mtx_left'])
    dist_left = np.array(data['dist_left']).reshape(-1,1)
    rect_left = np.array(data['rect_left'])
    proj_left = np.array(data['proj_left'])

    mtx_right = np.array(data['mtx_right'])
    dist_right = np.array(data['dist_right']).reshape(-1,1)
    rect_right = np.array(data['rect_right'])
    proj_right = np.array(data['proj_right'])

else:

    objpoints, imgpoints_left, imgpoints_right = calibrate_duo_image(duo_left_images, duo_right_images)

    print("Successfully calibrated the camera from image pairs which both contain chessboards")

    # Calibrating camera from image pairs which both contain chessboards
    ret_left, mtx_left, dist_left, rvecs_left, tvecs_left = cv.calibrateCamera(
        objpoints, imgpoints_left, img_size, None, None)
    ret_right, mtx_right, dist_right, rvecs_right, tvecs_right = cv.calibrateCamera(
        objpoints, imgpoints_right, img_size, None, None)

    L_cm, L_cd = calibrate_non_duo(non_left_images)
    # R_cm, R_cd = calibrate_non_duo(non_right_images)

    print("Successfully calibrated the camera from images of the left and right cameras")

    # Append the additional mtx to the list
    L_cm.append(mtx_left)
    L_cd.append(dist_left)

    print("Left camera matrices:")
    for i, cm in enumerate(L_cm):
        print(f"{i}:")
        print(cm)
    print("Left camera distortions:")
    for i, cd in enumerate(L_cd):
        print(f"{i}:")
        print(cd)

    # R_cm.append(mtx_right)
    # R_cd.append(dist_right)

    # print("Right camera matrices:")
    # for i, cm in enumerate(R_cm):
    #     print(f"{i}:")
    #     print(cm)
    # print("Right camera distortions:")
    # for i, cd in enumerate(R_cd):
    #     print(f"{i}:")
    #     print(cd)

    # Generate the average camera matrix
    mtx_left = np.mean(np.array(L_cm), axis=0)
    dist_left = np.mean(np.array(L_cd), axis=0)

    # mtx_right = np.mean(np.array(R_cm), axis=0)
    # dist_right = np.mean(np.array(R_cd), axis=0)


    # ===============
    # Testing
    # ===============
    # mtx_test = 1
    # dist_test = 1
    # mtx_left = L_cm[mtx_test]
    # # mtx_left = np.mean(np.array(L_cm), axis=0)
    # dist_left = L_cd[dist_test]
    # dist_left = np.mean (np.array(L_cd), axis=0)

    # mtx_right = R_cm[mtx_test]
    # # mtx_right = np.mean(np.array(R_cm), axis=0)
    # dist_right = R_cd[dist_test]
    # dist_right = np.mean(np.array(R_cd), axis=0)
    # ===============

    print("Successfully generated the average camera matrix")

    # Stereo calibration
    flags = 0
    flags |= cv.CALIB_FIX_INTRINSIC
    # criteria_stereo = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    ret_stereo, mtx_left, dist_left, mtx_right, dist_right, R, T, E, F = cv.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right, 
        mtx_left, dist_left, mtx_right, dist_right, 
        img_size, criteria=criteria, flags=flags)
    
    print("Successfully performed stereo calibration")
    print(R)
    print(T)
    print(E)
    print(F)

    # Compute rectification transforms
    rect_scale = 0.6  # Scaling factor: 0=zoomed out, 1=cropped
    rect_left, rect_right, proj_left, proj_right, Q, roi_left, roi_right = cv.stereoRectify(
        mtx_left, dist_left, mtx_right, dist_right, img_size, 
        R, T, flags=cv.CALIB_ZERO_DISPARITY, alpha=rect_scale)

    print("Successfully computed rectification transforms")

    data = {
        "mtx_left": mtx_left.tolist(),
        "dist_left": dist_left.tolist(),
        "rect_left": rect_left.tolist(),
        "proj_left": proj_left.tolist(),

        "mtx_right": mtx_right.tolist(),
        "dist_right": dist_right.tolist(),
        "rect_right": rect_right.tolist(),
        "proj_right": proj_right.tolist(),

        "R": R.tolist(),
        "T": T.tolist(),
        "E": E.tolist(),
        "F": F.tolist(),
    }

    with open('HenryFiles/camera_data.json', 'w') as file:
        json.dump(data, file, indent=4)

    print("Successfully wrote the camera data to file")

# Compute mapping for rectification
map_left_x, map_left_y = cv.initUndistortRectifyMap(
    mtx_left, dist_left, rect_left, proj_left, img_size, cv.CV_32FC1)
map_right_x, map_right_y = cv.initUndistortRectifyMap(
    mtx_right, dist_right, rect_right, proj_right, img_size, cv.CV_32FC1)

# idx = 2
# # Example: Rectify a pair of images
# left_img = cv.imread(duo_left_images[idx])
# right_img = cv.imread(duo_right_images[idx])

# left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
# right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_LWAC01_T00_P00_BS.png')
right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_RWAC01_T00_P00_BS.png')

left_rectified = cv.remap(left_img, map_left_x, map_left_y, cv.INTER_LINEAR)
right_rectified = cv.remap(right_img, map_right_x, map_right_y, cv.INTER_LINEAR)

# Draw horizontal lines on left and right rectified images
num_lines = 40
interval = left_rectified.shape[0] // num_lines
for i in range(0, left_rectified.shape[0], interval):
    cv.line(left_rectified, (0, i), (left_rectified.shape[1], i), (0, 255, 0), 1)
    cv.line(right_rectified, (0, i), (right_rectified.shape[1], i), (0, 255, 0), 1)

points = []

# Initialize lists to store points
points_left = []
points_right = []

def select_point_left(event, x, y, flags, param):
    global points_left
    if event == cv.EVENT_LBUTTONDOWN:
        if len(points_left) < 1:
            points_left.append((x, y))
            cv.circle(param, (x, y), 5, (0, 255, 0), -1)
            cv.imshow("Left Image", param)
            print(f"Left Image: Point selected at: {x}, {y}")
        if len(points_left) == 1:
            cv.setMouseCallback("Left Image", lambda *args: None)  # Disable further callbacks

def select_point_right(event, x, y, flags, param):
    global points_right
    if event == cv.EVENT_LBUTTONDOWN:
        if len(points_right) < 1:
            points_right.append((x, y))
            cv.circle(param, (x, y), 5, (0, 255, 0), -1)
            cv.imshow("Right Image", param)
            print(f"Right Image: Point selected at: {x}, {y}")
        if len(points_right) == 1:
            cv.setMouseCallback("Right Image", lambda *args: None)  # Disable further callbacks

cv.namedWindow("Left Image", cv.WINDOW_NORMAL)
cv.setMouseCallback("Left Image", select_point_left, left_rectified)
cv.resizeWindow('Left Image', 600, 600)
cv.setWindowProperty('Left Image', cv.WND_PROP_ASPECT_RATIO, cv.WINDOW_KEEPRATIO)

cv.namedWindow("Right Image", cv.WINDOW_NORMAL)
cv.setMouseCallback("Right Image", select_point_right, right_rectified)
cv.resizeWindow('Right Image', 600, 600)
cv.setWindowProperty('Right Image', cv.WND_PROP_ASPECT_RATIO, cv.WINDOW_KEEPRATIO)

cv.moveWindow('Left Image', 100, 100)  # Position of the left image window
cv.moveWindow('Right Image', 100 + 600, 100)  # Position of the right image window

while True:
    # cv.imshow("Image", combined_rectified)
    cv.imshow("Left Image", left_rectified)
    cv.imshow("Right Image", right_rectified)
    if cv.waitKey(1) & 0xFF == 27 or ((len(points_left) == 1) and (len(points_right) == 1)):  # ESC key or 2 points selected
        break

cv.destroyAllWindows()

if ((len(points_left) == 1) and (len(points_right) == 1)):
    point_left = points_left[0] # ( x , y )
    point_right = points_right[0] # ( x , y )

    disparity = point_right[0] - point_left[0]

    disparity = abs(disparity) #  Always non-negative

    print("disparity: ", disparity)

    # Currently works using estimations made from OpenCV.
    # Need to make adjustments to code to instead use new code.
    # Thus using real-world data

    # ==================
    # Real-world data
    # ==================

    focal_length_mm = 12
    image_width_pixels = 1024

    diagonal_length = 8 # diagonal size of the now-square sensor in mm
    side_length = 5.657 # side length of the now-square sensor in mm

    # INCORRECT
    # # perhaps I misinterpreted the size of the image? so its 8cm, 
    # # therefore diagonal length is 80mm
    # diagonal_length = 80
    # side_length = 56.57

    sensor_width_mm = side_length

    focal_length_pixels = (focal_length_mm / sensor_width_mm) * image_width_pixels

    focal_length = focal_length_pixels

    print("focal_length: ", focal_length)

    baseline = 0.5  # Distance in meters
    # baseline = 500 # Distance in mm

    depth = (focal_length * baseline) / disparity

    print("depth: ", depth)

    aupe_height = 1.094

    approximate_ground_distance = np.sqrt(depth**2 - aupe_height**2)

    print("approximate_ground_distance: ", approximate_ground_distance)
