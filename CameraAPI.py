import cv2
import threading
import time

class CameraAPI:
    def __init__(self):
        self.cap = None
        self.streaming = False
        self.stream_thread = None

    def init_library(self):
        print("Camera lib initiated")
    
    def open_camera(self, index=0):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError ("Cannot open")
        print("open camera")

    def close_camera(self, index=0):
        if self.cap.isOpened():
            self.cap.release()
            self.cap = None
            print("close camera")
        else:
            print("camera was not open")

    def start_capture(self, num_frames=10):
        if not self.cap:
            raise RuntimeError("Camera not opened.")
        frames = []
        for _ in range(num_frames):
            ret, frame = self.cap.read()
            if not ret:
                break
            frames.append(frame)
        print(f"Captured {len(frames)} frames.")
        return frames

    def start_streaming(self):
        if not self.cap:
            raise RuntimeError("Camera not opened.")
        if self.streaming:
            print("Already streaming.")
            return
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop)
        self.stream_thread.start()
        print("Streaming started.")

    def _stream_loop(self):
        while self.streaming:
            ret, frame = self.cap.read()
            if not ret:
                break
            cv2.imshow("Live Stream", frame) #can't run from a thread
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_streaming()
                break
        cv2.destroyAllWindows()

    def stop_streaming(self):
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join()
            self.stream_thread = None
        print("Streaming stopped.")


cam = CameraAPI()
cam.init_library()
cam.open_camera(0)
cam.start_streaming()
print("sleepp...")
time.sleep(3)
cam.stop_streaming()
cam.close_camera()