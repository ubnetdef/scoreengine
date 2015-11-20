#!/bin/bash

if [ $# -ne 5 ]; then
	echo "Usage: $0 [host] [port] [domain] [user] [pass]"
	exit 1
fi

## USER CONFIG
# User config is to be done in the ./rdp/rdptest file manually (sorry)
## END USER CONFIG

HOST=$1
PORT=$2
DOMAIN=$3
USER=$4
PASS=$5

COMMAND="/var/scoreengine/scripts/rdp/rdptest $DOMAIN $USER $PASS $HOST $PORT"
OUTPUT=$(eval $COMMAND 2> /dev/null)
RETURN_CODE=$?

echo "ScoreEngine Module: rdp_check"
echo
echo "RUNNING: $COMMAND"
echo "OUTPUT:"
echo $OUTPUT

exit $RETURN_CODE
