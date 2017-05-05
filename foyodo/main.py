import os
import RPi.GPIO as GPIO
import signal
import sys
import time

from lib.capture import Capture


def main():
    """
    Waits for switch to be turned on and then starts Capture thread and turns on LED.
    Then waits for switch to be turned off and then stops Capture thread and turns off LED.
    """

    PIN_INPUT_SWITCH = 11
    PIN_OUTPUT_LED_ON = 23

    # Set current directory to directory containing main.py. Can get this directory elsewhere with `os.getcwd()`
    os.chdir(os.path.realpath(__file__+"/.."))

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_INPUT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Switch set as input w/ pull-up
    GPIO.setup(PIN_OUTPUT_LED_ON, GPIO.OUT)

    running = False
    capture = None

    print("Flip switch to start FoYoDo.")

    try:
        while not running:
            if GPIO.input(PIN_INPUT_SWITCH) == GPIO.HIGH:
                print "Starting FoYoDo program..."

                GPIO.output(PIN_OUTPUT_LED_ON, GPIO.HIGH)

                running = True

                capture = Capture()
                capture.start()

                # Uncomment this if not using a switch and you need to stop with keyboard interrupt
                # signal.pause()  # sleep until KeyboardInterrupt or SystemExit signal is received

            time.sleep(1)

        print("Flip switch to stop FoYoDo.")

        while running:
            if GPIO.input(PIN_INPUT_SWITCH) == GPIO.LOW:
                print("Flipped switch to stop FoYoDo.")
                raise SystemExit("Flipped switch to stop FoYoDo.")

            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."

        if capture is not None:
            capture.stop()
            capture.join()

        GPIO.output(PIN_OUTPUT_LED_ON, GPIO.LOW)
        sys.exit()


main()
