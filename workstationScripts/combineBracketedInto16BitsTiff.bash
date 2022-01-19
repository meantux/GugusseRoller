#!/bin/bash

# Script created and tested on Ubuntu 20.04
# beside the regular bash tools you do need
# the software enfuse to be installed

USAGE="$0 <directoryFrom> <directoryTo>"

MING=30
MINM=$((MING*1024))

directoryFrom="$1"
directoryTo="$2"


if [ ! -d "$directoryFrom" ] || [ ! -d "$directoryTo" ]; then
    echo "$USAGE"
    exit 0
fi

if [ ! -f "$directoryFrom/00000_h.jpg" ]; then
    echo "We don't even have a first trio of picture at $directoryFrom"
    echo "$USAGE"
    exit 0
fi
# find first value
pushd "$directoryTo"
if [ "`ls *.tif | wc -l`" -gt "0" ]; then
    lastfile="`ls *.tif | tail -n 1`"    
    lastcount=${lastfile%.tif}
    while [ "${lastcount:0:1}" == "0" ]; do
        lastcount=${lastcount:1}
	if [ "$lastcount" == "" ]; then
	    lastcount=0
	    break
	fi
    done    
    export count=$((lastcount+1))
else
    export count=0
fi
popd
function getAvailableMegabytes () {
    df -BM "$1" | tail -n 1 | awk '{print $4}' | tr -d 'M'    
}

inCount=$count
outCount=$count
inFnA="`printf \"$directoryFrom/%05d_m.jpg\" $inCount`"
inFnB="`printf \"$directoryFrom/%05d_l.jpg\" $inCount`"
inFnC="`printf \"$directoryFrom/%05d_h.jpg\" $inCount`"

export spaceLeft=`getAvailableMegabytes ${directoryTo}`

while [ -f "$inFnA" ] && [ "$spaceLeft" -gt $MINM ]; do
    outFn=`printf "%s/B%05d.tif" "$directoryTo" $outCount`
    outFinal=`printf "%s/%05d.tif" "$directoryTo" $outCount`

    instances=`ps ax | grep enfuse | grep -v grep | wc -l`
    while [ $instances -gt 3 ]; do
	sleep 0.2
	instances=`ps ax | grep enfuse | grep -v grep | wc -l`
    done	
    nice -n 19 enfuse --depth 16 -o "$outFn" "$inFnA" "$inFnB" "$inFnC" && mv "$outFn" "$outFinal" &
    sleep 0.2
    outCount=$((outCount+1))
    inCount=$((inCount+1))
    inFnA=`printf "%s/%05d_m.jpg" "$directoryFrom" $inCount`
    inFnB=`printf "%s/%05d_l.jpg" "$directoryFrom" $inCount`
    inFnC=`printf "%s/%05d_h.jpg" "$directoryFrom" $inCount`
    nextOne=`printf "%s/%05d_h.jpg" "$directoryFrom" $((inCount+1))`
    if [ ! -f "$nextOne" ]; then
	echo "We might have catched up with the scan, sleeping 60 seconds"
	sleep 60
    fi
    export spaceLeft=`getAvailableMegabytes ${directoryTo}`
done


if [ "$spaceLeft" -le $MINM ]; then
    echo "THERE'S LESS THAN ${MING}G OF HARD DRIVE SPACE LEFT ON ${directoryTo}, exit!"
fi

