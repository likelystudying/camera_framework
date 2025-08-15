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
import inspect

import os
import sys
import logging
from datetime import datetime
from threading import Lock
import inspect

import inspect
import logging

#todo move
class ClassNameFilter(logging.Filter):
    """Attach actual class and caller function to log record."""
    def filter(self, record):
        frame = inspect.currentframe()
        # Walk up past the logger method itself
        while frame:
            code_name = frame.f_code.co_name
            module_name = frame.f_globals.get("__name__", "")
            if module_name not in ("logging", __name__) and code_name not in ("info", "warning", "error"):
                if "self" in frame.f_locals:
                    record.classname = frame.f_locals["self"].__class__.__name__
                else:
                    record.classname = "<module>"
                # Override funcName with actual caller
                record.funcName = code_name
                break
            frame = frame.f_back
        return True

class Logger:
    _instance = None
    _lock = Lock()

    def __new__(cls, log_file=None, level=logging.INFO):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

                if log_file is None:
                    log_dir = "./log"
                    os.makedirs(log_dir, exist_ok=True)
                    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

                cls._instance.logger = logging.getLogger("AppLogger")
                cls._instance.logger.setLevel(level)
                cls._instance.logger.propagate = False

                if cls._instance.logger.hasHandlers():
                    cls._instance.logger.handlers.clear()

                formatter = logging.Formatter(
                    "%(asctime)s [PID:%(process)d] [TID:%(thread)d] "
                    "[%(classname)s.%(funcName)s] [%(levelname)s] %(message)s",
                    "%Y-%m-%d %H:%M:%S"
                )

                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                file_handler.addFilter(ClassNameFilter())

                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                console_handler.addFilter(ClassNameFilter())

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
        self.log = Logger()

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
        self.log = Logger()


    def open_camera(self, index=0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap = None
            self.log.error("Failed to open camera")
            raise RuntimeError("Failed to open camera.")
        self.log.info(f"Camera {index} opened.")

    def close_camera(self):
        self.stop_streaming()
        if self.cap:
            self.cap.release()
            self.cap = None
            self.log.info("Camera closed.")

    def start_streaming(self):
        if not self.cap:
            raise RuntimeError("Camera not opened.")
        if self.streaming:
            self.log.info("Already streaming.")
            return

        self.streaming = True
        self.stop_event.clear()
        self.thread = Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        self.log.info("Streaming started.")

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
        self.log.info("Streaming stopped.")

    def stop_streaming(self):
        if self.streaming:
            self.stop_event.set()
            if self.thread:
                self.thread.join()
            self.thread = None

    def get_buffer(self):
        return self.buffer