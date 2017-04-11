import os
import usb.core
import usb.util
import sys
import time

VENDOR_ID = 0x0922  # DYMO
PRODUCT_ID = 0x8003 # M10

def listen_for_weight():
    print "listening for weight..."

    while True:
        time.sleep(1)

        # read a data packet
        attempts = 10
        data = None
        while data is None and attempts > 0:
            try:
                data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
            except usb.core.USBError as e:
                data = None
                if e.args == ("Operation timed out",):
                    attempts -= 1
                    continue
        print data

# find the USB device
device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

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


