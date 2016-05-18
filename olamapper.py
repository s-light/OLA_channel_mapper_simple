#!/usr/bin/env python
# coding=utf-8

"""
ola channel mapper.

    read a configuration file and map channels from one universe to a second.
    simplified version to test/compare speed

    history:
        see git commits

    todo:
        ~ all fine :-)
"""


import sys
import time
import os
import array
import json
import socket

from ola.ClientWrapper import ClientWrapper
from ola.OlaClient import OLADNotRunningException

import configdict


version = """18.05.2016 11:30 stefan"""


##########################################
# globals


##########################################
# functions


##########################################
# classes


class OLAMapper():
    """Mapper functions."""

    config_defaults = {
        "map": {
            "channels": [
               1, 2, 3, 4, 5, 6, 7, 8, 9, 10
            ],
        },
        "universe": {
            "channel_count": 240,
            "input": 1,
            "output": 2
        }
    }

    def __init__(self, config):
        """init mapper things."""
        # extend config with defaults
        self.config = config
        configdict.extend_deep(self.config, self.config_defaults.copy())
        # print("config: {}".format(self.config))

        self.channel_count = self.config['universe']['channel_count']
        self.channels_out = array.array('B')

        # internal map
        self.map = self.config['map']['channels']
        # self.map_create()
        # print("full map: {}".format(map_tostring_pretty()))

        # self.channels = []
        for channel_index in range(0, self.channel_count):
            self.channels_out.append(0)

        # timing things
        self.duration = 0
        self.calls = 0

    def print_measurements(self):
        """print duration statistics on exit."""
        # print duration meassurements:
        if self.calls > 0:
            print(
                (
                    "map_channels:\n" +
                    "  sum duration:  {:>10f}s\n" +
                    "  sum calls:     {:>10}\n" +
                    "  duration/call: {:>10.2f}ms/call\n"
                ).format(
                    self.duration,
                    self.calls,
                    ((self.duration / self.calls)*1000)
                )
            )

    def dmx_receive_frame(self, data):
        """receive one dmx frame."""
        # print(data)
        # meassure duration:
        start = time.time()
        self.map_channels(data)
        stop = time.time()
        duration = stop - start
        self.duration += duration
        self.calls += 1
        # temp_array = array.array('B')
        # for channel_index in range(0, self.channel_count):
        #     temp_array.append(self.channels[channel_index])

    def map_channels(self, data_input):
        """remap channels according to map tabel."""
        # print("map channels:")
        # print("data_input: {}".format(data_input))
        data_input_length = data_input.buffer_info()[1]
        # print("data_input_length: {}".format(data_input_length))
        # print("map: {}".format(self.config['map']))

        for channel_output_index, map_value in enumerate(self.map):

            # check if map_value is in range of input channels
            if (
                # (map_value < data_input_length) and
                (map_value < data_input_length)
            ):
                try:
                    self.channels_out[channel_output_index] = (
                        data_input[map_value]
                    )
                except Exception as e:
                    print(
                        (
                            "additional info:\n" +
                            "  channel_output_index: {}\n" +
                            "  len(self.channels_out): {}\n" +
                            "  map_value: {}\n"
                        ).format(
                            channel_output_index,
                            len(self.channels_out),
                            map_value
                        )
                    )
                    raise
            else:
                # don't alter data
                pass

        self.dmx_send_frame(
            self.config['universe']['output'],
            self.channels_out
        )

    # internals / olad things
    # dmx frame sending
    def dmx_send_frame(self, universe, data):
        """Send data as one dmx frame."""
        try:
            self.wrapper.Client().SendDmx(
                universe,
                data,
                # temp_array,
                self.dmx_send_callback
            )
            # print("done.")
        except OLADNotRunningException:
            self.wrapper.Stop()
            print("olad not running anymore.")

    def dmx_send_callback(self, state):
        """React on ola state."""
        if not state.Succeeded():
            self.wrapper.Stop()
            print("warning: dmxSent does not Succeeded.")
        else:
            # print("send frame succeeded.")
            pass

    def ola_setup(self):
        """Setup ola."""
        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()

        # register receive callback and switch to running mode.
        self.client.RegisterUniverse(
            self.config['universe']['input'],
            self.client.REGISTER,
            self.dmx_receive_frame
        )

    def ola_wrapper_run(self):
        """run ola wrapper."""
        print("run ola wrapper.")
        try:
            self.wrapper.Run()
        except KeyboardInterrupt:
            self.wrapper.Stop()
            print("\nstopped")
        except socket.error as error:
            print("connection to OLAD lost:")
            print("   error: " + error.__str__())
            self.flag_connected = False
            # except Exception as error:
            #     print(error)

##########################################
if __name__ == '__main__':

    print(42*'*')
    print('Python Version: ' + sys.version)
    print(42*'*')
    print(__doc__)
    print(42*'*')

    # parse arguments
    filename = "map.json"
    # only use args after script name
    arg = sys.argv[1:]
    if not arg:
        print("using standard values.")
        print(" Allowed parameters:")
        print("   filename for config file       (default='map.json')")
        print("")
    else:
        filename = arg[0]
        # if len(arg) > 1:
        #     pixel_count = int(arg[1])
    # print parsed argument values
    print('''values:
        filename :{}
    '''.format(filename))

    my_config = configdict.ConfigDict(filename=filename)
    print("my_config.config: {}".format(my_config.config))

    my_mapper = OLAMapper(my_config.config)

    my_mapper.ola_setup()
    # this call blocks:
    my_mapper.ola_wrapper_run()

    my_mapper.print_measurements()

    # ###########################################
