
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from sqlalchemy import update, delete
import os, io
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from PIL import Image
import uvicorn
import numpy as np
from pathlib import Path
import model_utils as mu
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime, select
from datetime import datetime

app = FastAPI(title="Attendance Face Recognition (FaceNet embeddings)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "attendance.db"
os.makedirs(DATA_DIR, exist_ok=True)

# simple SQLite DB using SQLAlchemy core
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
meta = MetaData()
attendance = Table("attendance", meta,
                   Column("id", Integer, primary_key=True),
                   Column("student_id", String, nullable=False),
                   Column("timestamp", DateTime, nullable=False),
                   Column("source", String, nullable=True))
meta.create_all(engine)

@app.post("/enroll")
async def enroll(student_id: str = Form(...), files: list[UploadFile] = File(...)):
    images = []
    for f in files:
        contents = await f.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        images.append(img)
    mu.enroll_student(student_id, images)
    return {"status":"ok", "enrolled": student_id, "images": len(images)}

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    results = mu.recognize_image(img, threshold=0.65)
    # log attendance for recognized students
    conn = engine.connect()
    recorded = []
    for r in results:
        if r.get("student_id"):
            ins = attendance.insert().values(student_id=str(r["student_id"]), timestamp=datetime.utcnow(), source="api")
            conn.execute(ins)
            recorded.append({"student_id": r["student_id"], "similarity": r.get("similarity"), "bbox": r.get("bbox")})
    conn.close()
    return {"results": results, "recorded": recorded}

@app.get("/attendance")
def get_attendance(limit: int = 100):
    conn = engine.connect()
    q = select(attendance).order_by(attendance.c.timestamp.desc()).limit(limit)
    rows = conn.execute(q).fetchall()
    conn.close()
    return [{"id": r[0], "student_id": r[1], "timestamp": r[2].isoformat(), "source": r[3]} for r in rows]

@app.get("/download_embeddings")
def download_embeddings():
    path = Path(mu.EMB_PATH)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Embeddings not found")
    return FileResponse(path, media_type="application/octet-stream", filename="embeddings.npy")

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


@app.post("/start_session")
def start_session():
    """Start a new attendance session: mark everyone Absent."""
    conn = engine.connect()
    try:
        # Clear today's records
        today = datetime.now().date()
        conn.execute(delete(attendance).where(attendance.c.date == today))
        
        # Load all student IDs from labels.json
        labels_path = Path(__file__).parent.parent / "attendance_data" / "labels.json"
        with open(labels_path, "r") as f:
            labels = json.load(f)
        
        students = set(labels.values())
        for sid in students:
            conn.execute(attendance.insert().values(
                student_id=sid,
                status="Absent",
                date=today,
                timestamp=datetime.now()
            ))
        conn.commit()
        return {"message": "Session started. All students marked Absent."}
    finally:
        conn.close()


@app.post("/mark_attendance")
async def mark_attendance(file: UploadFile = File(...)):
    """Mark present only for detected faces."""
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Recognize faces
    recognized_ids = mu.recognize_faces(image)

    conn = engine.connect()
    try:
        today = datetime.now().date()
        for sid in recognized_ids:
            conn.execute(
                update(attendance)
                .where(attendance.c.student_id == sid)
                .where(attendance.c.date == today)
                .values(status="Present", timestamp=datetime.now())
            )
        conn.commit()
        return {"message": "Attendance updated", "present": recognized_ids}
    finally:
        conn.close()


@app.get("/attendance_report")
def attendance_report():
    """Generate PDF of today's attendance and return as file."""
    today = datetime.now().date()
    conn = engine.connect()
    try:
        result = conn.execute(select([attendance.c.student_id, attendance.c.status])
                              .where(attendance.c.date == today)).fetchall()
    finally:
        conn.close()

    # Separate present and absent
    present = [r[0] for r in result if r[1] == "Present"]
    absent = [r[0] for r in result if r[1] == "Absent"]

    # Build PDF
    pdf_path = Path(__file__).parent / f"attendance_report_{today}.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Attendance Report - {today}", styles['Title']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Present Students:", styles['Heading2']))
    for sid in present:
        elements.append(Paragraph(str(sid), styles['Normal']))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Absent Students:", styles['Heading2']))
    for sid in absent:
        elements.append(Paragraph(str(sid), styles['Normal']))

    doc.build(elements)

    return FileResponse(str(pdf_path), media_type="application/pdf", filename=f"attendance_report_{today}.pdf")
