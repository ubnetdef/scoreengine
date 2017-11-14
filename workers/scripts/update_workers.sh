#!/bin/bash

#
# NOTE: This is the only script that is
# super 'custom' and should only be ran if
# you have the following setup:
#
# - scoreengine installed to ~/scoreengine
# - You modify the variable 'ENGINE_IP'
# - You comment out (add a '#' in the start of the line)
# to the next two lines
#
echo "Please read this file ($0) before running."
exit 1

ENGINE_IP="192.168.2.50"

pushd ~/scoreengine
(python -m SimpleHTTPServer 9090 > /dev/null) &
SERVER_PID=$!
popd

./worker_run.sh "cd scoreengine; git pull; rm -f config.py; wget ${ENGINE_IP}:9090/config.py -O config.py"

kill $SERVER_PID
