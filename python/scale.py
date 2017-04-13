import math
import os
import usb.core
import usb.util
import sys
import time
import threading


"""
Includes code modified from:
https://github.com/walac/pyusb/issues/76
https://gist.github.com/jacksenechal/5862530
https://github.com/yanigisawa/coffee-scale/blob/master/usbscale.py

Dymo M10 data packet (see http://steventsnyder.com/reading-a-dymo-usb-scale-using-python):
Element 1 always seems to have value 3
Element 2 indicates whether the value is stable, as follows:
    2: zero or stable weight
    4: increasing weight (not stable)
    5: decreasing weight (not stable)
Element 3 indicates units, as follows:
    2: grams
    11: ounces
Element 4 for calculating the scaling factor when reading in ounces. 255 is the signed value -1, which indicates that the raw value is in tenths, due
to a scaling factor of 10^-1 or 0.1. For a value of 254, the scaling factor is 10^-2, or 0.01.
Elements 5 and 6 are used to calculate the weight.

"""

class Scale(threading.Thread):

    VENDOR_ID = 0x0922  # DYMO
    PRODUCT_ID = 0x8003 # M10

    STATUS_STABLE = 2
    STATUS_INCREASING = 4
    STATUS_DECREASING = 5

    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11

    TOLERANCE_GRAMS = 5
    TOLERANCE_OUNCES = 0.167

    __stop = True
    weight_locked = False
    previous_weight = 0
    current_weight = 0
    data_mode = DATA_MODE_GRAMS
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)


    def __init__(self):
        print "## Init scale"
        threading.Thread.__init__(self)

        try:
            self.connect_scale()
            self.start()

        except Exception as e:
            print("Exception connecting scale and listening for weight: %s" % str(e))


    def run(self):
        print "## Running scale thread"
        self.__stop = False
        self.listen_for_weight()

    def stop(self):
        print("## Stopping scale thread")
        self.__stop = True

    def is_weight_reduced(self):
        delta_weight = self.current_weight - self.previous_weight
        tolerance = self.TOLERANCE_GRAMS if self.data_mode == self.DATA_MODE_GRAMS else self.TOLERANCE_OUNCES
        return delta_weight > 2 * tolerance


    def get_previous_weight(self):
        """
        Returns previous stable weight
        :return: integer
        """
    #     TODO


    def get_current_weight(self):
        """
        Returns current stable weight
        :return: integer
        """
    #     TODO


    def lock_previous_weight(self):
        self.weight_locked = True
    #     TODO


    def release_previous_weight(self):
        self.weight_locked = False
    #     TODO


    def connect_scale(self):
        # find the USB device

        if self.device is None:
            raise Exception("Could not find scale")

        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
                print "Kernel driver detached"
            except usb.core.USBError as e:
                raise Exception("Could not detach kernel driver: %s" % str(e))
        else:
            print "no kernel driver attached"

        try:
            # use the first/default configuration
            self.device.set_configuration()
            self.device.reset()

            try:
                usb.util.claim_interface(self.device, 0)
                print "Claimed device"
            except:
                raise Exception("Could not claim the device")

            # first endpoint
            endpoint = self.device[0][(0,0)][0]

        except usb.core.USBError as e:
            raise Exception("Could not set configuration: %s" % str(e))


    def grab_weight(self):
        data = None

        if self.device is None:
            return data

        try:
            # first endpoint
            endpoint = self.device[0][(0,0)][0]

            # read a data packet
            attempts = 10

            while data is None and attempts > 0:
                try:
                    data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                except usb.core.USBError as e:
                    data = None
                    if e.args == ('Operation timed out',):
                        attempts -= 1
                        print "timed out... trying again"
                        continue

            return data

        except usb.core.USBError as e:
            print "USBError: " + str(e.args)
        except IndexError as e:
            print "IndexError: " + str(e.args)


    def listen_for_weight(self):
        # TODO: rework

        last_raw_weight = 0
        last_raw_weight_stable = 4

        print "listening for weight..."

        while not self.__stop:
            time.sleep(.5)

            weight = 0
            print_weight = ""

            data = self.grab_weight()

            if data is not None:
                self.data_mode = data[2]

                raw_weight = data[4] + data[5] * 256

                print data
                if data[1] == self.STATUS_STABLE:
                    print "STABLE"
                elif data[1] == self.STATUS_INCREASING:
                    print "INCREASING"
                elif data[1] == self.STATUS_DECREASING:
                    print "DECREASING"
                else:
                    print "UNKNOWN"

                # +/- 2g
                if raw_weight != 0 and abs(raw_weight - last_raw_weight) > 0 and raw_weight != last_raw_weight:
                    last_raw_weight_stable = 4
                    last_raw_weight = raw_weight

                if raw_weight != 0 and last_raw_weight_stable >= 0:
                    last_raw_weight_stable -= 1

                if raw_weight != 0 and last_raw_weight_stable == 0:
                    if data[2] == self.DATA_MODE_OUNCES:
                        ounces = raw_weight * 0.1
                        weight = math.ceil(ounces)
                        print_weight = "%s oz" % ounces
                    elif data[2] == self.DATA_MODE_GRAMS:
                        grams = raw_weight
                        weight = math.ceil(grams)
                        print_weight = "%s g" % grams

                    print "stable weight: " + print_weight
