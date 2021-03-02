#/bin/bash

USAGE="$0 <output path> <suffix>"

if [ -z "$2" ]; then
    echo "$USAGE"
    exit -1
fi
export dirName="$1"
export suffix="$2"

mkdir -p /dev/shm/complete

if [ ! -d "$dirName" ]; then
    mkdir -p "$dirName"
fi

function sendAndDelete(){
    if [ "$1" == "*.$suffix" ]; then
	#echo no files, sleeping 1 sec
	sleep 1
    else
	echo moving $@ to $dirName
	mv $@ "$dirName"
    fi
}

cd /dev/shm/complete
while [ -f "/dev/shm/transferInProgress.flag" ]; do
    sendAndDelete *.$suffix
done
