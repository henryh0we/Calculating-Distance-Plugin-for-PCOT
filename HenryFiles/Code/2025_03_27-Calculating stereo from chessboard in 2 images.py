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

non_left_images = glob.glob(os.path.join('HenryFiles\Camera Calibration\left images', '*.png'))
non_right_images = glob.glob(os.path.join('HenryFiles\Camera Calibration\right images', '*.png'))

def calibrate_duo_image(left_images, right_images):


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

    cv.destroyAllWindows()
    return objpoints, imgpoints_left, imgpoints_right

def calibrate_non_duo(images):
    count = 0
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    # List storing the camera calibration matrices
    camera_mats = []
    camera_dists = []

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
            imgpoints.append(corners)
    
            # Draw and display the corners
            cv.drawChessboardCorners(img, chessboard_size, corners2, ret)
            # cv.imshow('Original', img)
            # cv.waitKey(500)

            # Calibrate the camera
            # This is achieved by comparing the placement of the chessboard corners in the image
            # to those of the real world.
            # The discrepency between the two is used to calculate the camera matrix
            ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
            
            # Add the camera matrix to a list
            camera_mats.append(mtx)
            camera_dists.append(dist)

            # Get the height and width of the image
            h,  w = img.shape[:2]

            # getOptimalNewCameraMatrix creates a matrix which is specifically useful for 
            # undistorting the image.
            newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
            
            # Undistorting the image
            dst = cv.undistort(img, mtx, dist, None, newcameramtx)

            # Crops the image
            x, y, w, h = roi
            dst = dst[y:y+h, x:x+w]

            # Shows the image
            # cv.imshow('Result', dst)
            # cv.waitKey(500)
            
            count += 1
            print('[{0}/{1}]'.format(count, len(images)))
            

    cv.destroyAllWindows()

    # # Generate the average camera matrix
    # average_camera_matrix = np.mean(np.array(camera_mats), axis=0)
    # # print(average_camera_matrix)

    # average_camera_dist = np.mean(np.array(camera_dists), axis=0)
    # return average_camera_matrix, average_camera_dist

    return camera_mats, camera_dists

if os.path.exists('camera_data.json'):
    # with open('camera_data.txt', 'r') as file:
    #     # file.readline()
    #     mtx_left = np.loadtxt(file, max_rows=3)

    #     dist_left = np.loadtxt(file, skiprows=4, max_rows=5)

    #     mtx_right = np.loadtxt(file, skiprows=9, max_rows=12)

    #     dist_right = np.loadtxt(file, skiprows=13, max_rows=18)
    with open('camera_data.json', 'r') as file:
        data = json.load(file)

    mtx_left = np.array(data['mtx_left'])
    dist_left = np.array(data['dist_left']).reshape(-1,1)

    mtx_right = np.array(data['mtx_right'])
    dist_right = np.array(data['dist_right']).reshape(-1,1)

    objpoints = [np.array(obj, dtype=np.float32) for obj in data['objpoints']]
    imgpoints_left = [np.array(img, dtype=np.float32) for img in data['imgpoints_left']]
    imgpoints_right = [np.array(img, dtype=np.float32) for img in data['imgpoints_right']]

    print(mtx_left)
    print(dist_left)
    print(mtx_right)
    print(dist_right)

    assert mtx_left.shape == (3, 3), "mtx_left shape is incorrect"
    assert dist_left.shape[0] in [4, 5], "dist_left shape is incorrect"
    assert mtx_right.shape == (3, 3), "mtx_right shape is incorrect"
    assert dist_right.shape[0] in [4, 5], "dist_right shape is incorrect"

else:
    objpoints, imgpoints_left, imgpoints_right = calibrate_duo_image(duo_left_images, duo_right_images)

    # Calibrating camera from image pairs which both contain chessboards
    ret_left, mtx_left, dist_left, rvecs_left, tvecs_left = cv.calibrateCamera(
        objpoints, imgpoints_left, img_size, None, None)
    ret_right, mtx_right, dist_right, rvecs_right, tvecs_right = cv.calibrateCamera(
        objpoints, imgpoints_right, img_size, None, None)

    L_cm, L_cd = calibrate_non_duo(non_left_images)
    R_cm, R_cd = calibrate_non_duo(non_right_images)

    # Append the additional mtx to the list
    L_cm.append(mtx_left)
    L_cd.append(dist_left)

    R_cm.append(mtx_right)
    R_cd.append(dist_right)

    # Generate the average camera matrix
    mtx_left = np.mean(np.array(L_cm), axis=0)
    dist_left = np.mean(np.array(L_cd), axis=0)

    mtx_right = np.mean(np.array(R_cm), axis=0)
    dist_right = np.mean(np.array(R_cd), axis=0)

    data = {
    "mtx_left": mtx_left.tolist(),
    "dist_left": dist_left.tolist(),
    "mtx_right": mtx_right.tolist(),
    "dist_right": dist_right.tolist(),
    "objpoints": [obj.tolist() for obj in objpoints],
    "imgpoints_left": [img.tolist() for img in imgpoints_left],
    "imgpoints_right": [img.tolist() for img in imgpoints_right]
    }

    # Save the data to a file
    # with open('camera_data.txt', 'w') as file:
    #     # file.write("Left Camera Matrix:\n")
    #     np.savetxt(file, mtx_left, newline="\n")
    #     # file.write("\nLeft Camera Distortion Coefficients:\n")
    #     np.savetxt(file, dist_left, newline="\n")
    #     # file.write("\n\nRight Camera Matrix:\n")
    #     np.savetxt(file, mtx_right, newline="\n")
    #     # file.write("\nRight Camera Distortion Coefficients:\n")
    #     np.savetxt(file, dist_right, newline="\n")

    with open('camera_data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Stereo calibration
flags = 0
flags |= cv.CALIB_FIX_INTRINSIC
# criteria_stereo = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

ret_stereo, mtx_left, dist_left, mtx_right, dist_right, R, T, E, F = cv.stereoCalibrate(
    objpoints, imgpoints_left, imgpoints_right, 
    mtx_left, dist_left, mtx_right, dist_right, 
    img_size, criteria=criteria, flags=flags)

# Compute rectification transforms
rect_scale = 1  # Scaling factor: 0=zoomed out, 1=cropped
rect_left, rect_right, proj_left, proj_right, Q, roi_left, roi_right = cv.stereoRectify(
    mtx_left, dist_left, mtx_right, dist_right, img_size, 
    R, T, flags=cv.CALIB_ZERO_DISPARITY, alpha=rect_scale)

# Compute mapping for rectification
map_left_x, map_left_y = cv.initUndistortRectifyMap(
    mtx_left, dist_left, rect_left, proj_left, img_size, cv.CV_32FC1)
map_right_x, map_right_y = cv.initUndistortRectifyMap(
    mtx_right, dist_right, rect_right, proj_right, img_size, cv.CV_32FC1)


# idx = 2
# # Example: Rectify a pair of images
# left_img = cv.imread(duo_left_images[idx])
# right_img = cv.imread(duo_right_images[idx])

left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

# left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_LWAC01_T00_P00_BS.png')
# right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_RWAC01_T00_P00_BS.png')

left_rectified = cv.remap(left_img, map_left_x, map_left_y, cv.INTER_LINEAR)
right_rectified = cv.remap(right_img, map_right_x, map_right_y, cv.INTER_LINEAR)

# Display rectified images
combined_rectified = np.hstack((left_rectified, right_rectified))

# Draw horizontal lines on combined image
num_lines = 80
interval = combined_rectified.shape[0] // num_lines
for i in range(0, combined_rectified.shape[0], interval):
    cv.line(combined_rectified, (0, i), (combined_rectified.shape[1], i), (0, 255, 0), 1)

cv.namedWindow('Rectified Images', cv.WINDOW_NORMAL)
cv.imshow('Rectified Images', combined_rectified)
cv.waitKey(0)
cv.destroyAllWindows()