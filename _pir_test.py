import RPi.GPIO as GPIO
import time


PIN_INPUT_PIR = 18

TIME_SEC_PIR_CALIBRATION = 15   # Time given to PIR sensor to calibrate (10-60 secs according to the data sheet)
TIME_MS_PAUSE = 5000

low_in = 0
lock_low = True
take_low_time = False


def __init_pir_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_INPUT_PIR, GPIO.IN)

    GPIO.output(PIN_INPUT_PIR, GPIO.HIGH)
    # give the sensor some time to calibrate
    for i in range(0, TIME_SEC_PIR_CALIBRATION):
        time.sleep(1)
        print("Calibrating PIR sensor...")

    print("Done calibrating PIR sensor")
    time.sleep(0.05)


def __run():
    global low_in
    global lock_low
    global take_low_time

    print("Running...")
    print("low_in: %s" % low_in)
    print("lock_low: %s" % lock_low)
    print("take_low_time: %s" % take_low_time)

    while True:
        if GPIO.input(PIN_INPUT_PIR) == GPIO.HIGH:
            print("HIGH")

            if lock_low:
                print("Lock is low")
                lock_low = False
                print("---")
                print("Motion detected at %s millisec" % time.time())
                # time.sleep(0.05);

            take_low_time = True

        if GPIO.input(PIN_INPUT_PIR) == GPIO.LOW:
            print("LOW")
            if take_low_time:
                low_in = time.time()    ## save the time of the transition from high to LOW
                take_low_time = False   ## make sure this is only done at the start of a LOW phase

            # if the sensor is low for more than the given pause,
            # we assume that no more motion is going to happen
            if not lock_low and (time.time() - low_in) > TIME_MS_PAUSE:
                # makes sure this block of code is only executed again after
                # a new motion sequence has been detected
                lock_low = True
                print("Motion ended at %s millisec" % (time.time() - TIME_MS_PAUSE))
                # time.sleep(0.05);


__init_pir_sensor()

__run()