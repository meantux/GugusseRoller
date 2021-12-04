from os import listdir,mkdir,remove,path
from shutil import move
from threading import Thread
from json import load
from time import sleep
from glob import glob

class LocalThread(Thread):
    def __init__(self, subdir, fileExt, uiTools, basePath):
        Thread.__init__(self)
        self.subdir=subdir
        self.fileExt=fileExt
        self.Loop=True
        self.message=uiTools["message"]
        self.fileIndex=0
        self.fullpath="{}/{}".format(basePath, subdir)
        print("fullpath={}".format(self.fullpath))
        try:
            mkdir(self.fullpath)
        except:
            pass
        

    def forceStartPoint(self, start):
        self.fileIndex=start
        
    def getStartPoint(self):
        if self.fileExt[0] == '.':
            search="{}/*{}".format(self.fullpath, self.fileExt)
        else:
            search="{}/*.{}".format(self.fullpath, self.fileExt)
        files=glob(search)
        if len(files) == 0:
            print("No previous file found, starting with index at 0")
            self.fileIndex=0
            return 0
        files.sort()
        lastFile=files[len(files)-1]
        print("last file={}".format(lastFile))
        base=path.basename(lastFile)        
        self.message("last file in {}={}".format(self.subdir,lastFile))
        self.fileIndex=1+int(base.split(".")[0],10)
        self.message("File index now at: {}".format(self.fileIndex))
        return self.fileIndex
                
        
    def run(self):
        self.Loop=True
        try:
            mkdir("/dev/shm/complete")
        except Exception as e:
            msg=str(e)
            if msg != "[Errno 17] File exists: '/dev/shm/complete'":
                self.message(e)
        while self.Loop:
            sleep(1)
            for item in listdir("/dev/shm/complete/"):
                if path.isfile("/dev/shm/complete/{}".format(item)):
                    destination="{}/{}".format(self.fullpath, item)
                    self.message(destination)
                    move("/dev/shm/complete/{}".format(item),destination)
                    
    def stopLoop(self):
        self.Loop=False
        
