import json
import signal
import sys
import subprocess
import time
import datetime
import picamera

import RPi.GPIO as GPIO

from lib.scale import Scale
from twilio.rest import Client


GPIO.setmode(GPIO.BCM)

TRIG = 20
ECHO = 26


def main():
    print "Starting FoYoDo program..."

    with open("./config.json", 'r') as config_file:
        config = json.load(config_file)

    try:
        twilio_client = Client(config["twilio"]["account"], config["twilio"]["token"])

        scale = Scale()
        scale.start()

        # signal.pause()

        camera = picamera.PiCamera()
        programflag = True
        recordflag = False
        idleflag = True

        print "Distance Measurement In Progress"

        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)

        GPIO.output(TRIG, False)
        print "Waiting For Sensor To Settle"
        time.sleep(2)
        while programflag is True:
            while idleflag is True:
                GPIO.output(TRIG, True)
                time.sleep(0.00001)
                GPIO.output(TRIG, False)

                while GPIO.input(ECHO) == 0:
                    pulse_start = time.time()

                while GPIO.input(ECHO) == 1:
                    pulse_end = time.time()

                pulse_duration = pulse_end - pulse_start
                distance = pulse_duration * 17150
                distance = round(distance, 2)
                # print "Distance:",distance,"cm"

                if distance <= 10:
                    idleflag = False
                    recordflag = True
            print "movement detected"

            while recordflag is True:
                scale.lock_previous_weight()
                print "Locking weight at: " + scale.weight_lock
                print "Start Recording"
                ts = time.time()
                vid_name = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                camera.capture('picture/'+vid_name+'.jpg')
                camera.start_recording('video/'+vid_name+'.h264')
                time.sleep(10)
                while True:
                    GPIO.output(TRIG, True)
                    time.sleep(0.00001)
                    GPIO.output(TRIG, False)

                    while GPIO.input(ECHO)==0:
                        pulse_start = time.time()

                    while GPIO.input(ECHO)==1:
                        pulse_end = time.time()

                    pulse_duration = pulse_end - pulse_start
                    distance = pulse_duration * 17150
                    distance = round(distance, 2)
                    # print "Recording, distance away: ",distance ,"cm"

                    if distance >= 30:
                        break

                print "stop recording"
                camera.stop_recording()
                recordflag = False

            time.sleep(5)   # wait for video to finish encoding

            print "Current weight is: " + scale.weight_current
            print "Done recording video. Is weight reduced: " + scale.is_weight_reduced()

            if scale.is_weight_reduced():
                rc = subprocess.call( ["youtube-upload", "--title="+vid_name, "--description='possible theft'",
                                       "--playlist='FoYoDo'", "--client-secret=client_secret.json",
                                       "/home/pi/Development/Python/video/"+vid_name+".h264"])

            print "Current weight is: " + scale.weight_current
            print "Releasing weight"
            scale.release_previous_weight()

            idleflag = True


        GPIO.cleanup()

        # call scale.lock_previous_weight when motion is detected to stop updating the stable weight value
        # call scale.is_weight_reduced when motion is no longer detected to see if the stable weight has decreased
        # call scale.release_previous_weight when motion is no longer detected to start updating the stable weight value
        #       again
        #
        """
        # The following can be used to send SMS to the user. "#TODO" should be replaced with the link to the new video:

        message_body = "Hi {0}, your package may have been disturbed. See the video here: " \
                       "https://www.youtube.com/embed/videoseries?list={1}".format(config["users"][0]["first_name"],
                                                                                   config["youtube"]["playlist"])
        twilio_client.messages.create(from_=config["twilio"]["phone"], to=config["users"][0]["phone"],
                                      body=unicode(message_body))
        """



    except (KeyboardInterrupt, SystemExit):
        print "Stopping FoYoDo program..."
        scale.stop()
        sys.exit()

main()
