import cv2 as cv
import numpy as np
import glob

chessboard_size = (9,6)

def find_chessboards(image_files):
    detected_images = []
    for file in image_files:
        
        # Load the image
        img = cv.imread(file)
        
        # cv.imshow('Image before detection', gray)
        # cv.waitKey(0)

        # Find the chessboard corners
        ret, corners = cv.findChessboardCorners(img, chessboard_size, None)

        if ret:
            detected_images.append(file)
            # Draw and display the corners
            img = cv.drawChessboardCorners(img, chessboard_size, corners, ret)
            cv.imshow('Chessboard Detection', img)
            cv.waitKey(10)

    cv.destroyAllWindows()
    return detected_images

# file_path = "HenryFiles/Camera Calibration/left images/"
file_path = "HenryFiles/Camera Calibration/right images/"


image_files = glob.glob(file_path + "*.png")

found_boards = find_chessboards(image_files)

print(len(found_boards), "Chessboards found:")
for image in found_boards:
    print(image)