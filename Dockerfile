# File: Dockerfile
FROM nvcr.io/nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Install Python and system-level audio/image libraries
RUN apt-get update && apt-get install -y \
    python3-pip \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --upgrade transformers

# Copy your app code
COPY . .

EXPOSE 8765

# Run either in normal or maintenance mode
CMD ["python3", "main.py"]