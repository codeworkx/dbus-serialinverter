# -*- coding: utf-8 -*-
import sys
import os

from inverter import Inverter
from utils import logger
import utils

sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-serialinverter/pymodbus",
    ),
)

from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

class Solis(Inverter):
    INVERTERTYPE = "Solis"
    
    def __init__(self, port, baudrate, slave):
        super(Solis, self).__init__(port, baudrate, slave)
        self.type = self.INVERTERTYPE

        self.client = ModbusSerialClient(method = 'rtu', port = port, baudrate = baudrate, stopbits = 1, parity = 'N', bytesize = 8, timeout = 1)
        logger.info("Creating ModbusSerialClient on port %s with baudrate %s" % (port, baudrate))
        
    def test_connection(self):
        try:
            logger.debug("test_connection(): Connected!")
            # Product model
            success, self.product_model = self.read_input_registers(2999, 1, "u16", 1, 0)
            if (success):
                logger.debug("Product model: %s" % self.product_model)
                if (self.product_model == 224):
                    return self.get_settings()
                else:
                    logger.warn("Unsupported product model: %s" % self.product_model)
                    return False
            else:
                return False
        except IOError:
            logger.debug("test_connection(): IOError")
            return False

    def get_settings(self):
        # Static info from config
        self.max_ac_power = utils.INVERTER_MAX_AC_POWER
        self.phase = utils.INVERTER_PHASE
        self.poll_interval = utils.INVERTER_POLL_INTERVAL
        self.position = utils.INVERTER_POSITION

        # Software version
        success, self.hardware_version = self.read_input_registers(3000, 1, "u16", 1, 0)
        logger.debug("DSP version: %s" % self.hardware_version)

        # Serial
        res = self.client.read_input_registers(address = 3060,
                                count = 4,
                                slave = self.slave)

        if not res.isError():
            serialparts = []
            for x in res.registers:
                serialparts.append((hex(x)[2:])[::-1])
            
            self.serial_number = ''.join(serialparts)
            logger.debug("Serial: %s" % self.serial_number)
        else:
            logger.debug("Error reading serial number")
            return False

        # Power limit
        success, power_limit = self.read_input_registers(3049, 1, "u16", 0.01, 0)
        if (success):
            power_limit_watts = float(self.max_ac_power * (int(power_limit) / 100))
            self.energy_data['overall']['power_limit'] = power_limit_watts
            self.energy_data['overall']['active_power_limit'] = power_limit_watts
            logger.debug("Active power limit: %d W (%d %%)" % (power_limit_watts, power_limit))
        
        return True

    def refresh_data(self):
        # call all functions that will refresh the inverter data.
        # This will be called for every iteration (1 second)
        # Return True if success, False for failure
        result = self.read_status_data()
        return result

    def read_input_registers(self, address, count, data_type, scale, digits):
        connection = self.client.connect()
        if (connection):
            res = self.client.read_input_registers(address = address,
                                    count = count,
                                    slave = self.slave)

            logger.debug("Read input register - address=%s, count=%s, slave=%s" % (address, count, self.slave))

            if not res.isError():
                decoder = BinaryPayloadDecoder.fromRegisters(res.registers, Endian.Big)

                if (data_type == 'string'):
                    data = decoder.decode_string(8)
                elif (data_type == 'float'):
                    data = decoder.decode_32bit_float()  
                elif (data_type == 'u16'):
                    data = decoder.decode_16bit_uint()  
                elif (data_type == 'u32'):
                    data = decoder.decode_32bit_uint()      
                else:
                    logger.warn("Unsupported data type specified: %s" % data_type)
                    return False, 0

                logger.debug("Register: %s - Raw data: %s" % (address, data))

                # Scale
                data = round(data * scale, digits)
                logger.debug("Register: %s - Scaled data: %s" % (address, data))
                return True, data
            else:
                logger.error("Error reading register %s" % address)
                logger.debug(res)
        else:
            logger.error("No connection")

        return False, 0

    def write_registers(self, address, value):
        connection = self.client.connect()
        if (connection):
            res = self.client.write_registers(address, value, slave = self.slave)
            logger.debug("Write register - address=%s, value=%s, slave=%s" % (address, value, self.slave))
            if not res.isError():
                logger.debug(res)
                return True
            else:
                logger.error("Error writing register %s" % address)
        else:
            logger.error("No connection")

        return False

    def read_status_data(self):
        error = False

        # Output type: Single or 3-Phase inverter
        success, output_type = self.read_input_registers(3002, 1, "u16", 1, 0)
        if (not success):
            error = True

        # AC power overall
        success, self.energy_data['overall']['ac_power'] = self.read_input_registers(3004, 2, "u32", 1, 0)
        if (not success):
            error = True

        # Energy forwarded overall
        success, self.energy_data['overall']['energy_forwarded'] = self.read_input_registers(3014, 1, "u16", 0.1, 2)
        if (not success):
            error = True

        if (output_type == 0):
            # Single phase inverter

            for phase in ['L1', 'L2', 'L3']:
                self.energy_data[phase]['ac_voltage'] = 0.0
                self.energy_data[phase]['ac_current'] = 0.0
                self.energy_data[phase]['ac_power'] = 0.0
                self.energy_data[phase]['energy_forwarded'] = 0.0
            
            # AC voltage phase
            success, self.energy_data[self.phase]['ac_voltage'] = self.read_input_registers(3035, 1, "u16", 0.1, 0)
            if (not success):
                error = True

            # AC current phase
            success, self.energy_data[self.phase]['ac_current'] = self.read_input_registers(3038, 1, "u16", 0.1, 2)
            if (not success):
                error = True

            # AC power phase
            self.energy_data[self.phase]['ac_power'] = self.energy_data['overall']['ac_power']

            # Energy forwarded
            self.energy_data[self.phase]['energy_forwarded'] = self.energy_data['overall']['energy_forwarded']
        else:
            # 3-Phase inverter
            # AC voltage L1
            success, self.energy_data['L1']['ac_voltage'] = self.read_input_registers(3033, 1, "u16", 0.1, 0)
            if (not success):
                error = True

            # AC voltage L2
            success, self.energy_data['L2']['ac_voltage'] = self.read_input_registers(3034, 1, "u16", 0.1, 0)
            if (not success):
                error = True

            # AC voltage L3
            success, self.energy_data['L3']['ac_voltage'] = self.read_input_registers(3035, 1, "u16", 0.1, 0)
            if (not success):
                error = True

            # AC current L1
            success, self.energy_data['L1']['ac_current'] = self.read_input_registers(3036, 1, "u16", 0.1, 2)
            if (not success):
                error = True

            # AC current L2
            success, self.energy_data['L2']['ac_current'] = self.read_input_registers(3037, 1, "u16", 0.1, 2)
            if (not success):
                error = True

            # AC current L3
            success, self.energy_data['L3']['ac_current'] = self.read_input_registers(3038, 1, "u16", 0.1, 2)
            if (not success):
                error = True

            # Energy forwarded L1
            self.energy_data['L1']['energy_forwarded'] = 0

            # Energy forwarded L2
            self.energy_data['L2']['energy_forwarded'] = 0

            # Energy forwarded L3
            self.energy_data['L3']['energy_forwarded'] = 0

        # Status
        success, status = self.read_input_registers(3043, 1, "u16", 1, 0)
        if (success):
            # Victron: # 0=Startup 0; 1=Startup 1; 2=Startup 2; 3=Startup 3; 4=Startup 4; 5=Startup 5; 6=Startup 6; 7=Running; 8=Standby; 9=Boot loading; 10=Error
            if (status == 0):
                self.status = 0 # Waiting
            elif (status == 1):
                self.status = 1 # OpenRun
            elif (status == 2):
                self.status = 2 # SoftRun
            elif (status == 3):
                self.status = 7 # Generating
            else:
                self.status = 10 # Fault
        else:
            self.status = 8 # Off
            error = True

        logger.debug("Inverter status: %s" % self.status)

        # Power limit
        success, power_limit = self.read_input_registers(3049, 1, "u16", 0.01, 0)
        if (success):
            power_limit_watts = float(self.max_ac_power * (int(power_limit) / 100))
            self.energy_data['overall']['active_power_limit'] = power_limit_watts
            logger.debug("Active power limit: %d W (%d %%)" % (power_limit_watts, power_limit))

            if (power_limit_watts != self.energy_data['overall']['power_limit']):
                new_power_limit = self.energy_data['overall']['power_limit'] / (self.max_ac_power / 100)
                logger.info("Power limit has changed from %s to %s" % (power_limit, new_power_limit))
                self.write_registers(3051, int(new_power_limit) * 100)
        else:
            error = True

        # Check if error or not
        if (not error):
            return True
        else:
            return False