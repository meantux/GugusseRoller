from ftplib import FTP
from os import listdir,chdir,mkdir,remove,path
from threading import Thread
from json import load
from time import sleep

class FtpThread(Thread):
    def __init__(self, subdir, fileExt):
        Thread.__init__(self)
        self.subdir=subdir
        self.Loop=True
        self.fileExt=fileExt
        self.connected=False
        self.fileIndex=0


    def forceStartPoint(self, start):
        self.fileIndex=start
        
    def getStartPoint(self):
        if not self.connected:
            self.openConnection()
        if self.fileIndex>0:
            return 0
        listdir=[]
        print("listing remote directory {} (this could take time if there are thousands of files)".format(self.subdir))
        try:
            listdir=self.ftp.nlst("*.{}".format(self.fileExt))
        except Exception as e:
            msg=str(e)
            if msg != "450 No files found":
                print(e)
                raise Exception(msg)
            print("subdirectory {} has no {} in it, we start with file index 0".format( self.subdir, self.fileExt))
            self.fileIndex=0
            return 0
        print("sorting list")
        listdir.sort()
        lastFile=listdir[len(listdir)-1]        
        print("last file in {}={}".format(self.subdir,lastFile))
        self.fileIndex=1+int(lastFile.split(".")[0],10)
        print("File index is set at: {}".format(self.fileIndex))
        return self.fileIndex
        
        
        
    def openConnection(self):
        with open("ftp.conf","rt") as h:
            cfg=load(h)
        self.ftp=FTP(cfg["server"])
        self.ftp.login(user=cfg["user"],passwd=cfg["passwd"])
        if cfg["path"]!="" and cfg["path"]!=".":            
            self.ftp.cwd(cfg["path"])
        try:
            self.ftp.mkd(self.subdir)
        except Exception as e:
            msg=str(e)
            if msg != "550 {}: File exists".format(self.subdir):
                print(e)
        self.ftp.cwd(self.subdir)
        self.connected=True
    
    def run(self):
        self.getStartPoint()
        try:
            mkdir("/dev/shm/complete")
        except Exception as e:
            msg=str(e)
            if msg != "[Errno 17] File exists: '/dev/shm/complete'":
                print(e)
        chdir("/dev/shm/complete")
        while self.Loop:
            sleep(1)
            for item in listdir():
                if path.isfile(item):
                    print("transferring {}".format(item))
                    a=open(item, "rb")                    
                    self.ftp.storbinary("STOR {}".format(item),a)
                    a.close()
                    remove(item)
                    
    def stopLoop(self):
        self.Loop=False
        

if __name__ == "__main__":
    # Just a test
    ft=FtpThread("fetes60","dng")
    ft.getStartPoint()
    ft.start()
    sleep(30)
    print("done sleeping")
    ft.stopLoop()
    ft.join()
