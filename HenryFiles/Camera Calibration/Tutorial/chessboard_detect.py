import cv2 as cv
import numpy as np
import glob

# Define the chessboard dimensions
chessboard_size = (7, 6)

def sharpen_image(image):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv.filter2D(image, -1, kernel)

def adjust_contrast(image, alpha=1.5, beta=0):
    """
    Adjust the contrast of the image.
    :param image: input image
    :param alpha: contrast control (1.0-3.0)
    :param beta: brightness control (0-100)
    :return: contrast adjusted image
    """
    return cv.convertScaleAbs(image, alpha=alpha, beta=beta)

def find_chessboards(image_files):
    detected_images = []
    for file in image_files:
        # Load the image
        img = cv.imread(file)
        # gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        gray = img.copy()
        
        gray = adjust_contrast(gray)
        
        gray = cv.GaussianBlur(gray, (7, 7), 0)
        
        # gray = sharpen_image(gray)

        # Find the chessboard corners
        # ret, corners = cv.findChessboardCorners(gray, chessboard_size, cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK)
        ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)

        if ret:
            detected_images.append(file)
            # Draw and display the corners
            img = cv.drawChessboardCorners(gray, chessboard_size, corners, ret)
            cv.imshow('Chessboard Detection', img)
            cv.waitKey(10)

    cv.destroyAllWindows()
    return detected_images

file_path = "HenryFiles/Camera Calibration/right images/"

# Get the list of PNG files in the directory
image_files = glob.glob(file_path + "*.png")
found_boards = find_chessboards(image_files)

print(len(found_boards), "Chessboards found:")
for image in found_boards:
    print(image)

