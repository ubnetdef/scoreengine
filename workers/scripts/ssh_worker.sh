#!/bin/bash

[ "$#" -ne 2 ] && { echo "Usage: $0 username worker-hostname"; exit 1; }

USERNAME=$1
WORKER=$2
WORKER_IP=$(curl -s http://localhost:8080/worker/$WORKER)

if [ "$WORKER_IP" == "127.0.0.1" ]; then
        echo "Unknown worker $WORKER!"
        exit 1
fi

ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ${USERNAME}@${WORKER_IP}
