#!/bin/bash
#
#
# 
#
################################################################################

USAGE="
  USAGE: $0 <format json file> <project name> <feeder orientation(cw|ccw)>

EXAMPLE: $0 super8.json vacation1986 ccw"

if [ ! -f "$1" ] || [ -z "$2" ] || ( [ "$3" != "cw" ] && [ "$3" != "ccw" ] ); then
    echo "$USAGE"
    exit 0
fi


# check if FTP server is available or exit if not.

# Does the directory exists on the ftp server?

# if not then create it

# else figure out which is last file.



# Is the sendWhileRunning.bash already running?

# if it is then kill it

# start a new sendWhileRunning.bash with proper film name


# start the Gugusse.py
