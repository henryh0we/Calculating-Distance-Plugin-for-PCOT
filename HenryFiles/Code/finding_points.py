import cv2 as cv
import numpy as np

left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

if left_img is None or right_img is None:
    print("Image not found")
    exit()

window_size = 50
search_range = 100

def select_point(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        
        half_w = window_size // 2
        # patch = left_img[y - half_w:y + half_w, x - half_w:x + half_w]
        
        # if patch.shape[0] != window_size or patch.shape[1] != window_size:
        #     print("Patch error")
        #     return

        y_start = max(0, y - half_w)
        y_end = min(right_img.shape[0], y + half_w)
        x_start = max(0, x-search_range)
        x_end = min(right_img.shape[1], x + search_range+1)
        
        patch = left_img[y_start:y_end, x_start:x_end]
        
        if patch.shape[0] != window_size or patch.shape[1] != window_size:
            # Calculate the padding needed
            pad_y = max(0, window_size - patch.shape[0])
            pad_x = max(0, window_size - patch.shape[1])
            
            # Pad the patch with zeros
            patch = np.pad(patch, ((0, pad_y), (0, pad_x), (0,0)), mode='constant')
        
        
        search_area = right_img[y_start:y_end, x_start:x_end]
        
        result = cv.matchTemplate(search_area, patch, cv.TM_CCOEFF_NORMED)
        _,_,_, max_loc = cv.minMaxLoc(result)
        
        matched_x = x_start + max_loc[0]
        matched_y = y
        
        left_copy = left_img.copy()
        right_copy = right_img.copy()
        
        cv.circle(left_copy, (x, y), 5, (0, 0, 255), -1)
        cv.circle(right_copy, (matched_x, matched_y), 5, (255, 0, 0), -1)
        
        combined = np.hstack([left_copy, right_copy])
        
        cv.imshow('Point Matching', combined)
        
cv.namedWindow('Point Matching', cv.WINDOW_NORMAL)
cv.setMouseCallback('Point Matching', select_point)

combined = np.hstack([left_img, right_img])
cv.imshow('Point Matching', combined)
cv.waitKey(0)
cv.destroyAllWindows()