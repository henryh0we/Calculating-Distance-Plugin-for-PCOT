import cv2 as cv
import numpy as np
import glob
import os
import json

# Chessboard parameters
chessboard_size = (9, 6)  # Number of inner corners
# square_size = 1.0  # Size of a square 
square_size = 0.02 # size of square in m = 20mm
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

camera_data_file_path = 'pcotplugins/pcotdistanceestimate plugins/mtx_dst_rect_proj.json'
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
            # cv.drawChessboardCorners(left_img, chessboard_size, corners_left, ret_left)
            # cv.drawChessboardCorners(right_img, chessboard_size, corners_right, ret_right)
            # cv.imshow('Left Corners', left_img)
            # cv.imshow('Right Corners', right_img)
            # cv.waitKey(1)

            count += 1
            print('[{0}/{1}]'.format(count, len(left_images)))
    # cv.destroyAllWindows()
    return objpoints, imgpoints_left, imgpoints_right

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

def full_calibration():
    objpoints, imgpoints_left, imgpoints_right = calibrate_duo_image(duo_left_images, duo_right_images)

    print("Successfully calibrated the camera from image pairs which both contain chessboards")

    # Calibrating camera from image pairs which both contain chessboards
    ret_left, mtx_left, dist_left, rvecs_left, tvecs_left = cv.calibrateCamera(
        objpoints, imgpoints_left, img_size, None, None)
    ret_right, mtx_right, dist_right, rvecs_right, tvecs_right = cv.calibrateCamera(
        objpoints, imgpoints_right, img_size, None, None)

    print("Calibrating non duo left")
    L_cm, L_cd = calibrate_non_duo(non_left_images)
    print("Calibrating non duo right")
    R_cm, R_cd = calibrate_non_duo(non_right_images)

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

    R_cm.append(mtx_right)
    R_cd.append(dist_right)

    print("Right camera matrices:")
    for i, cm in enumerate(R_cm):
        print(f"{i}:")
        print(cm)
    print("Right camera distortions:")
    for i, cd in enumerate(R_cd):
        print(f"{i}:")
        print(cd)

    # Generate the average camera matrix
    mtx_left = np.mean(np.array(L_cm), axis=0)
    dist_left = np.mean(np.array(L_cd), axis=0)

    mtx_right = np.mean(np.array(R_cm), axis=0)
    dist_right = np.mean(np.array(R_cd), axis=0)

    print("Successfully generated the average camera matrix")

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


    # Stereo calibration
    flags = 0
    flags |= cv.CALIB_FIX_INTRINSIC
    # criteria_stereo = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    with open('pcotplugins/pcotdistanceestimate plugins/mtx_dst_rect_proj.json', 'r') as file:
        data = json.load(file)
    known_T = np.array(data['known_t'])
    known_R = np.array(data['known_r'])

    ret_stereo, mtx_left, dist_left, mtx_right, dist_right, R, T, E, F = cv.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right, 
        mtx_left, dist_left, mtx_right, dist_right, 
        img_size, known_R, known_T, criteria=criteria, flags=flags)
    
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

    if os.path.exists(camera_data_file_path):
        with open(camera_data_file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    data["mtx_left"] = mtx_left.tolist()
    data["dist_left"] = dist_left.tolist()
    data["rect_left"] = rect_left.tolist()
    data["proj_left"] = proj_left.tolist()

    data["mtx_right"] = mtx_right.tolist()
    data["dist_right"] = dist_right.tolist()
    data["rect_right"] = rect_right.tolist()
    data["proj_right"] = proj_right.tolist()

    data["R"] = R.tolist()
    data["T"] = T.tolist()
    data["E"] = E.tolist()
    data["F"] = F.tolist()

    with open(camera_data_file_path, 'w') as file:
        json.dump(data, file, indent=4)

# camera_data_file_path = 'HenryFiles/camera_data_pre_major_non_duo_change.json'

if not os.path.exists(camera_data_file_path):
    print("Camera_data.json does not exist. Creating...")
    full_calibration()
    print("Successfully wrote the camera data to file")
else:
    response = input("Camera_data.json already exists. Overwrite? (y/n): ")
    if response.lower() == 'y':
        print("Overwriting camera_data.json")
        full_calibration()
        print("Successfully wrote the camera data to file")
    else:
        print("Not overwriting camera_data.json")
