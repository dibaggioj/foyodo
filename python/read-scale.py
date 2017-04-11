import math
import os
import usb.core
import usb.util
import sys
import time

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

VENDOR_ID = 0x0922  # DYMO
PRODUCT_ID = 0x8003 # M10

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

def connect_scale_and_listen():
    # find the USB device

    if device is None:
        sys.exit("Could not find scale")

    if device.is_kernel_driver_active(0):
        try:
            device.detach_kernel_driver(0)
            print "kernel driver detached"
        except usb.core.USBError as e:
            sys.exit("Could not detach kernel driver: %s" % str(e))
    else:
        print "no kernel driver attached"

    try:
        # use the first/default configuration
        device.set_configuration()
        device.reset()

        try:
            usb.util.claim_interface(device, 0)
            print "claimed device"
        except:
            sys.exit("Could not claim the device: %s" % str(e))

        # first endpoint
        endpoint = device[0][(0,0)][0]

        listen_for_weight()

    except usb.core.USBError as e:
        sys.exit("Could not set configuration: %s" % str(e))


def grab_weight():
    data = None

    if device is None:
        return data

    try:
        # first endpoint
        endpoint = device[0][(0,0)][0]

        # read a data packet
        attempts = 10
        
        while data is None and attempts > 0:
            try:
                data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
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


def listen_for_weight():
    STATUS_STABLE = 2
    STATUS_INCREASING = 4
    STATUS_DECREASING = 5
    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11

    last_raw_weight = 0
    last_raw_weight_stable = 4

    print "listening for weight..."

    while True:
        time.sleep(.5)

        weight = 0
        print_weight = ""

        data = grab_weight()
        if data != None:
            raw_weight = data[4] + data[5] * 256

            print data
            if data[1] == STATUS_STABLE:
                print "STABLE"
            elif data[1] == STATUS_INCREASING:
                print "INCREASING"
            elif data[1] == STATUS_DECREASING:
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
                if data[2] == DATA_MODE_OUNCES:
                    ounces = raw_weight * 0.1
                    weight = math.ceil(ounces)
                    print_weight = "%s oz" % ounces
                elif data[2] == DATA_MODE_GRAMS:
                    grams = raw_weight
                    weight = math.ceil(grams)
                    print_weight = "%s g" % grams

                print "stable weight: " + print_weight


def main():
    connect_scale_and_listen()


main()



