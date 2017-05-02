import picamera


class FydCamera(picamera.PiCamera):
    def is_camera_recording(self):
        try:
            self._check_recording_stopped()
            return False
        except picamera.PiCameraRuntimeError as e:
            print("Camera is currently recording: %s" % str(e))
            return True