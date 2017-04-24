import signal
import sys

from lib.capture import Capture


def main():
    print "Starting FoYoDo program..."

    capture = Capture()

    try:
        capture.start()
        signal.pause()  # sleep until KeyboardInterrupt or SystemExit signal is received

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."
        capture.stop()
        sys.exit()

main()
