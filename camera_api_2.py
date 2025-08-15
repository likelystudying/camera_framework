# camera_api.py


#when to use Event()
##until some event happens the thread keeps looping


import cv2
import time
import os
import sys
import logging
from datetime import datetime
from threading import Thread, Event, Lock
from collections import deque

class Logger:
    _instance = None
    _lock = Lock()

    def __new__(cls, log_file=None, level=logging.INFO):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

                # Default log file path
                if log_file is None:
                    log_dir = "./log"
                    os.makedirs(log_dir, exist_ok=True)
                    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

                # Create logger
                cls._instance.logger = logging.getLogger("AppLogger")
                cls._instance.logger.setLevel(level)
                cls._instance.logger.propagate = False  # Avoid duplicate logs

                # Clear old handlers
                if cls._instance.logger.hasHandlers():
                    cls._instance.logger.handlers.clear()

                # Formatter with PID and TID
                formatter = logging.Formatter(
                    "%(asctime)s [PID:%(process)d] [TID:%(thread)d] [%(levelname)s] %(message)s",
                    "%Y-%m-%d %H:%M:%S"
                )

                # File handler
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)

                # Console handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)

                cls._instance.logger.addHandler(file_handler)
                cls._instance.logger.addHandler(console_handler)

            return cls._instance

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)


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