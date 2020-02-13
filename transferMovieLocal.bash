#!/bin/bash
#
#
# 
#
################################################################################

USAGE="
  USAGE: $0 <film format json file> <save directory> <feeder orientation(cw|ccw)>

EXAMPLES: $0 super8.json /mnt/USBDISK/vacation1986 ccw"

if [ ! -f "$1" ] || [ -z "$2" ] || ( [ "$3" != "cw" ] && [ "$3" != "ccw" ] ); then
    echo "$USAGE"
    exit 0
fi

formatFile="$1"
outputPath="$2"
orientation="$3"

# check that directory is a full path
if [ "${outputPath:0:1}" != "/" ]; then
        echo "the save directory must be a full path. A full path must start with the \"/\" directory."
        echo "like  /home/pi/out/Film001"
        echo "like  /media/pi/SOMEUSBKEY/TripHawaii"
	echo "like  /mnt/SOMENETWORKDRIVEMOUNT/HomeComing"
	echo ""
	echo "$USAGE"
        exit -1
fi
# Does the directory already exists
dirExists=NO
if [ -d "$outputPath" ]; then
    # Can we write in it?
    touch "$outputPath/deleteme.txt"
    if [ $? -ne 0 ]; then
	echo "write error in save directory"
	exit -1
    fi
    # if directory already existed we need to figure out
    # which is the last file in it so we could resume from
    # there
    pushd "$outputPath"
    lastfile=`ls *.jpg | sort | tail -n 1`
    popd
    if [ "$lastfile" == "00000.jpg" ]; then
	export startNumber=1
    elif [ -n "$lastfile" ]; then
	lastnum=${lastfile%.jpg}
	while [ "${lastnum:0:1}" == "0" ]; do
	    export lastnum=${lastnum:1}
	done
	export startNumber=$((lastnum+1))
    else
	export startNumber=0
    fi	    
else
    # $outputPath does not exists, check if we can create it
    mkdir -p "$outputPath"
    if [ $? -ne 0 ]; then
	echo "We couldn't create the directory (write access?)"
	exit -1
    fi
    # ok we got a brand new directory in our hand
    export startNumber=0
fi
killall sendWhileRunning.bash &> /dev/null
killall copyWhileRunning.bash &> /dev/null
sleep 1
touch /dev/shm/transferInProgress.flag
./copyWhileRunning.bash "$outputPath"

# start the Gugusse.py
echo ./Gugusse.py $1 $startNumber $3
./Gugusse.py $1 $startNumber $3
sleep 2
rm /dev/shm/transferInProgress.flag
