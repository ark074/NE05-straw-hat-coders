import os
import cv2
import numpy as np
from typing import List, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STUDENTS_DIR = os.path.join(DATA_DIR, "students")
MODEL_PATH = os.path.join(DATA_DIR, "lbph_model.yml")
os.makedirs(STUDENTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Use Haar cascade for face detection (bundled with opencv)
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def detect_faces_gray(image_gray):
    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5, minSize=(60,60))
    return faces

def enroll_student(student_id: str, images: List[np.ndarray]) -> None:
    # Save enrollment images for a student and retrain model.
    student_folder = os.path.join(STUDENTS_DIR, student_id)
    os.makedirs(student_folder, exist_ok=True)
    # save images as grayscale jpg
    for i, img in enumerate(images):
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        path = os.path.join(student_folder, f"{i}.jpg")
        cv2.imwrite(path, img_gray)
    train_model()

def _gather_training_data() -> Tuple[List[np.ndarray], List[int], dict]:
    X = []
    y = []
    label_map = {}
    curr_label = 0
    for student in sorted(os.listdir(STUDENTS_DIR)):
        student_folder = os.path.join(STUDENTS_DIR, student)
        if not os.path.isdir(student_folder):
            continue
        label_map[curr_label] = student
        for fname in os.listdir(student_folder):
            fpath = os.path.join(student_folder, fname)
            img = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            # detect face and crop the largest face region
            faces = detect_faces_gray(img)
            if len(faces) == 0:
                face_img = cv2.resize(img, (200,200))
            else:
                # choose largest face
                x,y,w,h = max(faces, key=lambda r: r[2]*r[3])
                face_img = cv2.resize(img[y:y+h, x:x+w], (200,200))
            X.append(face_img)
            y.append(curr_label)
        curr_label += 1
    return X, y, label_map

def train_model():
    X, y, label_map = _gather_training_data()
    if len(X) == 0:
        # remove model if exists
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        return
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(X, np.array(y))
    recognizer.write(MODEL_PATH)
    # save label map
    import json
    with open(os.path.join(DATA_DIR, "label_map.json"), "w") as fh:
        json.dump(label_map, fh)

def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, {}
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    import json
    with open(os.path.join(DATA_DIR, "label_map.json"), "r") as fh:
        label_map = json.load(fh)
    return recognizer, label_map

def recognize_from_image(img_bgr, threshold=70):
    # Return list of (student_id, confidence, bbox) for faces recognized in the image.
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if len(img_bgr.shape)==3 else img_bgr
    faces = detect_faces_gray(gray)
    recognizer, label_map = load_model()
    results = []
    for (x,y,w,h) in faces:
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200,200))
        if recognizer is None:
            results.append((None, None, (int(x),int(y),int(w),int(h))))
            continue
        label, conf = recognizer.predict(face)
        student_id = label_map.get(str(label)) or label_map.get(label)
        # lower confidence is better for LBPH; threshold chosen empirically; smaller is more certain
        if conf <= threshold:
            results.append((student_id, float(conf), (int(x),int(y),int(w),int(h))))
        else:
            results.append((None, float(conf), (int(x),int(y),int(w),int(h))))
    return results
