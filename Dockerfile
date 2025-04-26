# Use Python 3.9 as the base image for ARM64 (Apple Silicon)
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    unzip \
    libsndfile1 \
    libblas-dev \
    liblapack-dev \
    ffmpeg \
    sox \
    autoconf \
    automake \
    libtool \
    pkg-config \
    python3-dev \
    libboost-all-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to reduce memory usage during compilation
ENV CFLAGS="-O2 -g" \
    CXXFLAGS="-O2 -g" \
    MAKEFLAGS="-j1"

# Install OpenFst (required for pynini) with memory optimizations
WORKDIR /tmp
RUN wget http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.8.2.tar.gz && \
    tar -xzvf openfst-1.8.2.tar.gz && \
    rm openfst-1.8.2.tar.gz && \
    cd openfst-1.8.2 && \
    ./configure --enable-far --enable-pdt --enable-mpdt --enable-grm \
                --enable-static --enable-shared --enable-bin \
                --enable-compact-fsts --enable-compress --enable-const-fsts \
                --enable-lookahead-fsts --enable-special && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf openfst-1.8.2 && \
    # Verify OpenFst installation
    echo "Checking for required OpenFst libraries:" && \
    ls -la /usr/local/lib/libfst* && \
    echo "Verifying scripts libraries:" && \
    ls -la /usr/local/lib/libfstfar* /usr/local/lib/libfstscript* && \
    echo "Verifying include files:" && \
    ls -la /usr/local/include/fst || true

# Reset environment variables for normal operation
ENV CFLAGS="" \
    CXXFLAGS="" \
    MAKEFLAGS=""

# Create working directory
WORKDIR /app

# Install Python package tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch and torchaudio for CPU (since this is ARM64, we'll use CPU versions)
# Split into separate commands for better cache utilization
RUN pip install --no-cache-dir --no-deps torch==2.0.1
RUN pip install --no-cache-dir --no-deps torchaudio==2.0.2

# Install specific numpy version that works well with NeMo
RUN pip install --no-cache-dir "numpy<1.24.0,>=1.20.0"

# Install required packages for NeMo in smaller batches
# Batch 1: Basic dependencies
RUN pip install --no-cache-dir \
    cython==0.29.36 \
    packaging \
    sox \
    librosa==0.10.1 \
    "pydantic<2.0.0" \
    python-dateutil \
    ruamel.yaml \
    wrapt \
    wget \
    text-unidecode

# Batch 2: Hydra and PyTorch related dependencies
RUN pip install --no-cache-dir \
    hydra-core==1.2.0 \
    omegaconf==2.2.3 \
    pytorch-lightning==1.9.5 \
    onnx>=1.7.0

# Batch 3: NLP and tokenization tools
RUN pip install --no-cache-dir \
    sentencepiece==0.1.99 \
    transformers==4.26.1 \
    huggingface-hub==0.17.3 \
    tokenizers==0.13.3 \
    nltk \
    sacremoses

# Batch 4: Audio and speech processing tools - broken into smaller parts
# Batch 4a: Soundfile and other audio related tools
RUN pip install --no-cache-dir \
    soundfile==0.12.1 \
    braceexpand \
    pyannote-core \
    pyannote-metrics

# Batch 4b: NLP tools
RUN pip install --no-cache-dir \
    editdistance \
    inflect

# Batch 4c: G2P tools
RUN pip install --no-cache-dir \
    g2p-en

# Batch 4d: Install youtokentome from source
RUN pip install --no-cache-dir \
    youtokentome==1.0.6

# Batch 4e: Install pynini (which requires OpenFst)
# Use environment variables to help pynini find OpenFst
ENV OPENFST_PATH=/usr/local \
    CPATH=/usr/local/include \
    LIBRARY_PATH=/usr/local/lib \
    LD_LIBRARY_PATH=/usr/local/lib \
    LDFLAGS="-L/usr/local/lib" \
    CPPFLAGS="-I/usr/local/include"

# Install pynini with specific options to find OpenFst
# Build from source with debug output
RUN pip install --verbose --no-cache-dir --no-build-isolation pynini==2.1.5 && \
    # Create a simple test to verify pynini installation
    python -c "import pynini; print('Pynini successfully imported')"

# Batch 5: Data processing and utilities
RUN pip install --no-cache-dir \
    marshmallow \
    pandas \
    webdataset==0.1.62

# Install NeMo - using a specific version known to work with these dependencies
# Split into two steps to reduce memory usage
RUN pip download --no-cache-dir "nemo_toolkit[asr]==1.20.0" --extra-index-url https://pypi.nvidia.com
RUN pip install --no-cache-dir --no-deps nemo_toolkit-1.20.0-py3-none-any.whl && \
    rm -f nemo_toolkit-1.20.0-py3-none-any.whl

# Verify NeMo installation
RUN python -c "import nemo; print(f'NeMo version: {nemo.__version__}')"

# Expose a port for potential Jupyter or API use
EXPOSE 8888

# Set the entrypoint to python
ENTRYPOINT ["python"]

# Additional dependencies for Sortformer and audio pipeline
RUN pip install --no-cache-dir \
    gunicorn==20.1.0 \
    fastapi==0.95.0 \
    uvicorn==0.21.1 \
    redis==4.3.4 \
    requests>=2.25.0 \
    pydantic<2.0.0 \
    tqdm>=4.62.3

# Create necessary directories
RUN mkdir -p /app/raw_audio /app/processed_audio /app/models /app/logs /app/configs /app/transcribed /app/summaries

# Set environment variables for pipeline
ENV PYTHONPATH=/app


# Default command (can be overridden)
CMD ["--version"]

