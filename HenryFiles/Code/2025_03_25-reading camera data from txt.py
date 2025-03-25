import numpy as np

def read_camera_data():
    """
    Read the camera calibration data from the text file 'camera_data.txt'
    and return the camera matrices and distortion coefficients.
    """
    # Read the entire file and split into lines
    with open('camera_data.txt', 'r') as file:
        lines = file.readlines()

    # Remove any empty lines and strip newline characters
    lines = [line.strip() for line in lines if line.strip() != '']

    # Parse Left Camera Matrix (Lines 0 to 2)
    left_camera_matrix = [list(map(float, lines[i].split())) for i in range(3)]
    left_camera_matrix = np.array(left_camera_matrix)

    # Parse Left Camera Distortion Coefficients (Line 3)
    left_camera_dist = list(map(float, lines[3].split()))
    left_camera_dist = np.array(left_camera_dist).reshape(-1, 1)  # Reshape

    # Parse Right Camera Matrix (Lines 4 to 6)
    right_camera_matrix = [list(map(float, lines[i].split())) for i in range(4, 7)]
    right_camera_matrix = np.array(right_camera_matrix)

    # Parse Right Camera Distortion Coefficients (Line 7)
    right_camera_dist = list(map(float, lines[7].split()))
    right_camera_dist = np.array(right_camera_dist).reshape(-1, 1)  # Reshape

    # Return the results
    return left_camera_matrix, left_camera_dist, right_camera_matrix, right_camera_dist

