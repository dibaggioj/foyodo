import signal
import sys

from lib.scale import Scale

def main():
    print "Starting FoYoDo program..."

    try:
        scale = Scale()
        scale.start()
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        print "\nStopping FoYoDo program...\n"
        scale.stop()
        sys.exit()

main()
