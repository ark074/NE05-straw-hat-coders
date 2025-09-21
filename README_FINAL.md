# Attendance AI — Pro (FaceNet embeddings + Professional UI)
This project uses facenet-pytorch (MTCNN + InceptionResnetV1) for embeddings and a React/Tailwind frontend.

Key points:
- Backend: FastAPI with facenet-pytorch; embeddings stored in backend/data/
- Frontend: Vite React app in frontend_pro, built and served by nginx in Docker
- To run: docker compose up --build
- API endpoints served at http://localhost:8000; frontend at http://localhost:3000
