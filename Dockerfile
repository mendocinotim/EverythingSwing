# COMPLETE REPLACEMENT FOR Dockerfile
FROM nvcr.io/nvidia/pytorch:24.05-py3

# Set environment to noninteractive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    tcl8.6 \
    tk8.6 \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# First install critical dependencies in correct order
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.24.0 && \
    pip install --no-cache-dir torch==2.3.0 && \
    pip install --no-cache-dir librosa==0.10.2 && \
    pip install --no-cache-dir nemo-toolkit[asr]==2.2.1 --extra-index-url https://pypi.nvidia.com && \
    pip install --no-cache-dir python-dotenv==1.1.0 pydantic==2.11.3 protobuf==3.20.3 ruamel.yaml==0.18.10 soundfile==0.12.1

# Copy application code
COPY . .

# Default command
CMD ["python", "core/audio/audio_processor.py"]
