import sys

from lib.capture import Capture


def main():
    print "Starting FoYoDo program..."

    capture = Capture()

    try:
        capture.start()

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."
        capture.stop()
        sys.exit()

main()
