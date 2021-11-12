#!/usr/bin/env bash
cd "${0%/*}"  # set current directory to the directory in which this script is located
source create_serial.sh &
python fake_cyberamp.py ./tty1