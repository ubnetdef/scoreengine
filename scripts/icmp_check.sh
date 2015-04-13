#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: $0 [host]"
	exit 1
fi

## USER CONFIG
# Time limit, in seconds
TIMELIMIT="5"

## END USER CONFIG

HOST=$1
EXPECTED_OUTPUT=2

COMMAND="ping -c 1 -t $TIMELIMIT $HOST | grep bytes | wc -l"
OUTPUT=$(eval $COMMAND)

echo "ScoreEngine Module: icmp_check"
echo
echo "RUNNING: $COMMAND"
echo "EXPECTED: $EXPECTED_OUTPUT"
echo "OUTPUT: $OUTPUT"

if [ $OUTPUT -eq $EXPECTED_OUTPUT ]; then
	exit 0;
else
	exit 1;
fi