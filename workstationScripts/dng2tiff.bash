#!/bin/bash

MING=2
MINM=$((MING*1024))



function getAvailableMegabytes () {
    df -BM "$1" | tail -n 1 | awk '{print $4}' | tr -d 'M'    
}


USAGE="$0 <dirFrom> [<dirTo>]"

if [ ! -d "$1" ]; then
    echo "$USAGE"
    exit 0
fi

export dirFrom="$1"
if [ -z "$2" ]; then
    export dirTo="$dirFrom"
elif [ ! -d "$2" ]; then
    echo "$USAGE"
    exit 0
else
    export dirTo="$2"
fi

if [ -n "$startPoint" ]; then
    fileCount=$startPoint
else    
    fileCount=0
fi


pushd "$dirTo"
lastFile=`ls *.tiff 2> /dev/null | tail -n 1`
if [ -f "$lastFile" ]; then
    export fileCount=${lastFile%.tiff}
    export fileCount="${fileCount#"${fileCount%%[!0]*}"}"
    export fileCount=$((fileCount+1))
fi
echo "starting file count at $fileCount"
popd

export spaceLeft=`getAvailableMegabytes ${dirTo}`
cd "$dirFrom"
while [ "$spaceLeft" -gt $MINM ]; do
    fin=`printf "%05d.dng" $fileCount`    
    fout=`printf "%05d.tiff" $fileCount`
    export fileCount=$((fileCount+1))
    fnext=`printf "%05d.dng" $fileCount`
    if [ ! -f "$fnext" ]; then
	echo "It seems we caught up with the scan, Sleeping 60 secs"
	sleep 60
    fi
    if [ ! -f "$fin" ]; then
	echo "No more dngs to convert, exiting"
	break
    fi
    echo "converting $fin to $fout"
    if [ "$dirFrom" != "$dirTo" ]; then
	cp "$fin" /dev/shm
	pushd /dev/shm > /dev/null
    fi
    dcraw -6 -w -T "$fin"  && rm "$fin"
    if [ -f "$fin" ]; then
	ls -l
	echo "Something unclear failed, we stop"
	exit 1
    fi
    if [ "$dirFrom" != "$dirTo" ]; then
	mv -f "$fout" "$dirTo"
	popd > /dev/null
    fi    
    export spaceLeft=`getAvailableMegabytes ${dirTo}`
done
export spaceLeft=`getAvailableMegabytes ${dirTo}`
if [ "$spaceLeft" -le $MINM ]; then
    echo "THERE'S LESS THAN ${MING}G OF HARD DRIVE SPACE LEFT ON ${dirTo}, exit!"
fi

