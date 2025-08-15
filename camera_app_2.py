# camera_asourcpp.py

#python3 -m venv venv
#source venv/bin/activate

import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
import os
import logging
from camera_api_2 import CameraAPI, CircularBuffer, Logger


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

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()

        self.log = Logger(level=logging.DEBUG)
        self.log.info("initialize --start")

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
        self.consumer = FrameConsumer(self.buffer)
        self.consumer.frame_ready.connect(self.display_frame)

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.save_button.clicked.connect(self.save_current_frame)

        self.last_frame = None
        self.log.info("initialize --end")

    def start_camera(self):
        self.log.info("start_camera --start")
        try:
            self.log.info("Starting camera...")

            if self.camera.cap is not None:
                self.log.info("Releasing camera before re-opening")
                self.camera.cap.release()
                self.camera.cap = None
                time.sleep(0.5)

            self.camera.open_camera()

            if self.consumer and self.consumer.isRunning():
                self.log.info("Stopping existing consumer thread")
                self.consumer.stop()
                self.consumer.wait()

            self.buffer.clear()

            self.consumer = FrameConsumer(self.buffer)
            self.consumer.frame_ready.connect(self.display_frame)
            self.consumer.start()

            self.camera.start_streaming()
            self.log.info("Camera started.")

        except RuntimeError as e:
            self.log.info(f"Error starting camera: {e}")
            self.image_label.setText(str(e))

        self.log.info("start_camera --end")

    def stop_camera(self):
        self.log.info("Stopping camera...")
        self.log.info("stop_camera --start")
        if self.consumer and self.consumer.isRunning():
            self.consumer.stop()
            self.consumer.wait()

        self.camera.stop_streaming()
        self.camera.close_camera()

        self.buffer.clear()

        self.image_label.setText("Camera stopped.")
        self.fps_label.setText("FPS: 0.00")
        self.log.info("Camera stopped.")
        self.log.info("start_camera --end")

    # def stop_camera(self):
    #     if self.consumer and self.consumer.isRunning():
    #         self.consumer.stop()
    #         self.consumer.wait()  # wait ensures thread stopped before restart
    #         #self.consumer.stop()
    #     self.camera.stop_streaming()
    #     self.camera.close_camera()
    #     self.image_label.setText("Camera stopped.")
    #     self.fps_label.setText("FPS: 0.00")

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
            self.log.info(f"Saved frame to {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CameraApp()
    viewer.show()
    sys.exit(app.exec_())
