# -*- coding: utf-8 -*-
from typing import Union, Tuple, List

from utils import logger
import utils
import logging
import math
from datetime import timedelta
from time import time
from abc import ABC, abstractmethod

class Inverter(ABC):
    """
    This Class is the abstract baseclass for all inverters. For each inverter this class needs to be extended
    and the abstract methods need to be implemented. The main program in dbus-serialinverter.py will then
    use the individual implementations as type Inverter and work with it.
    """

    def __init__(self, port, baudrate, slave):
        self.port = port
        self.baudrate = baudrate
        self.slave = slave
        self.role = "inverter"
        self.type = "Generic"
        self.poll_interval = 1000
        self.online = True

        # Static data
        self.hardware_version = 0x0
        self.software_version = 0x0
        self.serial_number = None

        self.max_ac_power = None
        self.positon = None
        self.phase = None
        
        self.status = None

        # Energy data
        self.energy_data = dict()
        
        for phase in ["L1", "L2", "L3"]:
            self.energy_data[phase] = dict()
            self.energy_data[phase]['ac_voltage'] = None
            self.energy_data[phase]['ac_current'] = None
            self.energy_data[phase]['ac_power'] = None
            self.energy_data[phase]['energy_forwarded'] = None

        self.energy_data["overall"] = dict()
        self.energy_data['overall']['ac_voltage'] = None
        self.energy_data['overall']['ac_current'] = None
        self.energy_data['overall']['ac_power'] = None
        self.energy_data['overall']['power_limit'] = None
        self.energy_data['overall']['energy_forwarded'] = None

    @abstractmethod
    def test_connection(self) -> bool:
        """
        This abstract method needs to be implemented for each inverter. It should return true if a connection
        to the inverter can be established, false otherwise.
        :return: the success state
        """
        # Each driver must override this function to test if a connection can be made
        # return false when failed, true if successful
        return False

    @abstractmethod
    def get_settings(self) -> bool:
        """
        Each driver must override this function to read/set the inverter settings
        It is called once after a successful connection by DbusHelper.setup_vedbus()
        Values: FIXME

        :return: false when fail, true if successful
        """
        return False

    @abstractmethod
    def refresh_data(self) -> bool:
        """
        Each driver must override this function to read inverter data and populate this class
        It is called each poll just before the data is published to vedbus

        :return:  false when fail, true if successful
        """
        return False

    def log_settings(self) -> None:
        logger.info(f"Inverter {self.type} connected to dbus from {self.port}")
        logger.info("=== Settings ===")
        logger.info(f"> Serial number: %s" % self.serial_number)
        logger.info(f"> Hardware version: %s" % self.hardware_version)
        logger.info(f"> Software version: %s" % self.software_version)
        logger.info(f"> Max. AC power: %s" % self.max_ac_power)
        logger.info(f"> Phase: %s" % self.phase)
        logger.info(f"> Position: %s" % self.position)
        return