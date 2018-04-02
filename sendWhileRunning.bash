#/bin/bash



#ncftpput -u gugusse -p macako 192.168.2.40 Capture/test3 *

while [ ! -d "/dev/shm/complete" ]; do
    echo directory not there yet, `date`
    sleep 10    
done


cd /dev/shm/complete

function sendAndDelete(){
    if [ "$1" == "*.jpg" ]; then
	echo no files, sleeping 1 sec
	sleep 1
    else
        ncftpput -u gugusse -p macako 192.168.2.40 Capture/super8test $@ && rm -f $@
   fi
}

while [ 1 ]; do
    sendAndDelete *.jpg
done
