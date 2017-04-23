import RPi.GPIO as GPIO
import subprocess
import time
import datetime
import sys
import picamera

GPIO.setmode(GPIO.BCM)

TRIG = 20
ECHO = 26
programflag = True
recordflag = False
idleflag = True
camera = picamera.PiCamera()

print "Distance Measurement In Progress"

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

GPIO.output(TRIG, False)
print "Waiting For Sensor To Settle"
time.sleep(2)
while programflag==True:
	while idleflag==True:
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
		print "Distance:",distance,"cm"

		if distance<=10:
			 idleflag = False
		 	 recordflag = True
	print "movement detected"

	while recordflag==True:
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
			print "Recording, distance away: ",distance ,"cm"

			if distance >= 30:
				break

		print "stop recording"
		camera.stop_recording()
		recordflag=False



	time.sleep(5)
	rc = subprocess.call( ["youtube-upload", "--title="+vid_name, "--description='possible theft'", "--playlist='FoYoDo'", 
		"--client-secret=client_secret.json", "/home/pi/Development/Python/video/"+vid_name+".h264"])
	
	idleflag=True


GPIO.cleanup()

