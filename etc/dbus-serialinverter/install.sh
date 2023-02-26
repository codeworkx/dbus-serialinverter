#!/bin/bash
set -x

DRIVERNAME=dbus-serialinverter

# handle read only mounts
sh /opt/victronenergy/swupdate-scripts/remount-rw.sh

# set permissions
chmod 755 /data/etc/$DRIVERNAME/start-serialinverter.sh
chmod 755 /data/etc/$DRIVERNAME/service/run
chmod 755 /data/etc/$DRIVERNAME/service/log/run

# install
rm -rf /opt/victronenergy/service/$DRIVERNAME
rm -rf /opt/victronenergy/service-templates/$DRIVERNAME
rm -rf /opt/victronenergy/$DRIVERNAME

mkdir /opt/victronenergy/$DRIVERNAME
cp -f /data/etc/$DRIVERNAME/* /opt/victronenergy/$DRIVERNAME &>/dev/null
cp -rf /data/etc/$DRIVERNAME/pymodbus /opt/victronenergy/$DRIVERNAME/ &>/dev/null
cp -rf /data/etc/$DRIVERNAME/service /opt/victronenergy/service-templates/$DRIVERNAME

# restart if running
pkill -f "python .*/$DRIVERNAME.py"

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]; then
    echo "#!/bin/bash" >> $filename
    chmod 755 $filename
fi
grep -qxF "sh /data/etc/$DRIVERNAME/install.sh" $filename || printf '\n%s' "sh /data/etc/$DRIVERNAME/install.sh" >> $filename
