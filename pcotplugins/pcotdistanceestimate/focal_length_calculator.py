import json
import os
import numpy as np

# === ORIGINALLY HARDCODED ===
# side_length = 7.0656 # in mm
# ============================

file_path = 'pcotplugins/pcotdistanceestimate/focal_baseline_height.json'

baseline = 0.5 # in meters

aupe_pixel_size = 3.45 # in um

# Bin Pixels
binned_pixel_size = aupe_pixel_size * 2 # 6.9um

# Size of image = 1024 x 1024

effective_focal_pane_side_um = 1024 * binned_pixel_size # 7065.6um
print(effective_focal_pane_side_um)

effective_focal_pane_side_mm = effective_focal_pane_side_um / 1000 # 7.0656mm
print(effective_focal_pane_side_mm)

side_length = round(effective_focal_pane_side_mm, 5 - int(np.floor(np.log10(abs(effective_focal_pane_side_mm)))) - 1)
print(side_length)

focal_length_mm = 12.1 # in mm
camera_height = 1.094

def focal_length_from_sensor_width(sensor_width_mm, focal_length_mm, image_width_pixels):
    """
    Calculates the focal length in pixels from the sensor width in mm
    """
    return (focal_length_mm / sensor_width_mm) * image_width_pixels

def generate_data():
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {
            'baseline': baseline,
            'camera_height': camera_height
        }
    
    new_focal_length = focal_length_from_sensor_width(side_length, focal_length_mm, 1024)
    data['focal_length'] = new_focal_length
    print(f"New focal length: {new_focal_length}")
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# try:
#     with open('focal_baseline_height.json') as f:
#         focal_baseline_height = json.load(f)
#     overwrite = input("Focal length and baseline file already exists. Do you want to overwrite it? (y/n): ")
#     if overwrite == 'y':
#         with open('focal_baseline_height.json', 'w') as f:
#             json.dump({
#                 'focal_length': focal_length_from_sensor_width(side_length, focal_length_mm, 1024),
#                 'baseline': baseline,
#                 'camera_height': camera_height
#             }, f, indent=4)
#     else:
#         print("Focal length and baseline file will not be overwritten.")
# except FileNotFoundError:
#     with open('focal_baseline_height.json', 'w') as f:
#         json.dump({
#             'focal_length': focal_length_from_sensor_width(side_length, focal_length_mm, 1024),
#             'baseline': baseline,
#             'camera_height': camera_height
#         }, f, indent=4)

if not os.path.exists(file_path):
    print(f"File {file_path} does not exist. Creating a new file with default values...")
    generate_data()
    print("Success")
else:
    response = input(f"File {file_path} already exists. Overwrite? (y/n): ")
    if response.lower() == 'y':
        print("Overwriting file...")
        generate_data()
        print("Success")
    else:
        print("Not overwriting file.")