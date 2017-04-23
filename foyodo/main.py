import signal
import sys

from lib.scale import Scale

def main():
    print "Starting FoYoDo program..."

    try:
        scale = Scale()
        scale.start()

        # call scale.lock_previous_weight when motion is detected to stop updating the stable weight value
        # call scale.is_weight_reduced when motion is no longer detected to see if the stable weight has decreased
        # call scale.lock_previous_weight when motion is no longer detected to start updating the stable weight value again

        signal.pause()

    except (KeyboardInterrupt, SystemExit):
        print "\nStopping FoYoDo program...\n"
        scale.stop()
        sys.exit()

main()
