import cv2 as cv
import numpy as np
import glob

chessboard_size = (6,6)

def find_chessboards(image_files):
    detected_images = []
    for file in image_files:
        # Load the image
        img = cv.imread(file)
        
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        
        ret1,gray = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)


        # Find the chessboard corners
        # ret, corners = cv.findChessboardCorners(gray, chessboard_size, cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK)
        ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)

        if ret:
            detected_images.append(file)
            # Draw and display the corners
            img = cv.drawChessboardCorners(gray, chessboard_size, corners, ret)
            cv.imshow('Chessboard Detection', img)
            cv.waitKey(0)

    cv.destroyAllWindows()
    return detected_images

file_path = "HenryFiles/Camera Calibration/left images/"
# file_path = "HenryFiles/Camera Calibration/right images/"


image_files = glob.glob(file_path + "*.png")

found_boards = find_chessboards(image_files)

print(len(found_boards), "Chessboards found:")
for image in found_boards:
    print(image)