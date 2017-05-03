import datetime
import json
import os
import RPi.GPIO as GPIO
import subprocess
import threading
import time

from fyd_camera import FydCamera
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

    PIN_INPUT_PIR = 18

    TIME_SEC_PIR_CALIBRATION = 10   # Time given to PIR sensor to calibrate (10-60 secs according to the data sheet)
    TIME_SEC_PAUSE = 10             # Stop recording video if no motion is sensed for 10 seconds

    recordflag = False
    idleflag = True
    low_in = 0
    lock_low = True
    take_low_time = False
    camera = FydCamera()
    scale = Scale(camera)

    def __init__(self):
        super(Capture, self).__init__()
        self._stop = threading.Event()

        with open(os.getcwd() + "/config.json", 'r') as config_file:
            self.CONFIG = json.load(config_file)

        self.twilio_client = Client(self.CONFIG["twilio"]["account"], self.CONFIG["twilio"]["token"])

        self.__init_pir_sensor()


    def stop(self):
        self.camera.close()

        self.scale.stop()
        self.scale.join()

        print("Stopping capture thread...")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def __init_pir_sensor(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_INPUT_PIR, GPIO.IN)
        # give the sensor some time to calibrate
        for i in range(0, self.TIME_SEC_PIR_CALIBRATION):
            time.sleep(1)
            print("Calibrating PIR sensor...")

        print("Done calibrating PIR sensor")
        time.sleep(0.05)


    def send_message(self):
        message_body = "Potential theft, see https://foyodo.bitbucket.io/ for more info"
        # message_body = "Potential theft: https://www.youtube.com/embed/videoseries?list={1}".format(
        #     self.CONFIG["users"][0]["first_name"],
        #     self.CONFIG["youtube"]["playlist_id"])

        self.twilio_client.messages.create(from_=self.CONFIG["twilio"]["phone"],
                                           to=self.CONFIG["users"][0]["phone"],
                                           body=unicode(message_body))

    def run(self):
        print "## Running capture thread..."
        print "## Starting scale..."
        self.scale.start()
        while not self.stopped():
            while self.idleflag is True:
                if GPIO.input(self.PIN_INPUT_PIR) == GPIO.HIGH:
                    if self.lock_low:
                        self.lock_low = False
                        print("Motion detected at %s millisec" % time.time())
                        self.idleflag = False
                        self.recordflag = True

                    self.take_low_time = True

                time.sleep(0.1);

            self.scale.lock_previous_weight()
            print("Locking weight at: %s" % self.scale.weight_lock)

            while self.recordflag is True:
                print "Start Recording"
                ts = time.time()
                vid_name = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
                self.camera.capture(os.getcwd() + '/picture/'+vid_name+'.jpg')
                self.camera.start_recording(os.getcwd() + '/video/'+vid_name+'.h264')

                while True:
                    if GPIO.input(self.PIN_INPUT_PIR) == GPIO.LOW:
                        if self.take_low_time:
                            self.low_in = time.time()   ## save the time of the transition from high to LOW
                            self.take_low_time = False  ## make sure this is only done at the start of a LOW phase

                        # if the sensor is low for more than the given pause,
                        # we assume that no more motion is going to happen
                        if not self.lock_low and (time.time() - self.low_in) > self.TIME_SEC_PAUSE:
                            # makes sure this block of code is only executed again
                            # after a new motion sequence has been detected
                            self.lock_low = True
                            print("Motion ended at %s millisec" % (time.time() - self.TIME_SEC_PAUSE))
                            break

                    time.sleep(0.1);

                print "Stop recording"
                self.camera.stop_recording()
                self.recordflag = False

            time.sleep(5)   # Wait until video finishes encoding
            print("Current weight is: %s" % self.scale.weight_current)
            print("Done recording video. Is weight reduced: %s" % self.scale.is_weight_reduced())

            if self.scale.is_weight_reduced():
                print("Current weight is: %s" % self.scale.weight_current)
                self.scale.release_previous_weight()
                rc = subprocess.call(["youtube-upload",
                                      "--title="+vid_name,
                                      "--description=Possible package theft",
                                      "--playlist="+self.CONFIG["youtube"]["playlist_name"],
                                      "--client-secret="+os.getcwd()+"/youtube_client.json",
                                      os.getcwd() + "/video/"+vid_name+".h264"])

                self.send_message()
            else:
                print("Current weight is: %s" % self.scale.weight_current)
                self.scale.release_previous_weight()

            self.idleflag = True

        GPIO.cleanup()
