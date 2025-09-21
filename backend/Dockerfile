FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y gcc libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./requirements.txt
# Install specific torch cpu wheels first
RUN pip install --upgrade pip
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.2.0 torchvision==0.17.0
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--app-dir","/app"]
