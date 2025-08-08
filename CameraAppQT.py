import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QTimer


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Viewer")

        # UI Components
        self.image_label = QLabel("Camera feed will appear here")
        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.last_time = time.time()
        self.fps = 0

        # Connect buttons
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.image_label.setText("Failed to open camera.")
            return
        self.timer.start(30)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                # FPS calculation
                now = time.time()
                dt = now - self.last_time
                self.last_time = now
                if dt > 0:
                    self.fps = 1.0 / dt

                # Draw FPS on the frame
                fps_text = f"FPS: {self.fps:.2f}"
                cv2.putText(frame, fps_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Convert to QImage and display
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.image_label.setPixmap(QPixmap.fromImage(q_img))
                self.setWindowTitle(f"Camera Viewer - {fps_text}")

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.image_label.setText("Camera stopped.")
        self.setWindowTitle("Camera Viewer")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CameraApp()
    viewer.resize(640, 480)
    viewer.show()
    sys.exit(app.exec_())