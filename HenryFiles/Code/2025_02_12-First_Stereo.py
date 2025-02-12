import cv2 as cv
import numpy as np

left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

if left_img is None or right_img is None:
    print("Image not found")
    exit()

orb = cv.ORB_create()
kp1, des1 = orb.detectAndCompute(left_img, None)
kp2, des2 = orb.detectAndCompute(right_img, None)

bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
matches = sorted(matches, key=lambda x: x.distance)

result = cv.drawMatches(left_img, kp1, right_img, kp2, matches[:10], None, flags=2)

# cv.imshow('result', result)
# cv.waitKey(0)
# cv.destroyAllWindows()

cv.namedWindow('result', cv.WINDOW_NORMAL)
cv.imshow('result', result)
cv.waitKey(0)
cv.destroyAllWindows()