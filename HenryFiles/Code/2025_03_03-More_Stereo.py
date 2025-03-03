import cv2
import numpy as np

# Load stereo images
imgL = cv2.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png', 0)  # Left image
imgR = cv2.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png', 0)  # Right image

# Camera parameters
# focal_length = 700  # Example focal length in pixels
baseline = 0.5  # Distance between the two cameras in meters

focal_length_mm = 12
sensor_width_mm = 8.8
image_width_pixels = 1024

focal_length_pixels = (focal_length_mm / sensor_width_mm) * image_width_pixels

focal_length = focal_length_pixels

# StereoBM parameters
num_disparities = 16 * 5  # Must be divisible by 16
block_size = 5  # Block size for matching

# Create StereoBM object and compute disparity map
stereo = cv2.StereoBM_create(numDisparities=num_disparities, blockSize=block_size)
disparity = stereo.compute(imgL, imgR)

# Compute depth map
depth_map = np.zeros(disparity.shape, np.float32)
depth_map[disparity > 0] = (focal_length * baseline) / disparity[disparity > 0]

# Normalize depth map to show it as an image
min_val = np.min(depth_map)
max_val = np.max(depth_map)
depth_map_normalized = cv2.normalize(depth_map, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

# Display disparity and depth maps
cv2.imshow('Disparity', disparity)
cv2.imshow('Depth Map', depth_map_normalized)
cv2.waitKey(0)
cv2.destroyAllWindows()