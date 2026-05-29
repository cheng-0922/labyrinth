import matplotlib.pyplot as plt
import cv2 as cv
import numpy as np
import os

def houghCircleTransform():
    root = os.getcwd()
    imgPath = os.path.join(root, 'Images//Final27.05.2026.png')
    img = cv.imread(imgPath)
    imgRGB = cv.cvtColor(img,cv.COLOR_BGR2RGB)
    imgGray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)

    imgGray = cv.medianBlur(imgGray,1)
    cv.imshow("gray",imgGray)
    circles = cv.HoughCircles(imgGray,cv.HOUGH_GRADIENT,dp=1,minDist=600,param1=200,
                              param2=30,minRadius=0,maxRadius=30)
    circles = np.uint16(np.around(circles))
    if circles is not None:
        for circle in circles[0,:]:
            cv.circle(imgRGB,(circle[0],circle[1]),circle[2],(255,255,255),10)

    imgResult = cv.cvtColor(imgRGB, cv.COLOR_RGB2BGR)
    
    cv.imshow('Hough Circles Result', imgResult)
    cv.waitKey(0) 
    cv.destroyAllWindows()

if __name__ == '__main__':
    houghCircleTransform()