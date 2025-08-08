# camera_api.py


#when to use Event()
##until some event happens the thread keeps looping


import cv2
import time
from threading import Thread, Event, Lock
from collections import deque


class CircularBuffer:
    def __init__(self, max_size=10):
        self.buffer = deque(maxlen=max_size)
        self.lock = Lock()

    def push(self, item):
        with self.lock:
            self.buffer.append(item)

    def pop(self):
        with self.lock:
            if self.buffer:
                return self.buffer.popleft()
            return None

    def is_empty(self):
        with self.lock:
            return len(self.buffer) == 0

    def clear(self):
        with self.lock:
            self.buffer.clear()


class CameraAPI:
    def __init__(self, buffer=None):
        self.cap = None
        self.streaming = False
        self.thread = None
        self.stop_event = Event()
        self.buffer = buffer if buffer else CircularBuffer(max_size=128)

    def open_camera(self, index=0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap = None
            raise RuntimeError("Failed to open camera.")
        print(f"Camera {index} opened.")

    def close_camera(self):
        self.stop_streaming()
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera closed.")

    def start_streaming(self):
        if not self.cap:
            raise RuntimeError("Camera not opened.")
        if self.streaming:
            print("Already streaming.")
            return

        self.streaming = True
        self.stop_event.clear()
        self.thread = Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        print("Streaming started.")

    def _stream_loop(self):
        prev_time = time.time()
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                continue

            current_time = time.time()
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time

            self.buffer.push((frame, fps))

        self.streaming = False
        print("Streaming stopped.")

    def stop_streaming(self):
        if self.streaming:
            self.stop_event.set()
            if self.thread:
                self.thread.join()
            self.thread = None

    def get_buffer(self):
        return self.buffer