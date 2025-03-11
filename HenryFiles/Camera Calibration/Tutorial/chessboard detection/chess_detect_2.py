import cv2 as cv
import numpy as np
import glob

chessboard_size = (9, 6)

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


# # Load the image
# img = cv.imread("kFM1C.jpg")

def find_chessboard_1(img):
    # Color-segmentation to get binary mask
    lwr = np.array([0, 0, 143])
    upr = np.array([179, 61, 252])
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    msk = cv.inRange(hsv, lwr, upr)

    # Extract chess-board
    krn = cv.getStructuringElement(cv.MORPH_RECT, (50, 30))
    dlt = cv.dilate(msk, krn, iterations=5)
    res = 255 - cv.bitwise_and(dlt, msk)

    # Displaying each step
    # cv.imshow("Original", img)
    # cv.imshow("HSV Mask", msk)
    # cv.imshow("Dilated", dlt)
    cv.imshow("Result", res)
    cv.waitKey(10)

    # Displaying chess-board features
    res = np.uint8(res)
   
    # ret, corners = cv.findChessboardCorners(res, chessboard_size,
    #                                         flags=cv.CALIB_CB_ADAPTIVE_THRESH +
    #                                             cv.CALIB_CB_FAST_CHECK +
    #                                             cv.CALIB_CB_NORMALIZE_IMAGE
    #                                         # None
    #                                             )
    
    ret, corners = cv.findChessboardCornersSB(res, chessboard_size,
                                            flags=
                                            # cv.CALIB_CB_ADAPTIVE_THRESH +
                                            #     cv.CALIB_CB_FAST_CHECK +
                                            #     cv.CALIB_CB_NORMALIZE_IMAGE
                                            # None
                                            cv.CALIB_CB_EXHAUSTIVE
                                                )
    
    if ret:
        print(corners)
        fnl = cv.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv.imshow("fnl", fnl)
        cv.waitKey(0)
    else:
        print("No Checkerboard Found")

image_files = glob.glob("HenryFiles/Camera Calibration/left images/*.png")

for file in image_files:
    img = cv.imread(file)
    find_chessboard_1(img)
# found_boards = find_chessboards(image_files)

# print("Chessboards found:")
# for image in found_boards:
#     print(image)