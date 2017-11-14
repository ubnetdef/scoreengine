#!/bin/bash

## CONFIGURATION
IP_RANGE_3_START=1
IP_RANGE_3_END=2

IP_RANGE_4_START=1
IP_RANGE_4_END=254

IP_PREFIX="192.168"
## /CONFIGURATION

generate_ip() {
	octect3=$(shuf -i ${IP_RANGE_3_START}-${IP_RANGE_3_END} -n 1)
	octect4=$(shuf -i ${IP_RANGE_4_START}-${IP_RANGE_4_END} -n 1)

	echo "$IP_PREFIX.$octect3.$octect4"
}

ip_in_use() {
	ip=$1

	ping -c 1 -t 1 $ip > /dev/null
	ip_in_use=$(/usr/sbin/arp $ip | grep "(incomplete)")

	if [ "$?" == "0" ]; then
		return 1
	fi
	return 0
}

## MAIN STUFF
ip=$(generate_ip)
while $(ip_in_use $ip); do
	ip=$(generate_ip)
done

## Update the IP
sed -i -r "s/address (.*?)$/address $ip/g" /etc/network/interfaces

## Alert the IP
echo "$(hostname) = $ip"

## Reboot
reboot