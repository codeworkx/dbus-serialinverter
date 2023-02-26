# -*- coding: utf-8 -*-
import sys
import os
import platform
import dbus
import traceback

# Victron packages
sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)

from vedbus import VeDbusService
from settingsdevice import SettingsDevice
import inverter

from utils import logger
import utils

def get_bus():
    return (
        dbus.SessionBus()
        if "DBUS_SESSION_BUS_ADDRESS" in os.environ
        else dbus.SystemBus()
    )

class DbusHelper:
    def __init__(self, inverter):
        self.inverter = inverter
        self.instance = 1
        self.settings = None
        self.error_count = 0
        self._dbusservice = VeDbusService(
            "com.victronenergy.pvinverter."
            + self.inverter.port[self.inverter.port.rfind("/") + 1 :],
            get_bus(),
        )

    def setup_instance(self):
        inverter_id = self.inverter.port[self.inverter.port.rfind("/") + 1 :]
        path = "/Settings/Devices/serialinverter"
        default_instance = "inverter:20" # pvinverters from 20-29
        settings = {
            "instance": [
                path + "_" + str(inverter_id).replace(" ", "_") + "/ClassAndVrmInstance",
                default_instance,
                0,
                0,
            ],
        }
        self.settings = SettingsDevice(get_bus(), settings, self.handle_changed_setting)
        self.inverter.role, self.instance = self.get_role_instance()

    def get_role_instance(self):
        val = self.settings["instance"].split(":")
        logger.info("DeviceInstance = %d", int(val[1]))
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == "instance":
            self.inverter.role, self.instance = self.get_role_instance()
            logger.info("Changed DeviceInstance = %d", self.instance)
            return
        logger.info("Changed DeviceInstance = %d", self.instance)

    def setup_vedbus(self):
        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        # This is only called once when a inverter is initiated
        self.setup_instance()
        short_port = self.inverter.port[self.inverter.port.rfind("/") + 1 :]
        logger.info("%s" % ("com.victronenergy.pvinverter." + short_port))

        # Get the settings for the inverter
        if not self.inverter.get_settings():
            return False

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion", "Python " + platform.python_version()
        )
        self._dbusservice.add_path("/Mgmt/Connection", "Serial " + self.inverter.port)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", self.instance)
        self._dbusservice.add_path("/ProductId", 41284, gettextcallback = lambda p, v: ('a144')) # VE_PROD_ID_PV_INVERTER_FRONIUS
        self._dbusservice.add_path(
            "/ProductName", "SerialInverter (" + self.inverter.type + ")"
        )
        self._dbusservice.add_path(
            "/FirmwareVersion", str(utils.DRIVER_VERSION) + utils.DRIVER_SUBVERSION
        )
        self._dbusservice.add_path("/HardwareVersion", self.inverter.hardware_version)
        self._dbusservice.add_path("/Connected", 1)
        self._dbusservice.add_path(
            "/CustomName", "SerialInverter (" + self.inverter.type + ")", writeable=True
        )

        # Create static inverter info
        self._dbusservice.add_path('/Ac/MaxPower', self.inverter.max_ac_power)
        self._dbusservice.add_path('/Position', self.inverter.position)
        self._dbusservice.add_path('/Serial', self.inverter.serial_number)
        self._dbusservice.add_path('/StatusCode', 0, gettextcallback=lambda p, v: ('Off'))
        self._dbusservice.add_path('/UpdateIndex', 0)

        # Create dynamic inverter info
        self._dbusservice.add_path("/Ac/L1/Voltage", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' V'))
        self._dbusservice.add_path("/Ac/L1/Current", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' A'))
        self._dbusservice.add_path("/Ac/L1/Power", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' W'))
        self._dbusservice.add_path("/Ac/L1/Energy/Forward", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 2)) + ' KWh'))

        self._dbusservice.add_path("/Ac/L2/Voltage", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' V'))
        self._dbusservice.add_path("/Ac/L2/Current", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' A'))
        self._dbusservice.add_path("/Ac/L2/Power", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' W'))
        self._dbusservice.add_path("/Ac/L2/Energy/Forward", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 2)) + ' KWh'))
        
        self._dbusservice.add_path("/Ac/L3/Voltage", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' V'))
        self._dbusservice.add_path("/Ac/L3/Current", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' A'))
        self._dbusservice.add_path("/Ac/L3/Power", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' W'))
        self._dbusservice.add_path("/Ac/L3/Energy/Forward", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 2)) + ' KWh'))

        self._dbusservice.add_path("/Ac/Voltage", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' V'))
        self._dbusservice.add_path("/Ac/Current", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' A'))
        self._dbusservice.add_path("/Ac/Power", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' W'))
        self._dbusservice.add_path('/Ac/PowerLimit', self.inverter.energy_data['overall']['power_limit'], writeable=True, gettextcallback=lambda p, v: (str(round(v, 1)) + ' W'))
        self._dbusservice.add_path("/Ac/Energy/Forward", 0, writeable=True, gettextcallback=lambda p, v: (str(round(v, 2)) + ' KWh'))

        logger.info(f"Publish config values = {utils.PUBLISH_CONFIG_VALUES}")
        if utils.PUBLISH_CONFIG_VALUES == 1:
            utils.publish_config_variables(self._dbusservice)

        return True

    def publish_inverter(self, loop):
        # This is called every inverter.poll_interval milli second as set up per inverter type to read and update the data
        try:
            # Call the inverter's refresh_data function
            success = self.inverter.refresh_data()
            if success:
                self.error_count = 0
                self.inverter.online = True
                self.inverter.poll_interval = utils.INVERTER_POLL_INTERVAL
            else:
                self.error_count += 1
                # If the inverter is offline for more than 10 polls (polled every second for most inverters)
                if self.error_count >= 10:
                    self.inverter.online = False
                # Has it completely failed
                if self.error_count >= 60:
                    logger.warn("Inverter seems to be offline, quitting!")
                    loop.quit()
                    #self.inverter.poll_interval = 900000 # 15 Mins
                    #logger.warn("Inverter seems to be offline, changing poll interval to %s seconds" % (self.inverter.poll_interval / 1000))

            # Publish all the data from the inverter object to dbus
            self.publish_dbus()

        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        self._dbusservice['/StatusCode'] = self.inverter.status

        self._dbusservice['/Ac/L1/Voltage'] = self.inverter.energy_data['L1']['ac_voltage']
        self._dbusservice['/Ac/L1/Current'] = self.inverter.energy_data['L1']['ac_current']
        self._dbusservice['/Ac/L1/Power'] = self.inverter.energy_data['L1']['ac_power']
        self._dbusservice['/Ac/L1/Energy/Forward'] = self.inverter.energy_data['L1']['energy_forwarded']
        
        self._dbusservice['/Ac/L2/Voltage'] = self.inverter.energy_data['L2']['ac_voltage']
        self._dbusservice['/Ac/L2/Current'] = self.inverter.energy_data['L2']['ac_current']
        self._dbusservice['/Ac/L2/Power'] = self.inverter.energy_data['L2']['ac_power']
        self._dbusservice['/Ac/L2/Energy/Forward'] = self.inverter.energy_data['L2']['energy_forwarded']
        
        self._dbusservice['/Ac/L3/Voltage'] = self.inverter.energy_data['L3']['ac_voltage']
        self._dbusservice['/Ac/L3/Current'] = self.inverter.energy_data['L3']['ac_current']
        self._dbusservice['/Ac/L3/Power'] = self.inverter.energy_data['L3']['ac_power']
        self._dbusservice['/Ac/L3/Energy/Forward'] = self.inverter.energy_data['L3']['energy_forwarded']
        
        self._dbusservice['/Ac/Voltage'] = self.inverter.energy_data['overall']['ac_voltage']
        self._dbusservice['/Ac/Current'] = self.inverter.energy_data['overall']['ac_current']
        self._dbusservice['/Ac/Power'] = self.inverter.energy_data['overall']['ac_power']
        self._dbusservice['/Ac/PowerLimit'] = self.inverter.energy_data['overall']['power_limit']
        self._dbusservice['/Ac/Energy/Forward'] = self.inverter.energy_data['overall']['energy_forwarded']

        # Increment UpdateIndex - to show that new data is available
        index = self._dbusservice['/UpdateIndex'] + 1  # increment index
        if index > 255:   # Maximum value of the index
            index = 0       # Overflow from 255 to 0
        self._dbusservice['/UpdateIndex'] = index

        logger.debug("published to dbus [%s]" % str(self.inverter.energy_data['overall']['energy_forwarded']))