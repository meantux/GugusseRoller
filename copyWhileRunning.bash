#/bin/bash


USAGE="$0 <output path>"


if [ -z "$1" ]; then
    echo "$USAGE"
    exit -1
fi
export dirName="$1"

mkdir -p /dev/shm/complete

cd /dev/shm/complete

if [ -n "$dirName" ]; then
    mkdir -p "$dirName"
fi

function sendAndDelete(){
    if [ "$1" == "*.jpg" ]; then
	echo no files, sleeping 1 sec
	sleep 1
    else
	mv $@ "$localPath/$dirName/"
    fi
}

while [ -f "/dev/shm/transferInProgress.flag" ]; do
    sendAndDelete *.jpg
done
