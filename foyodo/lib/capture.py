import datetime
import json
import picamera
import RPi.GPIO as GPIO
import subprocess
import threading
import time

from scale import Scale
from twilio.rest import Client

"""
# The following can be used to send SMS to the user. "#TODO" should be replaced with the link to the new video:

message_body = "Hi {0}, your package may have been disturbed. See the video here: " \
               "https://www.youtube.com/embed/videoseries?list={1}".format(CONFIG["users"][0]["first_name"],
                                                                           CONFIG["youtube"]["playlist_id"])
twilio_client.messages.create(from_=CONFIG["twilio"]["phone"], to=CONFIG["users"][0]["phone"],
                              body=unicode(message_body))
"""


class Capture(threading.Thread):
    """
    Capture thread

    Instantiate with:
    capture = Capture()

    Start with:
    capture.start()

    Stop with (to free up resources):
    capture.stop()

    Instantiates a scale thread instance.
    Uses ultrasonic motion sensing.
    Takes a picture and records video when motion is detected. Stops recording video after motion is no longer detected.
    Uploads the video to YouTube if the weight has been reduced on the scale since it was locked in after motion was
    sensed. Releases the locked weight after motion is no longer sensed.
    """
    TRIG = 20
    ECHO = 26

    with open("./config.json", 'r') as config_file:
        CONFIG = json.load(config_file)

    programflag = True
    recordflag = False
    idleflag = True
    camera = picamera.PiCamera()
    scale = Scale()

    twilio_client = Client(CONFIG["twilio"]["account"], CONFIG["twilio"]["token"])

    def __init__(self):
        super(Capture, self).__init__()
        self._stop = threading.Event()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

    def stop(self):
        print("Stopping capture thread...")
        self._stop.set()
        self.scale.stop()
        self.programflag = False

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        print("## starting scale...")
        self.scale.start()
        print("## Running capture thread...")
        GPIO.output(self.TRIG, False)
        print "Waiting For Sensor To Settle"
        time.sleep(2)
        while self.programflag is True:
            while self.idleflag is True:
                GPIO.output(self.TRIG, True)
                time.sleep(0.00001)
                GPIO.output(self.TRIG, False)

                while GPIO.input(self.ECHO) == 0:
                    pulse_start = time.time()

                while GPIO.input(self.ECHO) == 1:
                    pulse_end = time.time()

                pulse_duration = pulse_end - pulse_start
                distance = pulse_duration * 17150
                distance = round(distance, 2)
                print "Distance:", distance, "cm"

                if distance <= 10:
                    self.idleflag = False
                    self.recordflag = True
            print "movement detected"

            while self.recordflag is True:
                self.scale.lock_previous_weight()
                print "Locking weight at: " + self.scale.weight_lock
                print "Start Recording"
                ts = time.time()
                vid_name = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                self.camera.capture('picture/'+vid_name+'.jpg')
                self.camera.start_recording('video/'+vid_name+'.h264')
                time.sleep(10)
                while True:
                    GPIO.output(self.TRIG, True)
                    time.sleep(0.00001)
                    GPIO.output(self.TRIG, False)

                    while GPIO.input(self.ECHO) == 0:
                        pulse_start = time.time()

                    while GPIO.input(self.ECHO) == 1:
                        pulse_end = time.time()

                    pulse_duration = pulse_end - pulse_start
                    distance = pulse_duration * 17150
                    distance = round(distance, 2)
                    print "Recording, distance away: ", distance, "cm"

                    if distance >= 30:
                        break

                print "stop recording"
                self.camera.stop_recording()
                self.recordflag = False

            time.sleep(5)
            print "Current weight is: " + self.scale.weight_current
            print "Done recording video. Is weight reduced: " + self.scale.is_weight_reduced()

            if self.scale.is_weight_reduced():
                global CONFIG
                rc = subprocess.call(["youtube-upload", "--title="+vid_name, "--description='possible theft'",
                                      "--playlist='"+CONFIG["youtube"]["playlist_name"]+"'",
                                      "--client-secret=client_secret.json",
                                      "/home/pi/Development/Python/video/"+vid_name+".h264"])

            print "Current weight is: " + self.scale.weight_current
            print "Releasing weight"
            self.scale.release_previous_weight()

            self.idleflag = True

        GPIO.cleanup()
