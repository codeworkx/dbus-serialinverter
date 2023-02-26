# dbus-serialinverter
This is a driver for VenusOS devices (any GX device sold by Victron or a Raspberry Pi running the VenusOS image).

The driver will communicate with a inverter that supports serial communication (RS232, RS485 or TTL UART) and publish its data to the VenusOS system. 

## Inspiration
Based on https://github.com/Louisvdw/dbus-serialbattery and https://github.com/fabian-lauer/dbus-solax-x1-pvinverter

## Special remarks
- Early development stage, there's still some work to do
- Currently testing with https://www.waveshare.com/usb-to-rs485.htm and Solis mini 700 4G inverter
- Adding inverters like Growatt MIC (RS485) should be pretty easy

## Todo
- When TYPE is set in config, disable auto detection and use the specified type by default

## Installation
- Make sure you're running VenusOS Large, else you will get errors like:
> ModuleNotFoundError: No module named 'dataclasses'
- Grab a copy of the main branch
- Modify dbus-serialinverter\etc\config.ini
- Copy everything to /data on your VenusOS device (ATTENTION: If /data/conf/serial-starter.d is already there, DO NOT OVERWRITE and add the contents manually!)
- Connect to your VenusOS device via SSH
- Get model and serial of your USB-to-Serial-Converter. Example for /dev/ttyUSB0:
```
udevadm info --query=property --name=/dev/ttyUSB0 | sed -n s/^ID_MODEL=//p
udevadm info --query=property --name=/dev/ttyUSB0 | sed -n s/^ID_SERIAL_SHORT=//p
```
- To prevent other services from bugging your serial converter, modify /etc/udev/rules.d/serial-starter.rules and add following line (replace XXXXXXXX with the values you got in previous step):
```
ACTION=="add", ENV{ID_BUS}=="usb", ENV{ID_MODEL}=="XXXXXXXX", ENV{ID_SERIAL_SHORT}=="XXXXXXXX", ENV{VE_SERVICE}="sinv"
```
- Call the installer:
```
cd /data/etc/dbus-serialinverter
chmod +x install.sh
./install.sh
```
- Reboot!