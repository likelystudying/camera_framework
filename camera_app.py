# camera_app.py

import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
import os
from camera_api import CameraAPI, CircularBuffer


class FrameConsumer(QThread):
    frame_ready = pyqtSignal(object, float)  # Emits (frame, fps)

    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer
        self.running = True

    def run(self):
        while self.running:
            if not self.buffer.is_empty():
                item = self.buffer.pop()
                if item:
                    frame, fps = item
                    self.frame_ready.emit(frame, fps)
            else:
                self.msleep(10)  # avoid busy waiting

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Camera Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.image_label = QLabel("Camera feed will appear here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFrameStyle(QFrame.Box)

        self.fps_label = QLabel("FPS: 0.00")
        self.save_button = QPushButton("Save Frame")
        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.fps_label)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.buffer = CircularBuffer(10)
        self.camera = CameraAPI(self.buffer)
        self.consumer = None  # will be created on start

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.save_button.clicked.connect(self.save_current_frame)

        self.last_frame = None

    def start_camera(self):
        try:
            if self.camera.cap is None:
                self.camera.open_camera()

            # If a consumer thread exists and running, stop it first
            if self.consumer and self.consumer.isRunning():
                self.consumer.stop()
                self.consumer.wait()

            # Clear buffer to avoid stale frames
            self.buffer.clear()

            # Create new consumer thread and start
            self.consumer = FrameConsumer(self.buffer)
            self.consumer.frame_ready.connect(self.display_frame)
            self.consumer.start()

            self.camera.start_streaming()
        except RuntimeError as e:
            self.image_label.setText(str(e))

    def stop_camera(self):
        if self.consumer and self.consumer.isRunning():
            self.consumer.stop()
            self.consumer.wait()

        self.camera.stop_streaming()
        self.camera.close_camera()

        self.buffer.clear()

        self.image_label.setText("Camera stopped.")
        self.fps_label.setText("FPS: 0.00")

    def display_frame(self, frame, fps):
        self.last_frame = frame.copy()

        overlay = frame.copy()
        text = f"FPS: {fps:.2f}"
        cv2.putText(overlay, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))

        self.fps_label.setText(text)

    def save_current_frame(self):
        if self.last_frame is not None:
            os.makedirs("saved_frames", exist_ok=True)
            filename = f"saved_frames/frame_{int(time.time())}.png"
            cv2.imwrite(filename, self.last_frame)
            print(f"Saved frame to {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CameraApp()
    viewer.show()
    sys.exit(app.exec_())