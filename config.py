# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'face_database.db')
IMAGE_FOLDER = os.path.join(BASE_DIR, 'images')
DATABASE_PKL = os.path.join(BASE_DIR, 'face_database.pkl')

FACE_MODEL_NAME = "buffalo_l"
FACE_MODEL_PROVIDERS = ['CUDAExecutionProvider', 'CPUExecutionProvider']
FACE_MODEL_CTX_ID = 0
FACE_MODEL_DET_SIZE = (640, 640)
