import cv2 as cv
import numpy as np
import json

def rectify_and_display_images(imgL_path, imgR_path, camera_file_path):
    imgL = cv.imread(imgL_path, 0)
    imgR = cv.imread(imgR_path, 0)

    chessboard_size = (9, 6)
    img_size = (1024, 1024)

    def add_chessboard(img_file_path):
        img = cv.imread(img_file_path)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
        if ret:
            img = cv.drawChessboardCorners(img, chessboard_size, corners, ret)
        return img

    chess_imgL = add_chessboard(imgL_path)
    chess_imgR = add_chessboard(imgR_path)

    def read_camera_data(camera_file_path):
        with open(camera_file_path, 'r') as file:
            data = json.load(file)

        left_matrix = np.array(data['mtx_left'])
        left_dist = np.array(data['dist_left']).reshape(-1,1)
        right_matrix = np.array(data['mtx_right'])
        right_dist = np.array(data['dist_right']).reshape(-1,1)
        R = np.array(data['R'])
        T = np.array(data['T']).reshape(-1,1)

        return left_matrix, left_dist, right_matrix, right_dist, R, T

    left_matrix, left_dist, right_matrix, right_dist, R, T = read_camera_data(camera_file_path)

    rect_scale = 0.7

    LR, RR, p1, p2, q, roi1, roi2 = cv.stereoRectify(
        left_matrix, left_dist, 
        right_matrix, right_dist, 
        img_size, R, T, alpha=rect_scale)
    left_map1, left_map2 = cv.initUndistortRectifyMap(
        left_matrix, left_dist, 
        LR, 
        p1, img_size, cv.CV_32FC1)
    right_map1, right_map2 = cv.initUndistortRectifyMap(
        right_matrix, right_dist, 
        RR, 
        p2, img_size, cv.CV_32FC1)
    rectifiedL = cv.remap(chess_imgL, left_map1, left_map2, cv.INTER_LINEAR)
    rectifiedR = cv.remap(chess_imgR, right_map1, right_map2, cv.INTER_LINEAR)
    line_color = (0, 255, 0)
    line_thickness = 1
    num_lines = 40
    spacing = int(1024 // num_lines)

    for i in range(int(img_size[1]*0.333), int(img_size[1]*0.666), spacing):
        cv.line(rectifiedL, (0, i), (img_size[0], i), line_color, line_thickness)
        cv.line(rectifiedR, (0, i), (img_size[0], i), line_color, line_thickness)

    cv.namedWindow('Rectified Left', cv.WINDOW_NORMAL)
    cv.namedWindow('Rectified Right', cv.WINDOW_NORMAL)
    cv.moveWindow('Rectified Left', 0, 0)
    cv.moveWindow('Rectified Right', 700, 0)
    cv.resizeWindow('Rectified Left', 700, 700)
    cv.resizeWindow('Rectified Right', 700, 700)
    cv.imshow('Rectified Left', rectifiedL)
    cv.imshow('Rectified Right', rectifiedR)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":
    imgL_path = "HenryFiles/Camera Calibration/aupe-cal/c2/aupe-cal_c2_LWAC01_T00_P00_BS.png"
    imgR_path = "HenryFiles/Camera Calibration/aupe-cal/c2/aupe-cal_c2_RWAC01_T00_P00_BS.png"
    camera_file_path = "pcotplugins\pcotdistanceestimate\mtx_dst_rect_proj.json"

    rectify_and_display_images(imgL_path, imgR_path, camera_file_path)

    hall_l = "HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_LWAC01_T00_P00_BS.png"
    hall_r = "HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_RWAC01_T00_P00_BS.png"

    rectify_and_display_images(hall_l, hall_r, camera_file_path)

