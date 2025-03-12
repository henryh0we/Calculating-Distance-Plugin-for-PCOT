import numpy as np
import cv2 as cv
import glob
import os

# NOTE:
# Impossible to do unless I collect calibration data 
# that has chessboards in both images simultaneously

chessboard_left = 9
chessboard_right = 6
chessboard_size = (chessboard_left, chessboard_right)

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((chessboard_left*chessboard_right,3), np.float32)
objp[:,:2] = np.mgrid[0:chessboard_left,0:chessboard_right].T.reshape(-1,2)

Limages = glob.glob(os.path.join('Camera Calibration\left images', '*.png'))
Rimages = glob.glob(os.path.join('Camera Calibration/right images', '*.png'))

Timages = glob.glob(os.path.join('HenryFiles/Camera Calibration/Tutorial/Tutorial images', '*.jpg'))

def calibrate_camera(images):
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
            corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
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

    cv.destroyAllWindows()

    # Generate the average camera matrix
    average_camera_matrix = np.mean(np.array(camera_mats), axis=0)
    # print(average_camera_matrix)

    average_camera_dist = np.mean(np.array(camera_dists), axis=0)
    return average_camera_matrix, average_camera_dist, camera_mats, 

l_ACM, l_ACD = calibrate_camera(Limages)

print(l_ACM)
print(l_ACD)

r_ACM, r_ACD = calibrate_camera(Rimages)

print(r_ACM)
print(r_ACD)