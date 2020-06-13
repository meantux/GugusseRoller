import tifffile as tif
import sys
import os
import time
import tty
import termios
import threading
import numpy as np
import signal
import json


print("len args={}({})".format(len(sys.argv), sys.argv))

if len(sys.argv)==4:
    count=int(sys.argv[3])
elif len(sys.argv) not in [3,4]:
    print("Do not call this python script yourself, let bracketedToProResMov.bash do it")
    sys.exit(0)
else:
    count=0

    
directoryFrom=sys.argv[1]
outPipe=open(str(sys.argv[2]), "wb")
endFlag="{}.flagIn".format(sys.argv[2])


def getFilenames(count):
    a="{}/{:05d}_l.jpg".format(directoryFrom, count)
    b="{}/{:05d}_m.jpg".format(directoryFrom, count)
    c="{}/{:05d}_h.jpg".format(directoryFrom, count)
    nextPix="{}/{:05d}_h.jpg".format(directoryFrom, count+1)
    return nextPix, a, b, c

nextPix,inA,inB,inC=getFilenames(count)

tmpTif="{}.tif".format(sys.argv[2])

while os.path.exists(inC):
    print("doing {}, {}, {}".format(inA, inB, inC))
    os.system('enfuse --verbose=0 --depth 16 -o "{}" "{}" "{}" "{}"'.format(tmpTif,inA,inB,inC))
    img=tif.imread(tmpTif)
    outPipe.write(img.data)
    count+= 1
    nextPix,inA,inB,inC=getFilenames(count)
    if not os.path.exists(nextPix):
        print("It seems we caught up the scan, let's give it a minute")
        time.sleep(60)


#h=Image.open("16BitsTest/00000.tif", mode='r')
#print(h)

os.remove(endFlag)
