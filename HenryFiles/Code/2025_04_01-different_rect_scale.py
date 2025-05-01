import numpy as np
import json
import cv2 as cv

img_size = (1024, 1024)

def select_point_left(event, x, y, flags, param):
    global points_left
    if event == cv.EVENT_LBUTTONDOWN:
        if len(points_left) < 1:
            points_left.append((x, y))
            cv.circle(param, (x, y), 5, (0, 255, 0), -1)
            cv.imshow("Left Image", param)
            print(f"Left Image: Point selected at: {x}, {y}")
        if len(points_left) == 1:
            cv.setMouseCallback("Left Image", lambda *args: None)  # Disable further callbacks

def select_point_right(event, x, y, flags, param):
    global points_right
    if event == cv.EVENT_LBUTTONDOWN:
        if len(points_right) < 1:
            points_right.append((x, y))
            cv.circle(param, (x, y), 5, (0, 255, 0), -1)
            cv.imshow("Right Image", param)
            print(f"Right Image: Point selected at: {x}, {y}")
        if len(points_right) == 1:
            cv.setMouseCallback("Right Image", lambda *args: None)  # Disable further callbacks

with open('HenryFiles/camera_data.json') as f:
    data = json.load(f)

mtx_left = np.array(data['mtx_left'])
dist_left = np.array(data['dist_left']).reshape(-1,1)
rect_left = np.array(data['rect_left'])
proj_left = np.array(data['proj_left'])

mtx_right = np.array(data['mtx_right'])
dist_right = np.array(data['dist_right']).reshape(-1,1)
rect_right = np.array(data['rect_right'])
proj_right = np.array(data['proj_right'])

R = np.array(data['R'])
T = np.array(data['T'])
E = np.array(data['E'])
F = np.array(data['F'])

rect_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
output_table = []

for i in range(len(rect_values)):

    alpha_val = rect_values[i]
    rect_left, rect_right, proj_left, proj_right, Q, roi_left, roi_right = cv.stereoRectify(
        mtx_left, dist_left, mtx_right, dist_right, img_size, 
        R , T, flags=cv.CALIB_ZERO_DISPARITY, alpha=alpha_val
    )

    print(f"Rectification at alpha={rect_values[i]}")
    # print(f"Left ROI: {roi_left}")
    # print(f"Right ROI: {roi_right}")

    map_left_x, map_left_y = cv.initUndistortRectifyMap(
        mtx_left, dist_left, rect_left, proj_left, img_size, cv.CV_32FC1)
    map_right_x, map_right_y = cv.initUndistortRectifyMap(
        mtx_right, dist_right, rect_right, proj_right, img_size, cv.CV_32FC1)

    left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_LWAC01_T00_P00_BS.png')
    right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit-tiltdown\distance_pctset-1m-8bit-tiltdown_RWAC01_T00_P00_BS.png')

    left_rectified = cv.remap(left_img, map_left_x, map_left_y, cv.INTER_LINEAR)
    right_rectified = cv.remap(right_img, map_right_x, map_right_y, cv.INTER_LINEAR)

    # Draw horizontal lines on left and right rectified images
    num_lines = 40
    interval = left_rectified.shape[0] // num_lines
    for i in range(0, left_rectified.shape[0], interval):
        cv.line(left_rectified, (0, i), (left_rectified.shape[1], i), (0, 255, 0), 1)
        cv.line(right_rectified, (0, i), (right_rectified.shape[1], i), (0, 255, 0), 1)

    points = []

    # Initialize lists to store points
    points_left = []
    points_right = []

    cv.namedWindow("Left Image", cv.WINDOW_NORMAL)
    cv.setMouseCallback("Left Image", select_point_left, left_rectified)
    cv.resizeWindow('Left Image', 600, 600)
    cv.setWindowProperty('Left Image', cv.WND_PROP_ASPECT_RATIO, cv.WINDOW_KEEPRATIO)

    cv.namedWindow("Right Image", cv.WINDOW_NORMAL)
    cv.setMouseCallback("Right Image", select_point_right, right_rectified)
    cv.resizeWindow('Right Image', 600, 600)
    cv.setWindowProperty('Right Image', cv.WND_PROP_ASPECT_RATIO, cv.WINDOW_KEEPRATIO)

    cv.moveWindow('Left Image', 100, 100)  # Position of the left image window
    cv.moveWindow('Right Image', 100 + 600, 100)  # Position of the right image window

    while True:
        # cv.imshow("Image", combined_rectified)
        cv.imshow("Left Image", left_rectified)
        cv.imshow("Right Image", right_rectified)
        if cv.waitKey(1) & 0xFF == 27 or ((len(points_left) == 1) and (len(points_right) == 1)):  # ESC key or 2 points selected
            break

    cv.destroyAllWindows()

    if ((len(points_left) == 1) and (len(points_right) == 1)):
        point_left = points_left[0] # ( x , y )
        point_right = points_right[0] # ( x , y )

        disparity = point_right[0] - point_left[0]

        disparity = abs(disparity) #  Always non-negative

        print("disparity: ", disparity)

        # Currently works using estimations made from OpenCV.
        # Need to make adjustments to code to instead use new code.
        # Thus using real-world data

        # ==================
        # Real-world data
        # ==================

        focal_length_mm = 12.1
        image_width_pixels = 1024

        sensor_width_mm = 7.0656

        focal_length_pixels = (focal_length_mm / sensor_width_mm) * image_width_pixels

        focal_length = focal_length_pixels

        baseline = 0.5  # Distance in meters

        depth = (focal_length * baseline) / disparity

        aupe_height = 1.094

        approximate_ground_distance = np.sqrt(depth**2 - aupe_height**2)

        print(f"depth: {depth:.3f} m, approximate ground distance: {approximate_ground_distance:.3f} m")

        output = f"alpha value: {alpha_val}, leftpoint: {point_left}, rightpoint: {point_right}, depth: {depth:.3f} m, approximate ground distance: {approximate_ground_distance:.3f} m"

        output_table.append(output)

        # return output

print("\n".join(output_table))
    
