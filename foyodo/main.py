import os
import RPi.GPIO as GPIO
import signal
import sys
import time

from lib.capture import Capture


def main():
    PIN_INPUT_SWITCH = 11

    # Set current directory to directory containing main.py. Can get this directory elsewhere with `os.getcwd()`
    os.chdir(os.path.realpath(__file__+"/.."))

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_INPUT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Switch set as input w/ pull-up

    running = False
    capture = None

    print("Flip switch to start FoYoDo.")

    try:
        while not running:
            if GPIO.input(PIN_INPUT_SWITCH) == GPIO.HIGH:
                print "Starting FoYoDo program..."

                running = True

                # TODO: uncomment
                # capture = Capture()
                # capture.start()
                signal.pause()  # sleep until KeyboardInterrupt or SystemExit signal is received

            time.sleep(1)

        while running:
            print("Flip switch to stop FoYoDo.")
            if GPIO.input(PIN_INPUT_SWITCH) == GPIO.LOW:
                raise SystemExit("Flipped switch to stop FoYoDo.")

            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."

        if capture is not None:
            capture.stop()
            capture.join()

        sys.exit()


main()
