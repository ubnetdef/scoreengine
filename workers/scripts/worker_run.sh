#!/bin/bash
[ "$#" -ne 1 ] && [ "$#" -ne 2 ] && { echo "Usage: $0 <command> ['1' if command should run on a random host]"; exit 1; }

USERNAME="engine"
WORKERS=($(curl -s localhost:8080/workers | jq -r 'keys | .[]'))

if [ "$#" == 2 ]; then
        WORKERS=(${WORKERS[$RANDOM % ${#WORKERS[@]}]})
fi

for w in ${WORKERS[@]}; do
        ip=$(curl -s localhost:8080/worker/$w)

        ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ServerAliveInterval=1 ${USERNAME}@${ip} ${1}
done
