import numpy as np
import cv2 as cv
import glob
import os

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

def calibration(images):
	# Arrays to store object points and image points from all the images.
	objpoints = [] # 3d point in real world space
	imgpoints = [] # 2d points in image plane.

	# images = glob.glob('*.jpg')
	camera_mats = []
	for fname in images:
		img = cv.imread(fname)
		if img is None:
			print(f"Image {fname} not found")
			continue
		# Convert to grayscale
		gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
  
		# Find the chess board corners
		ret, corners = cv.findChessboardCorners(gray, (9,6), None)
  
		# # Try different flags in cv.findChessboardCorners
		# ret, corners = cv.findChessboardCorners(gray, (7, 6), cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK)  
		print(f"Chessboard detection for {fname}: {ret}")
		# If found, add object points, image points (after refining them)
		if ret == True:
			objpoints.append(objp)
			corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
			imgpoints.append(corners)
			# Draw and display the corners
			cv.drawChessboardCorners(img, (7,6), corners2, ret)
			cv.imshow('img', img)
			cv.waitKey(500)
			ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
			camera_mats.append(mtx)
			h,  w = img.shape[:2]
			newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
			dst = cv.undistort(img, mtx, dist, None, newcameramtx)
			x, y, w, h = roi
			dst = dst[y:y+h, x:x+w]
			cv.imshow('img', dst)
			cv.waitKey(500)
	cv.destroyAllWindows()
	print("====== Camera Matrices ======")
	print(len(camera_mats))
	print(np.mean(np.array(camera_mats), axis=0))
 
tut_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/Tutorial/Tutorial images', '*.jpg'))
print(len(tut_images))

left_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/left images', '*.png'))
print(len(left_images))

right_images = glob.glob(os.path.join('HenryFiles/Camera Calibration/right images', '*.png'))
print(len(right_images))



# calibration(tut_images)

calibration(left_images)

# calibration(right_images)
