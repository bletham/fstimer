#!/bin/sh
cd "$(dirname "$0")"
nohup /opt/local/bin/python3.5 fstimer.py &
killall Terminal