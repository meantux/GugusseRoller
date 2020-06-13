#!/bin/bash
#
#
#
#

pyScript=${0%.bash}.py
pyScript="`basename \"$pyScript\"`"

USAGE="$0 <directoryFrom> <output filename>"

directoryFrom="$1"
outputFilename="$2"


if [ ! -d "$directoryFrom" ] || [ -z "$outputFilename" ]; then
    echo "$USAGE"
    exit 0
fi

if [ ! -f "$directoryFrom/00000_h.jpg" ]; then
    echo "We don't even have a first trio of picture at $directoryFrom"
    echo "$USAGE"
    exit 0
fi

fifo="`mktemp -p /dev/shm -u`"
echo "fifo=${fifo}"

mknod "${fifo}" p

touch "${fifo}.flagIn"
touch "${fifo}.flagOut"

xterm -geometry 132x33 -e "ffmpeg -y -f rawvideo -pix_fmt rgba64le -s 4056x3040  -r 24 -i $fifo -vcodec prores -vb 120M -an $outputFilename ; rm ${fifo}.flagOut" &

python3 ~/bin/$pyScript "${directoryFrom}" "${fifo}"

echo "Waiting for $pyScript to finish"
while [ -f "${fifo}.flagIn" ]; do
    sleep 1
done

echo "Waiting for ffmpeg to finish"
while [ -f "${fifo}.flagOut" ]; do
    sleep 1
done

rm "${fifo}"
echo "${0} done"
