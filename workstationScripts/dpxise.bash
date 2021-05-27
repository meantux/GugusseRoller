#!/bin/bash

USAGE="$0 <directory from> [<directory to>] [<extras options>] [evaluate min value if not 50]"

if [ -z "$1" ] || [ ! -d "$1" ]; then
    echo "first parameter is required and must be a directory"
    echo "$USAGE"
    exit 1
fi
if [ -n "$2" ] && [ ! -d "$2" ]; then
    echo "if there is a second parameter it must be a directory"
    echo "$USAGE"
    exit 1
fi

pushd "$1"

extras="$3"

if [ -n "$4" ]; then
    value=$4
else
    value=50
fi




here="`pwd`"
if [ -z "$2" ]; then
    outDir="$here"
else
    outDir="$2"
fi

workfile=`mktemp`
count=1
while [ "$count" -gt 0 ]; do
    ls *.jpg > $workfile
    sleep 8
    count=0
    for i in `cat $workfile` ; do
	if [ "$value" -eq 100 ] || [ "$value" -eq 0 ]; then
	    nice convert "$i" "${outDir}/${i%.jpg}.dpx"
	    err=$?
	else	    
 	    nice convert "$i" $extras  -evaluate Min ${value}% "${outDir}/${i%.jpg}.dpx"
	    err=$?
	fi	    
	echo "$i -> ${outDir}/${i%.jpg}.dpx"
	if [ $err -eq 0 ] ; then
	    if [ "$outDir" == "$here" ]; then
		rm "$i"
	    fi
	    count=$((count+1))
	else
	    exit -1
	fi
    done
    echo batch done
    sleep 8
done
rm $workfile
	
	
	
