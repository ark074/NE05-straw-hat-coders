import os, json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from facenet_pytorch import InceptionResnetV1, MTCNN
import torch
from PIL import Image

DATA_DIR = Path(__file__).parent / "data"
EMB_PATH = DATA_DIR / "embeddings.npy"
LABELS_PATH = DATA_DIR / "labels.json"
os.makedirs(DATA_DIR, exist_ok=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# initialize models
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

def _load_embeddings() -> Tuple[np.ndarray, Dict[int,str]]:
    if not EMB_PATH.exists() or not LABELS_PATH.exists():
        return np.zeros((0,512), dtype=np.float32), {}
    embs = np.load(EMB_PATH)
    with open(LABELS_PATH, 'r') as fh:
        labels = json.load(fh)
    # labels saved as {"0":"alice", "1":"bob"}
    return embs, {int(k):v for k,v in labels.items()}

def _save_embeddings(embs: np.ndarray, labels: Dict[int,str]):
    np.save(EMB_PATH, embs)
    with open(LABELS_PATH, 'w') as fh:
        json.dump({str(k):v for k,v in labels.items()}, fh)

def enroll_student(student_id: str, pil_images: List[Image.Image]) -> None:
    """Compute embeddings for provided PIL images, average them, and append to store"""
    embs, labels = _load_embeddings()
    new_embs = []
    for img in pil_images:
        # detect and crop faces
        crops = mtcnn(img)
        if crops is None:
            continue
        # if multiple faces, pick first / iterate
        if isinstance(crops, list) or crops.ndim==4:
            # convert to batch if single
            pass
        # crops is tensor(s) of shape (3,160,160) or batch
        if crops.ndim == 3:
            batch = crops.unsqueeze(0)
        else:
            batch = crops
        with torch.no_grad():
            batch = batch.to(device)
            out = resnet(batch) # (N,512)
            for v in out:
                new_embs.append(v.cpu().numpy())
    if len(new_embs) == 0:
        return
    # average embeddings for this student
    avg = np.mean(np.stack(new_embs, axis=0), axis=0)
    if embs.shape[0] == 0:
        embs = np.stack([avg], axis=0)
        labels = {0: student_id}
    else:
        embs = np.vstack([embs, avg])
        labels = {k:v for k,v in labels.items()}
        new_idx = max(labels.keys())+1
        labels[new_idx] = student_id
    _save_embeddings(embs.astype(np.float32), labels)

from numpy.linalg import norm
def recognize_image(pil_image: Image.Image, threshold: float = 0.65):
    """Return list of dicts with student_id (or None), distance, bbox (x,y,w,h)"""
    boxes, _ = mtcnn.detect(pil_image)
    if boxes is None or len(boxes)==0:
        return []
    crops = mtcnn.extract(pil_image, boxes, save_path=None)
    # crops: list of PIL Images or tensors; use resnet to get embeddings
    tensors = []
    for c in crops:
        if isinstance(c, Image.Image):
            c = np.array(c)
        # facenet-pytorch extract returns tensors; ensure tensor
    # Use mtcnn(img, return_prob=False) to get tensors directly
    faces = mtcnn(pil_image, save_path=None)
    if faces is None:
        return []
    if faces.ndim == 3:
        faces_batch = faces.unsqueeze(0)
    else:
        faces_batch = faces
    with torch.no_grad():
        faces_batch = faces_batch.to(device)
        emb = resnet(faces_batch).cpu().numpy()  # (N,512)
    stored, labels = _load_embeddings()
    results = []
    for i, e in enumerate(emb):
        if stored.shape[0] == 0:
            results.append({"student_id": None, "distance": None, "bbox": [int(x) for x in boxes[i]]})
            continue
        # compute cosine distance
        sims = (stored @ e) / (np.linalg.norm(stored, axis=1) * np.linalg.norm(e) + 1e-10)
        # higher is more similar (cosine similarity). convert to distance = 1 - sim
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        if best_sim >= (1 - threshold):  # transform threshold to similarity; threshold default 0.65 means distance 0.35?
            student_id = labels.get(best_idx)
            results.append({"student_id": student_id, "similarity": best_sim, "bbox": [int(x) for x in boxes[i]]})
        else:
            results.append({"student_id": None, "similarity": best_sim, "bbox": [int(x) for x in boxes[i]]})
    return results
