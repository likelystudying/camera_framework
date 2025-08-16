# camera_asourcpp.py

#python3 -m venv venv
#source venv/bin/activate
# camera_app_2.py
# camera_app_2.py

import sys
import time
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
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

        # --- Camera display ---
        self.image_label = QLabel("Camera feed will appear here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFrameStyle(QFrame.Box)

        # --- FPS label ---
        self.fps_label = QLabel("FPS: 0.00")

        # --- Buttons ---
        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.save_button = QPushButton("Save Frame")
        self.apply_button = QPushButton("Apply Settings")

        # index input
        self.index_input = QLineEdit("0")

        # --- Width/Height/FPS input fields ---
        self.width_input = QLineEdit("640")
        self.height_input = QLineEdit("480")
        self.fps_input = QLineEdit("30")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.apply_button)

        button_layout.addWidget(QLabel("Index"))
        button_layout.addWidget(self.index_input)

        button_layout.addWidget(QLabel("Width"))
        button_layout.addWidget(self.width_input)
        button_layout.addWidget(QLabel("Height"))
        button_layout.addWidget(self.height_input)
        button_layout.addWidget(QLabel("FPS"))
        button_layout.addWidget(self.fps_input)
        button_layout.addWidget(self.fps_label)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- Camera setup ---
        self.buffer = CircularBuffer(10)
        self.camera = CameraAPI(self.buffer)
        self.consumer = FrameConsumer(self.buffer)
        self.consumer.frame_ready.connect(self.display_frame)
        self.last_frame = None

        # --- Button connections ---
        self.start_button.clicked.connect(self.on_start_button)
        self.stop_button.clicked.connect(self.stop_camera)
        self.save_button.clicked.connect(self.save_current_frame)
        self.apply_button.clicked.connect(self.apply_settings)

        self.log.info("initialize --end")

    def apply_settings(self):
        """Apply width, height, and FPS when streaming is stopped."""
        if self.camera.streaming:
            self.log.warning("Stop streaming before applying settings.")
            return

        try:
            w = int(self.width_input.text())
            h = int(self.height_input.text())
            f = float(self.fps_input.text())

            self.camera.settings.set("width", w)
            self.camera.settings.set("height", h)
            self.camera.settings.set("fps", f)
            self.camera.settings.apply()

            self.log.info(f"Applied settings: width={w}, height={h}, fps={f}")
        except ValueError as e:
            self.log.error(f"Invalid input for settings: {e}")

    def on_start_button(self):
        try:
            index = int(self.index_input.text())
        except ValueError:
            self.log.error("Invalid camera index")
            return
        self.start_camera(index)

    def start_camera(self, index):
        """Start camera streaming using a specific camera index."""
        self.log.info(f"start_camera(index={index}) --start")
        try:
            # Stop existing consumer thread
            if self.consumer.isRunning():
                self.consumer.stop()
                self.consumer.wait()

            if self.camera.streaming:
                self.camera.stop_streaming()

            self.buffer.clear()

            if self.camera.cap is not None:
                self.camera.cap.release()
                self.camera.cap = None
                time.sleep(0.2)

            # open camera with selected index
            self.camera.open_camera(index=index)

            self.consumer = FrameConsumer(self.buffer)
            self.consumer.frame_ready.connect(self.display_frame)
            self.consumer.start()
            self.camera.start_streaming()
            self.log.info(f"Camera {index} started.")

        except RuntimeError as e:
            self.log.error(f"Error starting camera: {e}")
            self.image_label.setText(str(e))
        self.log.info("start_camera --end")

    def stop_camera(self):
        self.log.info("Stopping camera...")
        if self.consumer.isRunning():
            self.consumer.stop()
            self.consumer.wait()

        self.camera.stop_streaming()
        self.camera.close_camera()
        self.buffer.clear()

        self.image_label.setText("Camera stopped.")
        self.fps_label.setText("FPS: 0.00")
        self.log.info("Camera stopped.")

    def display_frame(self, frame, fps):
        self.last_frame = frame.copy()
        overlay = frame.copy()
        #text = f"FPS: {fps:.2f}"
        #cv2.putText(overlay, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        #self.fps_label.setText(text)

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