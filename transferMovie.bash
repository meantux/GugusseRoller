#!/bin/bash
#
#
# 
#
################################################################################

USAGE="
  USAGE: $0 <film format json file> <project name> <feeder orientation(cw|ccw)>

EXAMPLE: $0 super8.json vacation1986 ccw"

if [ ! -f "$1" ] || [ -z "$2" ] || ( [ "$3" != "cw" ] && [ "$3" != "ccw" ] ); then
    echo "$USAGE"
    exit 0
fi

source ftpserver.conf


# check if FTP server is available or exit if not.
ncftpls -u$ftpuser -p$ftppassword ftp://$ftpserver/$ftppathprefix > /dev/shm/directoriesOnServer.txt
if [ $? -ne 0 ]; then
    echo "ftp server check Error (check your settings in ftpserver.conf)"
    exit -1
fi

# Does the directory already exists on the ftp server?
dirExists=NO
for i in `cat /dev/shm/directoriesOnServer.txt` ; do
    if [ "$2" == "$i" ]; then
	export dirExists=YES
    fi
done

# if not then create it
if [ $dirExists == NO ]; then
    echo hello > deleteme.txt
    ncftpput -m -u$ftpuser -p$ftppassword deleteme.txt ftp://$ftpserver/$ftppathprefix/$2/deleteme.txt
    if [ $? -ne 0 ]; then
	echo "We could not create directory on ftp server"
	exit -1
    fi
    export $startNumber=0
else
    # else figure out which is last file.
    echo "Directory $2 already existed on the ftp server!"
    echo "checking which is its last file in it"
    echo "(this could take a while)"
    ncftpls -u$ftpuser -p$ftppassword ftp://$ftpserver/$ftppathprefix/$2/*.jpg > /dev/shm/filesOnServer.txt
    if [ $? -ne 0 ]; then
	echo "We failed listing the directory, ouch! don't know what to do"
	exit -1
    fi
    lastFile=`cat /dev/shm/filesOnServer.txt | sort | tail -n 1`
    echo lastfile=$lastFile	
    if [ -z "$lastFile" ]; then
	echo "The directory existed but we couldn't find a jpg in it"
	echo "therefore we'll start with 0, press Enter if you agree"
	echo "or press Ctrl-C to cancel"
	read
	export startNumber=0
    elif [ "$lastFile" == "00000.jpg" ]; then
	export startNumber=1
    else	
	lastFileNum=${lastFile%.jpg}
	while [ "${lastFileNum:0:1}" == "0" ]; do
	    export lastFileNum=${lastFileNum:1}
	    startNumber=$((lastFileNum+1))
	done
    fi
fi	    
echo "We'll start with number $starNumber"

killall sendWhileRunning.bash &> /dev/null
sleep 2

# start a new sendWhileRunning.bash with proper film name
./sendWhileRunning.bash "$2" &

# start the Gugusse.py
./Gugusse.py $1 $3
