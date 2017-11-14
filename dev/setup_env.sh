#!/bin/bash

if [ -z "$1" ]; then
	echo "Usage: $0 /path/to/requirements.txt"
	exit 1
fi

# Fix for OSX
pip install \
	-r $1 \
	--global-option=build_ext \
	--global-option="-I$(xcrun --show-sdk-path)/usr/include/sasl"