import picamera.PiCamera as PiCamera
import picamera.PiCameraRuntimeError as PiCameraRuntimeError


class FydCamera(PiCamera):
    def is_camera_recording(self):
        if self.camera is None:
            return True  # don't try to take a picture if the camera is null
        try:
            self._check_recording_stopped()
            return False
        except PiCameraRuntimeError as e:
            print("Camera is currently recording: %s" % str(e))
            return True