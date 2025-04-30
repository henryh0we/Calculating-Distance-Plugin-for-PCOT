import numpy as np
import json
file_path = "pcotplugins\pcotdistanceestimate plugins\mtx_dst_rect_proj.json"

with open(file_path, 'r') as file:
    data = json.load(file)

print(data['R'])
print(data['T'])

def rotation_matrix_to_degrees(R):
    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0

    return np.degrees([x, y, z])

def degrees_to_rotation_matrix(degrees):
    """
    Function to convert a list of Euler angles in degrees to a rotation matrix.

    Parameters
    ----------
    degrees : list
        List of 3 Euler angles in degrees.

    Returns
    -------
    R : numpy array
        Rotation matrix.
    """
    x_deg, y_deg, z_deg = degrees
    x_rad = np.deg2rad(x_deg)
    y_rad = np.deg2rad(y_deg)
    z_rad = np.deg2rad(z_deg)

    Rx = np.array([[1, 0, 0],
                   [0, np.cos(x_rad), -np.sin(x_rad)],
                   [0, np.sin(x_rad), np.cos(x_rad)]])

    Ry = np.array([[np.cos(y_rad), 0, np.sin(y_rad)],
                   [0, 1, 0],
                   [-np.sin(y_rad), 0, np.cos(y_rad)]])

    Rz = np.array([[np.cos(z_rad), -np.sin(z_rad), 0],
                   [np.sin(z_rad), np.cos(z_rad), 0],
                   [0, 0, 1]])

    R = Rz @ Ry @ Rx
    return R

def translation_matrix_to_mm(T):
    return T * 1000
r_degrees = rotation_matrix_to_degrees(np.array(data['R']))

T_output = translation_matrix_to_mm(np.array(data['T']))

print("R_degrees:", r_degrees)
print("T_output:", T_output)
print("==========")

possible_r = (0, 5.6, 0)

rotation_matrix = degrees_to_rotation_matrix(possible_r)
print(rotation_matrix)