#/bin/bash



source ftpserver.conf

suffix=$2

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "We need the directory name for the ftp server"
    echo "(not the full path)"
    echo "plz don't use the space character in the name, it's"
    echo "against my religion"
    exit -1
fi

export dirName="$1"

mkdir -p /dev/shm/complete
cd /dev/shm/complete

function sendAndDelete(){
    if [ "$1" == "*.$suffix" ]; then
	#echo no files, sleeping 1 sec
	sleep 1
    else
        ncftpput -u $ftpuser -p $ftppassword $ftpserver ${ftppathprefix}${dirName} $@ && rm -f $@
    fi
}

while [ -f "/dev/shm/transferInProgress.flag" ]; do
    sendAndDelete *.$suffix
done
