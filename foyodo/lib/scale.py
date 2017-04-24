import threading
import time
import usb.core
import usb.util

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

    weight_is_locked = False
    weight_lock = 0
    weight_current = 0
    data_mode = DATA_MODE_GRAMS
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    def __init__(self):
        super(Scale, self).__init__()
        self._stop = threading.Event()

    def start(self):
        super(Scale, self).start()
        try:
            self.connect_scale()
        except Exception as e:
            print("Exception connecting scale and listening for weight: %s" % str(e))

    def stop(self):
        print("Stopping scale thread...")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self.listen_for_weight()

    def is_weight_reduced(self):
        delta_weight = self.weight_current - self.weight_lock
        tolerance = self.TOLERANCE_GRAMS if self.data_mode == self.DATA_MODE_GRAMS else self.TOLERANCE_OUNCES
        return delta_weight > 2 * tolerance

    def lock_previous_weight(self):
        self.weight_is_locked = True

    def release_previous_weight(self):
        self.weight_is_locked = False

    def get_raw_tolerance(self):
        return (self.TOLERANCE_GRAMS * self.CONVERSION_RAW_WEIGHT_TO_GRAMS) if self.data_mode == self.DATA_MODE_GRAMS \
            else (self.TOLERANCE_OUNCES * self.CONVERSION_RAW_WEIGHT_TO_OUNCES)

    def connect_scale(self):
        """
        Finds the USB device
        """

        if self.device is None:
            raise Exception("Could not find scale")

        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
                print("Kernel driver detached")
            except usb.core.USBError as e:
                raise Exception("Could not detach kernel driver: %s" % str(e))
        else:
            print("no kernel driver attached")

        try:
            # use the first/default configuration
            self.device.set_configuration()
            self.device.reset()

            try:
                usb.util.claim_interface(self.device, 0)
                print("Claimed device")
            except:
                raise Exception("Could not claim the device")

            # first endpoint
            endpoint = self.device[0][(0,0)][0]

        except usb.core.USBError as e:
            raise Exception("Could not set configuration: %s" % str(e))

    def grab_weight(self):
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
            attempts = 10

            while data is None and attempts > 0:
                try:
                    data = self.device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                except usb.core.USBError as e:
                    data = None
                    if e.args == ('Operation timed out',):
                        attempts -= 1
                        print("timed out... trying again")
                        continue

            return data

        except usb.core.USBError as e:
            print("USBError: " + str(e.args))
        except IndexError as e:
            print("IndexError: " + str(e.args))

    def listen_for_weight(self):
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
        count = self.READING_COUNT

        while not self.stopped():
            data = self.grab_weight()

            if data is not None:
                self.data_mode = data[2]
                raw_weight_current = data[4] + data[5] * 256

                if abs(raw_weight_current - raw_weight_previous) < self.get_raw_tolerance():
                    count -= 1
                    if count <= 0:
                        raw_weight_stable = raw_weight_current  # TODO: maybe use previous weight or average over readings
                        count = self.READING_COUNT
                else:
                    raw_weight_previous = raw_weight_current
                    count = self.READING_COUNT

            if self.weight_is_locked:
                print("Locked, stable raw weight: %s" % raw_weight_stable)
                self.weight_current = raw_weight_stable
            else:
                print("Not locked, stable raw weight: %s" % raw_weight_stable)
                self.weight_lock = raw_weight_stable

            time.sleep(self.READING_PERIOD_SECONDS)


        ################################################################################################################
        # # TODO: REMOVE
        #
        # last_raw_weight = 0
        # last_raw_weight_stable = 4
        #
        # while not self.__stop:
        #     time.sleep(.5)
        #
        #     weight = 0
        #     print_weight = ""
        #
        #     data = self.grab_weight()
        #
        #     if data is not None:
        #         self.data_mode = data[2]
        #
        #         raw_weight = data[4] + data[5] * 256
        #
        #         print data
        #         if data[1] == self.STATUS_STABLE:
        #             print("STABLE")
        #         elif data[1] == self.STATUS_INCREASING:
        #             print("INCREASING")
        #         elif data[1] == self.STATUS_DECREASING:
        #             print("DECREASING")
        #         else:
        #             print("UNKNOWN")
        #
        #         # +/- 2g
        #         if raw_weight != 0 and abs(raw_weight - last_raw_weight) > 0 and raw_weight != last_raw_weight:
        #             last_raw_weight_stable = 4
        #             last_raw_weight = raw_weight
        #
        #         if raw_weight != 0 and last_raw_weight_stable >= 0:
        #             last_raw_weight_stable -= 1
        #
        #         if raw_weight != 0 and last_raw_weight_stable == 0:
        #             if data[2] == self.DATA_MODE_OUNCES:
        #                 ounces = raw_weight * 0.1
        #                 weight = math.ceil(ounces)
        #                 print_weight = "%s oz" % ounces
        #             elif data[2] == self.DATA_MODE_GRAMS:
        #                 grams = raw_weight
        #                 weight = math.ceil(grams)
        #                 print_weight = "%s g" % grams
        #
        #             print("stable weight: " + print_weight)
        ################################################################################################################
