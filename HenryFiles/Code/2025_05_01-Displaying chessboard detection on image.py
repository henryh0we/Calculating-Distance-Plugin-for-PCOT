import cv2 as cv

chessboard_size = (9, 6)
file_path = "HenryFiles/Camera Calibration/right images/aupe-cal_c7_RWAC01_T00_P00_BS.png"
def display_chessboard_detection(image_file_path):
    img = cv.imread(image_file_path)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
    if ret:
        img = cv.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv.namedWindow("Chessboard Detection", cv.WINDOW_NORMAL)
        cv.resizeWindow("Chessboard Detection", 700, 700)
        cv.setWindowProperty("Chessboard Detection", cv.WND_PROP_ASPECT_RATIO, cv.WINDOW_KEEPRATIO)
        cv.imshow('Chessboard Detection', img)
        cv.waitKey(0)
        cv.destroyAllWindows()

display_chessboard_detection(file_path)