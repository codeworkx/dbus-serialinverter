#!/usr/bin/env python
import platform 
import sys

from time import sleep
from typing import Union
from threading import Thread

from dbus.mainloop.glib import DBusGMainLoop

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject

from dbushelper import DbusHelper
from utils import logger
import utils

from inverter import Inverter
from dummy import Dummy
from solis import Solis

supported_inverter_types = [
    {"inverter": Dummy, "baudrate": 0, "slave": 0},
    {"inverter": Solis, "baudrate": 9600, "slave": 1},
]

expected_inverter_types = [
    inverter_type
    for inverter_type in supported_inverter_types
    if inverter_type["inverter"].__name__ == utils.INVERTER_TYPE or utils.INVERTER_TYPE == ""
]

def main():
    def poll_inverter(loop):
        # Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
        poller = Thread(target=lambda: helper.publish_inverter(loop))
        # Thread will die with us if deamon
        poller.daemon = True
        poller.start()
        return True

    def get_inverter(_port) -> Union[Inverter, None]:
        # all the different inverters the driver support and need to test for
        # try to establish communications with the inverter 3 times, else exit
        count = 3
        while count > 0:
            # create a new inverter object that can read the inverter and run connection test
            for test in expected_inverter_types:
                logger.info("Testing " + test["inverter"].__name__)
                inverterClass = test["inverter"]
                baudrate = test["baudrate"]
                inverter: Inverter = inverterClass(
                    port=_port, baudrate=baudrate, slave=test.get("slave")
                )
                if inverter.test_connection():
                    logger.info(
                        "Connection established to " + inverter.__class__.__name__
                    )
                    return inverter
            count -= 1
            sleep(0.5)

        return None

    def get_port() -> str:
        # Get the port we need to use from the argument
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            # just for MNB-SPI
            logger.info("No Port needed")
            return "/dev/tty/USB9"

    logger.info("Start dbus-serialinverter");

    port = get_port()
    inverter: Inverter = get_inverter(port)

    if inverter is None:
        logger.error("ERROR >>> No inverter connection at " + port)
        sys.exit(1)

    inverter.log_settings()

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    if sys.version_info.major == 2:
        gobject.threads_init()
    mainloop = gobject.MainLoop()

    # Get the initial values for the inverter used by setup_vedbus
    helper = DbusHelper(inverter)

    if not helper.setup_vedbus():
        logger.error("ERROR >>> Problem with inverter set up at " + port)
        sys.exit(1)

    # Poll the inverter at INTERVAL and run the main loop
    gobject.timeout_add(inverter.poll_interval, lambda: poll_inverter(mainloop))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
