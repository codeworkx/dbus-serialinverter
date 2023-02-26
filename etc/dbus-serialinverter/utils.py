# -*- coding: utf-8 -*-
import logging

import configparser
from pathlib import Path
from typing import List, Any, Callable

# Constants
DRIVER_VERSION = 0.1
DRIVER_SUBVERSION = ".1"

# Logging
logging.basicConfig()
logger = logging.getLogger("SerialInverter")
logger.setLevel(logging.INFO)

# Config
config = configparser.ConfigParser()
path = Path(__file__).parents[0]
config_file_path = path.joinpath("config.ini").absolute().__str__()
config.read([config_file_path])

PUBLISH_CONFIG_VALUES = int(config["DEFAULT"]["PUBLISH_CONFIG_VALUES"])

INVERTER_TYPE = config["INVERTER"]["TYPE"]
INVERTER_MAX_AC_POWER = int(config["INVERTER"]["MAX_AC_POWER"])
INVERTER_PHASE = config['INVERTER']['PHASE'] # L1; L2; L3
INVERTER_POLL_INTERVAL = int(config['INVERTER']['POLL_INTERVAL'])
INVERTER_POSITION = int(config['INVERTER']['POSITION']) # 0 = AC input 1; 1 = AC output; 2 = AC input 2

locals_copy = locals().copy()

def publish_config_variables(dbusservice):
    for variable, value in locals_copy.items():
        if variable.startswith("__"):
            continue
        if (
            isinstance(value, float)
            or isinstance(value, int)
            or isinstance(value, str)
            or isinstance(value, List)
        ):
            dbusservice.add_path(f"/Info/Config/{variable}", value)