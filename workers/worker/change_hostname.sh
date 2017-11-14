#!/bin/bash
OLD=$(cat /etc/hostname)
NEW=$1

sed -i "s/$OLD/$NEW/g" /etc/hosts
sed -i "s/$OLD/$NEW/g" /etc/hostname
hostname $NEW
