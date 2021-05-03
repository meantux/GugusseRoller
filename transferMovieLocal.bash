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

source ftpserver.conf

captureMode=`cat cameraSettings.json | jq .captureMode | tr -d "\""`
echo "captureMode=$captureMode (`cat captureModes.json | jq .$captureMode.description | tr -d \"\\\"\"`)"
suffix=`cat captureModes.json | jq .$captureMode.suffix | tr -d "\""`
echo "files suffix=$suffix"

echo check if directory is a full path
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
echo -n "does the directory already exists? " 
# Does the directory already exists
if [ -d "$outputPath" ]; then
    echo "Yes!"
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
    lastfile=`ls *.$suffix | sort | tail -n 1`
    popd
    lastNum=`echo $lastFile | cut -c1-5`
    echo lastNum=$lastNum
    if [ -z "$lastFile" ]; then
	echo "The directory existed but we couldn't find a .$suffix in it"
	echo "therefore we'll start with 0, press Enter if you agree"
	echo "or press Ctrl-C to cancel"
	read
	export startNumber=0
    elif [ "$lastNum" == "00000" ]; then
	export startNumber=1
    else
	while [ "${lastNum:0:1}" == "0" ]; do
	    export lastNum=${lastNum:1}
	done
	startNumber=$((lastNum+1))
    fi
else
    echo "No!"
    # $outputPath does not exists, check if we can create it
    echo creating "$outputPath"
    
    mkdir -p "$outputPath"
    if [ $? -ne 0 ]; then
	echo "We couldn't create the directory (write access?)"
	exit -1
    fi
    # ok we got a brand new directory in our hand
    export startNumber=0
fi
echo startNumber=$startNumber
echo Killing any previous instances of sendWhileRunning and copy WhileRunning
killall sendWhileRunning.bash &> /dev/null
killall copyWhileRunning.bash &> /dev/null
sleep 1
touch /dev/shm/transferInProgress.flag
./copyWhileRunning.bash "$outputPath" "$suffix" &

# start the Gugusse.py
echo ./Gugusse.py $1 $startNumber $3
./Gugusse.py $1 $startNumber $3
sleep 2
./motors.py off
./Lights.py off
rm /dev/shm/transferInProgress.flag
