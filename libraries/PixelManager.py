""" Pixel Manager with Data Storage, Websocket, and HTTP Get Interface """
from enum import Enum
import json
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError

import websocket

NET_LIGHT_WIDTH = 12 # Number of columns
NET_LIGHT_HEIGHT = 5 # Number of rows

class Color(Enum):
    """ Three options of the Net Lights. Off, Red, and Green """
    OFF = 0
    RED = 1
    GREEN = 2
    BOTH = 3

class ColorEncoder(json.JSONEncoder):
    """ Allow color to be encoded with the JSONEncoder """
    def default(self, o): # pylint: disable=E0202
        if isinstance(o, Color):
            return o.value
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)

class PixelManager(object):
    """ Pixel Manager with Data Storage, Websocket, and HTTP Get Interface """
    def __init__(self, websocket_port=8080, webserver_port=80):
        """ Initializes the pixels to the correct size and pre-sets everything to OFF """
        self.pixels = [[Color.OFF for x in range(NET_LIGHT_WIDTH)] for y in range(NET_LIGHT_HEIGHT)]
        self.dmx = None

        config = RawConfigParser()
        config.read('DMX.cfg')

        self.dmxmap = []
        for row in range(NET_LIGHT_HEIGHT):
            for col in range(NET_LIGHT_WIDTH):
                def read_color_config(name, row, col):
                    """ Small helper function to pull DMX channels for a name, row, and col """
                    try:
                        color = config.getint(name, str(col) + ',' + str(row))
                    except NoSectionError:
                        print name, " Netlights entries not found"
                        color = None
                    except NoOptionError:
                        print "DMX Channel for netlight ", name, row, col, " not found in config"
                        color = None

                    return color

                # Remove the first Color.OFF
                self.dmxmap.append([read_color_config(name, row, col) for name, color in Color.__members__.items()[1:-1]]) 

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("ws://ec2-18-220-127-31.us-east-2.compute.amazonaws.com:8000",
                              on_message = self.on_message,
                              on_error = self.on_error,
                              on_close = self.on_close)

        self.ws.on_open = self.on_open

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        print("### opened ###")

    def on_message(self, ws, message):
        """ Receives web socket update and updates the pixel manager """
        print "Message in a bottle"
        update = json.loads(message)
        print update
        
        if update['type'] == 'pixel_update':
            self.set_frame(update['pixels'])
            

        if update['type'] == 'pixel_touch':
            row = int(update['row'])
            col = int(update['col'])
            color = Color(int(update['color']))
            self.set_color(row, col, color)
        
        self.render_update()

    def clear(self):
        """ Sets an individual pixel to a given color """
        self.pixels = [[Color.OFF for x in range(NET_LIGHT_WIDTH)] for y in range(NET_LIGHT_HEIGHT)]

    def set_color(self, row, column, color):
        """ Sets an individual pixel to a given color """
        if not isinstance(color, Color):
            color = Color(color)

        # Make sure we need to update the pixel
        if row < 0 or row >= NET_LIGHT_HEIGHT: # Out of range 
            # print "Out of range!"
            return
        if column < 0 or column >= NET_LIGHT_WIDTH: # Out of range 
            # print "Out of range!"
            return
        if self.pixels[row][column] == color: # Not changing
            # print "Pixel didn't change"
            return

        print "Pixel set: ", row, column, color
        self.pixels[row][column] = color
        

    def render_update(self):
        if self.dmx is not None:
            print "Sending DMX"
            self.dmx.sendDMX(self.convert_to_dmx_array())

    def set_frame(self, new_pixels):
        """ Sets an individual pixel to a given color """
        for row in range(NET_LIGHT_HEIGHT):
            for col in range(NET_LIGHT_WIDTH):
                 self.set_color(row, col, new_pixels[row][col])

    def get_pixels(self):
        """ Sets an individual pixel to a given color """
        return self.pixels

    def convert_to_dmx_array(self):
        """ Converts the matrix to a single 1D array. """
        output = [255] * 512
        flattened = (self.pixels[4] + self.pixels[3] + self.pixels[2] + self.pixels[1] + self.pixels[0])
        index = 0
        for pixel in flattened:
            # print index, pixel, self.dmxmap[index]
            if pixel == Color.RED:
                output[self.dmxmap[index][0]-1] = 255
                output[self.dmxmap[index][1]-1] = 0
            elif pixel == Color.GREEN:
                output[self.dmxmap[index][0]-1] = 0
                output[self.dmxmap[index][1]-1] = 255
            elif pixel == Color.BOTH:
                output[self.dmxmap[index][1]-1] = 255
                output[self.dmxmap[index][0]-1] = 255
            else:
                output[self.dmxmap[index][0]-1] = 0
                output[self.dmxmap[index][1]-1] = 0
 
            index += 1
             
        return output

    def link_dmx(self, dmx):
        """ Links the DMX instance to the Pixel Manager  """
        self.dmx = dmx

    def start_websocket(self):
        """ Starts the web socket """
        print 'Starting web socket...'
        self.ws.run_forever()
