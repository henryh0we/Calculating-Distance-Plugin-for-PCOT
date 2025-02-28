import cv2 as cv
import numpy as np
import glob

chessboard_size = (7, 6)

def find_chessboards(image_files):
    detected_images = []
    for file in image_files:
        img = cv.imread(file)
        if img is None:
            print(f"Failed to load image: {file}")
            continue

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        
        # Try multiple preprocessing techniques
        preprocessed_images = [
            gray,
            cv.GaussianBlur(gray, (5, 5), 0),
            cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2),
            cv.equalizeHist(gray)
        ]

        found = False
        for processed in preprocessed_images:
            try:
                ret, corners = cv.findChessboardCorners(processed, chessboard_size, 
                    cv.CALIB_CB_ADAPTIVE_THRESH + 
                    cv.CALIB_CB_NORMALIZE_IMAGE + 
                    cv.CALIB_CB_FAST_CHECK)
                
                if ret:
                    detected_images.append(file)
                    img = cv.drawChessboardCorners(img, chessboard_size, corners, ret)
                    cv.imshow('Chessboard Detection', img)
                    cv.waitKey(15)
                    found = True
                    break
            except cv.error as e:
                print(f"OpenCV error processing {file}: {str(e)}")

        if not found:
            print(f"Failed to detect chessboard in {file}")

    cv.destroyAllWindows()
    return detected_images

image_files = glob.glob("HenryFiles/Camera Calibration/right images/*.png")
found_boards = find_chessboards(image_files)

print("Chessboards found:")
for image in found_boards:
    print(image)