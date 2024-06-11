# face_recognition/face_recognition_manager.py
import os
import pickle
import numpy as np
from scipy.spatial.distance import cdist
from insightface.app import FaceAnalysis
from config import FACE_MODEL_NAME, FACE_MODEL_PROVIDERS, FACE_MODEL_CTX_ID, FACE_MODEL_DET_SIZE, DATABASE_PKL

face_analysis_app = FaceAnalysis(name=FACE_MODEL_NAME, providers=FACE_MODEL_PROVIDERS)
face_analysis_app.prepare(ctx_id=FACE_MODEL_CTX_ID, det_size=FACE_MODEL_DET_SIZE)

def get_face_embedding_and_crop(frame):
    faces = face_analysis_app.get(frame)
    if len(faces) == 0:
        return None, None
    face = faces[0]
    bbox = face.bbox.astype(int)
    cropped_face = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    embedding = face.normed_embedding
    return embedding, cropped_face

def load_database():
    if os.path.exists(DATABASE_PKL):
        with open(DATABASE_PKL, 'rb') as f:
            return pickle.load(f)
    return {}

def save_database(database):
    with open(DATABASE_PKL, 'wb') as f:
        pickle.dump(database, f)

def update_database(person_name, new_embeddings):
    database = load_database()
    if person_name in database:
        database[person_name].extend(new_embeddings)
    else:
        database[person_name] = new_embeddings
    save_database(database)

def recognize_face(embedding, database, threshold=0.6):
    min_dist = float('inf')
    identity = None
    for person_name, embeddings in database.items():
        dists = cdist([embedding], embeddings, 'cosine')
        avg_dist = np.mean(dists)
        if avg_dist < min_dist:
            min_dist = avg_dist
            identity = person_name
    if min_dist > threshold:
        identity = "Unknown"
    confidence = 1 - min_dist
    return identity, confidence
