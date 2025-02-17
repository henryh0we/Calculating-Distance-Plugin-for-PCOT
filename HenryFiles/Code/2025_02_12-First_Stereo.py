import cv2 as cv
import numpy as np

left_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_LWAC01_T00_P00_BS.png')
right_img = cv.imread('HenryFiles\AUPE Images\distance\pctset-1m-8bit\distance_pctset-1m-8bit_RWAC01_T00_P00_BS.png')

if left_img is None or right_img is None:
    print("Image not found")
    exit()

# orb = cv.ORB_create()
orb = cv.ORB_create(nfeatures=1000, scaleFactor=1.2, nlevels=8, edgeThreshold=31, firstLevel=0, WTA_K=2, patchSize=31, fastThreshold=20)
kp1, des1 = orb.detectAndCompute(left_img, None)
kp2, des2 = orb.detectAndCompute(right_img, None)

bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
matches = sorted(matches, key=lambda x: x.distance)

result = cv.drawMatches(left_img, kp1, right_img, kp2, matches[:50], None, flags=2)

# cv.drawKeypoints(left_img, kp1, left_img, color=(0, 255, 0), flags=cv.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)
# cv.drawKeypoints(right_img, kp2, right_img, color=(0, 255, 0), flags=cv.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)

# cv.imshow('result', result)
# cv.waitKey(0)
# cv.destroyAllWindows()

cv.namedWindow('result', cv.WINDOW_NORMAL)
cv.imshow('result', result)
cv.waitKey(0)
cv.destroyAllWindows()