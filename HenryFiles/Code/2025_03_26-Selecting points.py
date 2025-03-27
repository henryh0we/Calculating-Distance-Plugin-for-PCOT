# import cv2 as cv
# import os
# import numpy as np

# left_images = []
# right_images = []

# points_img1 = []
# points_img2 = []
# current_image_index = 0

# def load_image_pairs(base_directory):
#     """
#     Loads image pairs from subdirectories.
    
#     Args:
#         base_directory: Path to directory containing subdirectories with image pairs
        
#     Returns:
#         left_images: List of left images
#         right_images: List of right images
#     """
#     left_images = []
#     right_images = []
    
#     # Iterate through all subdirectories
#     for folder_name in os.listdir(base_directory):
#         folder_path = os.path.join(base_directory, folder_name)
        
#         if os.path.isdir(folder_path):
#             # Get all image files in the folder
#             image_files = [f for f in os.listdir(folder_path) 
#                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
#             if len(image_files) >= 2:
#                 # Sort to ensure consistent ordering
#                 image_files.sort()
                
#                 # Load the first image as left, second as right
#                 left_path = [f for f in image_files if 'LWAC' in f][0]
#                 right_path = [f for f in image_files if 'RWAC' in f][0]
                
#                 left_img = cv.imread(os.path.join(folder_path, left_path))
#                 right_img = cv.imread(os.path.join(folder_path, right_path))
                
#                 if left_img is not None and right_img is not None:
#                     left_images.append(left_img)
#                     right_images.append(right_img)
    
#     return left_images, right_images

# def click_event(event, x, y, flags, param):
#     if event == cv.EVENT_LBUTTONDOWN:
#         # Determine which image was clicked
#         window_name = cv.getWindowName(cv.getWindowProperty(cv.getWindowProperty(0, cv.WND_PROP_FULLSCREEN)))
        
#         if window_name == "Image 1":
#             points_img1.append((x, y))
#             # Draw circle at clicked point
#             cv.circle(left_images[current_image_index], (x, y), 5, (0, 255, 0), -1)
#             cv.imshow("Image 1", left_images[current_image_index])
#             print(f"Image 1: Point added at ({x}, {y})")
#         else:
#             points_img2.append((x, y))
#             # Draw circle at clicked point
#             cv.circle(right_images[current_image_index], (x, y), 5, (0, 255, 0), -1)
#             cv.imshow("Image 2", right_images[current_image_index])
#             print(f"Image 2: Point added at ({x}, {y})")

# # left_images, right_images = load_image_pairs('HenryFiles\AUPE Images\distance\pctset-1m-8bit')

# # # Create a window for the first image
# # cv.namedWindow('Image Pair', cv.WINDOW_NORMAL)
# # combined = np.hstack([left_images[0], right_images[0]])
# # cv.imshow('Image Pair', combined)

# # cv.waitKey(0)
# # cv.destroyAllWindows()

# left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
# right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

# left_images.append(left_img)
# right_images.append(right_img)

import cv2 as cv
import numpy as np

class DualImagePointSelector:
    def __init__(self, images1, images2):
        self.images1 = images1
        self.images2 = images2
        self.points_img1 = []
        self.points_img2 = []
        self.current_image_idx = 0
        self.img1_copy = None
        self.img2_copy = None
    
    def click_event_img1(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.points_img1.append((x, y))
            # Draw circle at clicked point on copy to preserve original
            cv.circle(self.img1_copy, (x, y), 3, (0, 255, 0), -1)
            cv.imshow("Image 1", self.img1_copy)
            print(f"Image 1: Point added at ({x}, {y})")
    
    def click_event_img2(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.points_img2.append((x, y))
            # Draw circle at clicked point on copy to preserve original
            cv.circle(self.img2_copy, (x, y), 3, (0, 255, 0), -1)
            cv.imshow("Image 2", self.img2_copy)
            print(f"Image 2: Point added at ({x}, {y})")
    
    def show_images(self, idx):
        """
        Display two images and allow the user to click on points in both.
        
        Args:
            idx: Index of the images to display from the arrays
            
        Returns:
            Tuple of two lists containing the clicked points for each image
        """
        self.current_image_idx = idx
        
        # Create copies of the original images to draw on
        self.img1_copy = self.images1[idx].copy()
        self.img2_copy = self.images2[idx].copy()
        
        # Reset points for new images
        self.points_img1 = []
        self.points_img2 = []
        
        # Create windows
        cv.namedWindow("Image 1")
        cv.namedWindow("Image 2")
        
        # Set mouse callback for both windows with separate functions
        cv.setMouseCallback("Image 1", self.click_event_img1)
        cv.setMouseCallback("Image 2", self.click_event_img2)
        
        # Display images
        cv.imshow("Image 1", self.img1_copy)
        cv.imshow("Image 2", self.img2_copy)
        
        print("Click on points in both images. Press 'ESC' to finish.")
        
        # Wait for key press
        while True:
            key = cv.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                break
            elif key == ord('c'):  # Clear points
                self.points_img1 = []
                self.points_img2 = []
                self.img1_copy = self.images1[idx].copy()
                self.img2_copy = self.images2[idx].copy()
                cv.imshow("Image 1", self.img1_copy)
                cv.imshow("Image 2", self.img2_copy)
                print("Points cleared")
        
        cv.destroyAllWindows()
        return self.points_img1, self.points_img2

# Example usage
if __name__ == "__main__":
    # Load example images (replace with your actual image loading code)
    # For demonstration, creating blank images
    img1_1 = np.ones((400, 600, 3), dtype=np.uint8) * 255
    img1_2 = np.ones((400, 600, 3), dtype=np.uint8) * 200
    img2_1 = np.ones((400, 600, 3), dtype=np.uint8) * 150
    img2_2 = np.ones((400, 600, 3), dtype=np.uint8) * 100
    
    # Create image arrays
    images1 = [img1_1, img1_2]
    images2 = [img2_1, img2_2]
    
    # Create point selector
    selector = DualImagePointSelector(images1, images2)
    
    # Show images at index 0
    points1, points2 = selector.show_images(0)
    
    print("Final points for Image 1:", points1)
    print("Final points for Image 2:", points2)
    
    # You can continue with other indices if needed
    # points1, points2 = selector.show_images(1)