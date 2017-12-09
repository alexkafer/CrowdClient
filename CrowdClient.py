#!/usr/bin/python
"""This is the super fun main file to run the whole thing. Be nice."""

import platform
import sys
import time
import threading

import libraries

from libraries.PixelManager import PixelManager, Color
from serial.serialutil import SerialException
from libraries.EnttecUsbDmxPro import EnttecUsbDmxPro


print "Welcome to the Crowd Interaction software. We put the cool in cool beans."
PIXELS = PixelManager()
DMX = EnttecUsbDmxPro()

DPORT = None
if len(sys.argv) < 2:
    if platform.system() == 'Linux':
        DPORT = '/dev/ttyUSB0'
    elif platform.system() == 'Darwin':
        DPORT = '/dev/tty.usbserial-EN215593'
        # Erwin: tty.usbserial-EN215593
        # Timmy: tty.usbserial-EN17533
else:
    DPORT = sys.argv[1]

if DPORT is None:
    DMX.list()
    sys.stderr.write("ERROR: No serial port for DMX detected!\n")
    sys.exit()

DMX.setPort(DPORT)

try:
    DMX.connect()
    PIXELS.link_dmx(DMX)
except SerialException:
    print "Unable to connect to USB to DMX converter. Is Timmy (Erwin) alive? Proceeding without DMX"

PIXELS.start_websocket()

PIXELS.set_color(0,0, Color.RED)
PIXELS.render_update()
