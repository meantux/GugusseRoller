from array import array
import cv2
import numpy as np
from Lights import Lights

#cv2.namedWindow("Gugusse", 1)

w=5440
h=3696

def capturePicture():
    a=array('H')
    f=open("/dev/video0","rb")
    a.fromfile(f, h*w)
    f.close()
    n=np.array(a)
    n=n<<4
    img=n.reshape(h,w,1)
    res=cv2.resize(img, (1024,768), interpolation = cv2.INTER_LINEAR)
    cv2.imshow("Gugusse", res)
    cv2.waitKey(20)
    return img

l=Lights()
l.set("red")
r=capturePicture()
l.set("green")
g=capturePicture()
l.set("blue")
b=capturePicture()
img=cv2.merge([b,g,r])
cv2.imwrite("test.tif", img)
#res=cv2.resize(img,(1024,768),interpolation=cv2.INTER_LINEAR)
#cv2.imshow("Gugusse", res)
#cv2.waitKey(10000)





