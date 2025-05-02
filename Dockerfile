# COMPLETE REPLACEMENT FOR Dockerfile
FROM nvcr.io/nvidia/pytorch:24.05-py3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    tcl8.6 \
    tk8.6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --extra-index-url https://pypi.nvidia.com

COPY . .

CMD ["python", "core/audio/audio_processor.py"]
