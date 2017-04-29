import os
import signal
import sys

from lib.capture import Capture


def main():
    print "Starting FoYoDo program..."

    # Set current directory to directory containing main.py. Can get this directory elsewhere with `os.getcwd()`
    os.chdir(os.path.realpath(__file__+"/.."))

    capture = Capture()

    try:
        capture.start()
        signal.pause()  # sleep until KeyboardInterrupt or SystemExit signal is received

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."
        capture.stop()
        capture.join()
        sys.exit()

main()
