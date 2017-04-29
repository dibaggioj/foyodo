import datetime
import json
import os
import picamera
import RPi.GPIO as GPIO
import subprocess
import threading
import time

from scale import Scale
from twilio.rest import Client


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

    recordflag = False
    idleflag = True
    camera = picamera.PiCamera()
    scale = Scale()


    def __init__(self):
        super(Capture, self).__init__()
        self._stop = threading.Event()

        with open(os.getcwd() + "/config.json", 'r') as config_file:
            self.CONFIG = json.load(config_file)
        with open(os.getcwd() + "/youtube.json", 'r') as youtube_file:
            self.YOUTUBE = json.load(youtube_file)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        self.twilio_client = Client(self.CONFIG["twilio"]["account"], self.CONFIG["twilio"]["token"])

    def stop(self):
        self.camera.close()

        self.scale.stop()
        self.scale.join()

        print("Stopping capture thread...")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def send_message(self):
        message_body = "Hi {0}, your package may have been disturbed. See the video here: " \
                       "https://www.youtube.com/embed/videoseries?list={1}".format(
                           self.CONFIG["users"][0]["first_name"],
                           self.YOUTUBE["installed"]["playlist_id"])

        self.twilio_client.messages.create(from_=self.CONFIG["twilio"]["phone"],
                                           to=self.CONFIG["users"][0]["phone"],
                                           body=unicode(message_body))

    def run(self):
        print "## Running capture thread..."
        print "## Starting scale..."
        self.scale.start()
        GPIO.output(self.TRIG, False)
        print "Waiting For UltraSonic Sensor To Settle"
        time.sleep(2)
        while not self.stopped():
            while self.idleflag is True:
                try:
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
                except:
                    print "Exception occurred while recording distance"
            print "movement detected"
            self.scale.lock_previous_weight()
            print("Locking weight at: %s" % self.scale.weight_lock)

            while self.recordflag is True:
                print "Start Recording"
                ts = time.time()
                vid_name = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                self.camera.capture(os.getcwd() + '/picture/'+vid_name+'.jpg')
                self.camera.start_recording(os.getcwd() + '/video/'+vid_name+'.h264')
                time.sleep(10)
                while True:
                    try:
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
                    except:
                        print "Exception occurred while recording distance"

                print "stop recording"
                self.camera.stop_recording()
                self.recordflag = False

            time.sleep(5)
            print("Current weight is: %s" % self.scale.weight_current)
            print("Done recording video. Is weight reduced: %s" % self.scale.is_weight_reduced())

            if self.scale.is_weight_reduced():
                rc = subprocess.call(["youtube-upload",
                                      "--title="+vid_name,
                                      "--description='possible theft'",
                                      "--playlist='"+self.YOUTUBE["installed"]["playlist_name"]+"'",
                                      "--client-secret="+os.getcwd()+"/youtube.json",
                                      os.getcwd() + "/video/"+vid_name+".h264"])

                self.send_message()

            print("Current weight is: %s" % self.scale.weight_current)
            print "Releasing weight"
            self.scale.release_previous_weight()

            self.idleflag = True

        GPIO.cleanup()
