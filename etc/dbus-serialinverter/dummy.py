# -*- coding: utf-8 -*-
import sys
import os

from inverter import Inverter
from utils import logger
import utils

class Dummy(Inverter):
    INVERTERTYPE = "Dummy"
    
    def __init__(self, port, baudrate, slave):
        super(Dummy, self).__init__(port, baudrate, slave)
        self.type = self.INVERTERTYPE
        
    def test_connection(self):
        return self.get_settings()

    def get_settings(self):
        if (utils.INVERTER_TYPE == "Dummy"):
            # Static info from config
            self.max_ac_power = utils.INVERTER_MAX_AC_POWER
            self.phase = utils.INVERTER_PHASE
            self.poll_interval = utils.INVERTER_POLL_INTERVAL
            self.position = utils.INVERTER_POSITION

            # Hardware version
            self.hardware_version = "1.0.0"

            # Serial number  
            self.serial_number = 12345678

	       # Power limit
            self.energy_data['overall']['power_limit'] = utils.INVERTER_MAX_AC_POWER
        
            return True
        else:
            return False

    def refresh_data(self):
        # call all functions that will refresh the inverter data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()
        return result

    def read_status_data(self):
        # Energy data
        power = self.energy_data['overall']['power_limit']
        
        self.energy_data["L1"]['ac_voltage'] = 230.0
        self.energy_data["L1"]['ac_current'] = power / 230
        self.energy_data["L1"]['ac_power'] = power
        self.energy_data["L1"]['energy_forwarded'] = 0.1

        self.energy_data["L2"]['ac_voltage'] = 0.0
        self.energy_data["L2"]['ac_current'] = 0.0
        self.energy_data["L2"]['ac_power'] = 0.0
        self.energy_data["L2"]['energy_forwarded'] = 0.0
            
        self.energy_data["L3"]['ac_voltage'] = 0.0
        self.energy_data["L3"]['ac_current'] = 0.0
        self.energy_data["L3"]['ac_power'] = 0.0
        self.energy_data["L3"]['energy_forwarded'] = 0.0

        self.energy_data['overall']['ac_power'] = power
        self.energy_data['overall']['energy_forwarded'] = 0.1

        self.status = 7

        return True
