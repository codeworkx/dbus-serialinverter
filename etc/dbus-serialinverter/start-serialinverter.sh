#!/bin/bash
set -x

. /opt/victronenergy/serial-starter/run-service.sh

app="python /opt/victronenergy/dbus-serialinverter/dbus-serialinverter.py"
args="/dev/$tty"
start $args