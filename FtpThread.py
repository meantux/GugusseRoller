from ftplib import FTP
from os import listdir,chdir,mkdir,remove,path
from threading import Thread
from json import load
from time import sleep

class FtpThread(Thread):
    def __init__(self, subdir):
        Thread.__init__(self)
        self.subdir=subdir
        self.Loop=True
    
    def run(self):
        with open("ftp.conf","rt") as h:
            cfg=load(h)
        ftp=FTP(cfg["server"])
        ftp.login(user=cfg["user"],passwd=cfg["passwd"])
        if cfg["path"]!="" and cfg["path"]!=".":            
            ftp.cwd(cfg["path"])
        try:
            ftp.mkd(self.subdir)
        except Exception as e:
            print(e)
        ftp.cwd(self.subdir)
        try:
            mkdir("/dev/shm/complete")
        except Exception as e:
            print(e)
        chdir("/dev/shm/complete")
        while self.Loop:
            sleep(1)
            for item in listdir():
                if path.isfile(item):
                    print("transferring {}".format(item))
                    a=open(item, "rb")                    
                    ftp.storbinary("STOR {}".format(item),a)
                    a.close()
                    remove(item)
                    
    def stopLoop(self):
        self.Loop=False
        

if __name__ == "__main__":
    # Just a test
    ft=FtpThread("ftpTest")
    ft.start()
    sleep(30)
    print("done sleeping")
    ft.stopLoop()
    ft.join()
