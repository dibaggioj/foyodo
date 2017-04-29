import numpy
import threading
import time
import usb.core
import usb.util

from twilio.rest import Client

"""
Scale class for use in multi-threaded program

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
Element 4 for calculating the scaling factor when reading in ounces. 255 is the signed value -1, which indicates that
the raw value is in tenths, due to a scaling factor of 10^-1 or 0.1. For a value of 254, the scaling factor is 10^-2, or
0.01.
Elements 5 and 6 are used to calculate the weight. An increase in the value of element 6 is a larger increase (by a
factor of 256) than an increase in element 5
"""


class Scale(threading.Thread):
    """
    Scale thread

    Instantiate with:
    scale = Scale()

    Start with:
    scale.start()

    Stop with (to free up resources):
    scale.stop()
    """

    VENDOR_ID = 0x0922      # DYMO
    PRODUCT_ID = 0x8003     # M10

    READ_ATTEMPTS_MAX = 10
    READING_PERIOD_SECONDS = 0.5
    READING_COUNT = 4

    STATUS_STABLE = 2
    STATUS_INCREASING = 4
    STATUS_DECREASING = 5

    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11

    TOLERANCE_GRAMS = 5
    TOLERANCE_OUNCES = 0.167

    CONVERSION_RAW_WEIGHT_TO_OUNCES = 10
    CONVERSION_RAW_WEIGHT_TO_GRAMS = 1

    MESSAGES_SENT_MAX_DEBUG = 3

    connected = False
    connecting_flag = False
    weight_is_locked = False
    weight_lock = 0
    weight_current = 0
    data_mode = DATA_MODE_GRAMS
    messages_sent = 0


    def __init__(self):
        super(Scale, self).__init__()
        self._stop = threading.Event()

        self.twilio_client = Client(self.CONFIG["twilio"]["account"], self.CONFIG["twilio"]["token"])

    def start(self):
        super(Scale, self).start()
        try:
            self.__connect_scale()
        except Exception as e:
            print("Exception occurred while connecting to scale\n%s" % str(e))

    def stop(self):
        print("Stopping scale thread...")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self.__listen_for_weight()

    def is_weight_reduced(self):
        delta_weight = self.weight_current - self.weight_lock
        tolerance = self.TOLERANCE_GRAMS if self.data_mode == self.DATA_MODE_GRAMS else self.TOLERANCE_OUNCES
        return delta_weight < -2 * tolerance

    def lock_previous_weight(self):
        self.weight_is_locked = True

    def release_previous_weight(self):
        self.weight_is_locked = False

    def __get_raw_tolerance(self):
        return (self.TOLERANCE_GRAMS * self.CONVERSION_RAW_WEIGHT_TO_GRAMS) if self.data_mode == self.DATA_MODE_GRAMS \
            else (self.TOLERANCE_OUNCES * self.CONVERSION_RAW_WEIGHT_TO_OUNCES)

    def __send_message(self):
        message_body = "Lost scale connection!"
        self.twilio_client.messages.create(from_=self.CONFIG["twilio"]["phone"],
                                           to=self.CONFIG["users"][0]["phone"],
                                           body=unicode(message_body))

    def __connect_scale(self):
        """
        Finds the USB device
        """
        print "Connecting scale..."
        self.connecting_flag = True

        self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)

        if self.device is None:
            self.connecting_flag = False
            raise Exception("Could not find scale")

        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
                print("Kernel driver detached")
            except usb.core.USBError as e:
                self.connecting_flag = False
                raise Exception("Could not detach kernel driver: %s" % str(e))
        else:
            print("no kernel driver attached")

        try:
            # use the first/default configuration
            self.device.set_configuration()
            self.device.reset()

            try:
                usb.util.claim_interface(self.device, 0)
                self.connected = True
                print("Claimed device")
            except:
                self.connecting_flag = False
                raise Exception("Could not claim the device")

            # first endpoint
            endpoint = self.device[0][(0,0)][0]

        except usb.core.USBError as e:
            self.connecting_flag = False
            raise Exception("Could not set configuration: %s" % str(e))

        self.connecting_flag = False

    def __reconnect_scale(self):
        print "Reconnect scale"
        if self.connecting_flag:
            print "Scale is already connecting"
        else:
            try:
                self.__connect_scale()
            except Exception as e:
                print("Exception occurred while connecting to scale\n%s" % str(e))

    def __read_weight(self):
        """
        Gets a data packet from the USB scale
        :return: array of integers
        """
        data = None

        if self.device is None:
            return data

        try:
            # first endpoint
            endpoint = self.device[0][(0,0)][0]

            # read a data packet
            attempts = self.READ_ATTEMPTS_MAX

            while data is None and attempts > 0:
                try:
                    data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                except usb.core.USBError as e:
                    data = None
                    attempts -= 1
                    print("USBError occurred while reading from scale for attempt #%s\n%s" % (
                        (self.READ_ATTEMPTS_MAX - attempts), str(e)))

            if data is None:
                print("Setting device to None")
                if self.messages_sent < self.MESSAGES_SENT_MAX_DEBUG:  # Don't send too many messages while testing
                    self.__send_message()
                self.device = None

            return data

        except usb.core.USBError as e:
            print("USBError occurred while reading from scale\n%s" % str(e))
        except IndexError as e:
            print("IndexError occurred while reading from scale\n%s" % str(e))

    def __listen_for_weight(self):
        """
        Reads weight every `READING_PERIOD_SECONDS` seconds.
        If weight fluctuations are within tolerance for `READING_COUNT` readings, then store a new stable weight
        (a raw weight).
        If the weight is locked (from the main thread that instantiated this scale), then store the new stable weight as
        the current weight. Otherwise, store the new stable weight as the locked weight. These `weight_current` and
        `weight_lock` values will be used later when the main thread checks to see if the weight has been reduced
        unexpectedly.
        """

        print("listening for weight...")

        raw_weight_stable = 0
        raw_weight_previous = 0
        weight_readings = []

        while not self.stopped():
            if self.connected:
                data = self.__read_weight()

                if data is not None:
                    self.data_mode = data[2]
                    raw_weight_current = data[4] + data[5] * 256

                    # print("raw_weight_current: %s, raw_weight_previous: %s, raw_tolerance: %s" %
                    #       (raw_weight_current, raw_weight_previous, self.get_raw_tolerance()))

                    if abs(raw_weight_current - raw_weight_previous) < self.__get_raw_tolerance():
                        weight_readings.append(raw_weight_current)
                        if len(weight_readings) >= self.READING_COUNT:
                            print("## Setting stable raw weight to: %s" % raw_weight_stable)
                            raw_weight_stable = numpy.median(weight_readings)
                            weight_readings = []
                    else:
                        raw_weight_previous = raw_weight_current
                        weight_readings = []

                elif self.device is None:
                    self.__reconnect_scale()

            else:
                self.__reconnect_scale()

            if self.weight_is_locked:
                print("Locked, stable raw weight: %s, locked raw weight: %s" %
                      (raw_weight_stable, self.weight_lock))
                self.weight_current = raw_weight_stable
            else:
                print("Not locked, stable raw weight: %s" % raw_weight_stable)
                self.weight_lock = raw_weight_stable

            time.sleep(self.READING_PERIOD_SECONDS)
