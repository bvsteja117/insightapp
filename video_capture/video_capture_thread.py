# video_capture/video_capture_thread.py
import cv2
import os
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from face_recognition.face_recognition_manager import get_face_embedding_and_crop, update_database
from config import IMAGE_FOLDER

ipcam= "rtsp://admin:1234Admin@192.168.1.250:554/cam/realmonitor?channel=1&subtype=0"
def create_directory_structure(person_name):
    person_path = os.path.join(IMAGE_FOLDER, person_name)
    if not os.path.exists(person_path):
        os.makedirs(person_path)
    return person_path

class VideoCaptureThread(QThread):
    finished = pyqtSignal(str, int)
    embeddingCaptured = pyqtSignal(np.ndarray, np.ndarray, str)

    def __init__(self, person_name, frames_per_second=5, images_folder=IMAGE_FOLDER):
        super().__init__()
        self.person_name = person_name
        self.frames_per_second = frames_per_second
        self.images_folder = images_folder
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(ipcam)
        frame_count = 0
        frame_interval = int(30 / self.frames_per_second)
        start_time = time.time()
        new_embeddings = []
        output_dir = create_directory_structure(self.person_name)
        existing_files = os.listdir(output_dir)
        if existing_files:
            max_index = max([int(f.split('_')[-1].split('.')[0]) for f in existing_files if f.endswith('.jpg')])
            frame_count = max_index + 1
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            current_time = time.time()
            elapsed_time = current_time - start_time
            if int(elapsed_time * 30) % frame_interval == 0:
                embedding, cropped_face = get_face_embedding_and_crop(frame)
                if embedding is not None and cropped_face is not None and frame_count<100:
                    new_embeddings.append(embedding)
                    frame_path = os.path.join(output_dir, f"{self.person_name}_{frame_count:04d}.jpg")
                    cv2.imwrite(frame_path, cropped_face)
                    self.embeddingCaptured.emit(embedding, cropped_face, frame_path)
                    frame_count += 1
                else:
                    self.stop()
        cap.release()
        if new_embeddings:
            update_database(self.person_name, new_embeddings)
        self.finished.emit(self.person_name, frame_count)

    def stop(self):
        self.running = False
        self.wait()
