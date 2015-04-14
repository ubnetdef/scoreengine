#!/bin/bash
if [ $# -ne 4 ]; then
	echo "Usage: $0 [host] [port] [user] [pass]"
	exit 1
fi

## USER CONFIG
# Time limit, in seconds
TIMELIMIT=5

# File to upload
TESTFILE="fill_in_here"
## END USER CONFIG

##input arguments for FTP check with file option in comment
HOST=$1
PORT=$2
USER=$3
PASS=$4

## Establishes FTP connection, uploads and checks for file
ftp -in $HOST << EOF_FTP > $FTPLOG
user $USER $PASS
verbose
#put $TESTFILE
put ftptest 
#ls $TESTFILE
ls ftptest
close
quit
EOF_FTP

##greps "completed" statements for both put and ls commands
EXPECTED_OUTPUT=2 
COMMAND="grep -c 'complete' $FTPLOG"
OUTPUT=$(eval $COMMAND)

echo "ScoreEngine Module: ftp_check"
echo
echo "EXPECTED: $EXPECTED_OUTPUT"
echo "OUTPUT: $OUTPUT"

#returns 0 if file is uploaded, 1 for any other failure
if [ $OUTPUT == $EXPECTED_OUTPUT ]; then
	exit 0;
else
	exit 1;
fi
