import json
import signal
import sys

from lib.scale import Scale
from twilio.rest import Client


def main():
    print "Starting FoYoDo program..."

    with open("config.json", 'r') as config_file:
        config = json.load(config_file)

    try:
        twilio_client = Client(config["twilio"]["account"], config["twilio"]["token"])

        scale = Scale()
        scale.start()

        # call scale.lock_previous_weight when motion is detected to stop updating the stable weight value
        # call scale.is_weight_reduced when motion is no longer detected to see if the stable weight has decreased
        # call scale.lock_previous_weight when motion is no longer detected to start updating the stable weight value
        #       again
        #
        """
        # The following can be used to send SMS to the user. "#TODO" should be replaced with the link to the new video:

        message_body = "Your package may have been disturbed. See the video here: https://youtube.com/#TODO"
        twilio_client.messages.create(from_=config["twilio"]["phone"], to=config["users"][0]["phone"],
                                  body=unicode(message_body))
        """

        signal.pause()

    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."
        scale.stop()
        sys.exit()

main()
