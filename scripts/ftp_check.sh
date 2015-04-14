#!/bin/bash
if [ $# -ne 4 ]; then
	echo "Usage: $0 [host] [port] [user] [pass]"
	exit 1
fi

UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)

## USER CONFIG
# Time limit, in seconds
TIMELIMIT=5

# File to upload
TESTFILE_LOCAL="/tmp/scoreengine-check-file"
TESTFILE_REMOTE="scoreengine-$UUID.check"
## END USER CONFIG

if [ ! -f $TESTFILE_LOCAL ]; then
	touch $TESTFILE_LOCAL
fi

HOST=$1
PORT=$2
USER=$3
PASS=$4

COMMAND="lftp -u $USER,$PASS -e 'set net:timeout $TIMELIMIT; set net:max-retries 1; put $TESTFILE_LOCAL -o $TESTFILE_REMOTE; ls; rm $TESTFILE_REMOTE; quit' $HOST:$PORT"

EXPECTED_OUTPUT="File $TESTFILE_REMOTE sucessfully uploaded AND removed" 
OUTPUT=$(eval $COMMAND 2> /dev/null)
ACTUAL=$(echo $OUTPUT | grep -c "$TESTFILE_REMOTE")

echo "ScoreEngine Module: ftp_check"
echo
echo "RUNNING: $COMMAND"
echo
echo "EXPECTED: $EXPECTED_OUTPUT"
echo
echo "OUTPUT:"
echo "$OUTPUT"

if [ "$ACTUAL" == 1 ]; then
	exit 0;
else
	exit 1;
fi
