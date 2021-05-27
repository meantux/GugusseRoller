#!/usr/bin/python3

from array import array
import cv2
import numpy as np
from Lights import Lights

cv2.namedWindow("Gugusse", 1)

# define width and height (fixed value that must match the driver)
w=5440
h=3696
ww=1200
wh=680
# open the driver device file handle
f=open("/dev/video0","rb")

def capturePicture():
    # create an empty array of unsigned short int (16 bits) 
    a=array('H')

    # read 20095360 unsigned short int from the file handle (40190720 bytes)
    a.fromfile(f, h*w)
    # convert it to a numpy object
    n=np.array(a)

    # shift the unused bits (we have 12bits pixels saved in 16bits unsigned ints)
    # by shifting the bits to the left we are actually pushing the unused bits to
    # the least significant values.
    n=n<<4

    # transform the simple array into a array of arrays of arrays
    # basically we're just separating the data in rows, columns and channels
    img=n.reshape(h,w,1)

    # save the picture.
    # cv2.imwrite("test.tif", img)

    return img

while True:
    img=capturePicture()
    res=cv2.resize(img,(ww,wh),interpolation=cv2.INTER_LINEAR)
    # res = img[ int((h-wh)/2):int((h+wh)/2) , int((w-ww)/2):int((w+ww)/2) ]
    #res = img[ int((h-wh)/2):int((h+wh)/2) , 0:int(ww) ]
    cv2.imshow("Gugusse", res)
    cv2.waitKey(1)





