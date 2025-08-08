# camera_api.py

import cv2
import time
from threading import Thread


class CameraAPI:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.streaming = False
        self.thread = None
        self.frame_callback = None

    def open_camera(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            self.cap = None
            raise RuntimeError(f"Failed to open camera {self.camera_id}")
        print(f"Camera {self.camera_id} opened.")

    def close_camera(self):
        self.stop_streaming()
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera closed.")

    def start_streaming(self, frame_callback):
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Camera not opened.")

        if self.streaming:
            print("Camera is already streaming.")
            return

        self.streaming = True
        self.frame_callback = frame_callback
        self.thread = Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        print("Streaming started.")

    def _stream_loop(self):
        prev_time = time.time()

        while self.streaming:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # FPS calculation (let UI decide how to display)
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time

            # Send frame + fps back to UI
            if self.frame_callback:
                self.frame_callback(frame, fps)

        print("Stream loop exited.")

    def stop_streaming(self):
        if self.streaming:
            self.streaming = False
            if self.thread:
                self.thread.join()
                self.thread = None
            print("Streaming stopped.")