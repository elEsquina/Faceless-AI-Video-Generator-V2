# Optional local CPU Kokoro test; GPU compose provides GPU device, but CUDA-enabled torch
# must be installed in a separate image for torch.cuda.is_available() to become True.
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
  espeak-ng libsndfile1 ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.6.0
RUN pip install --no-cache-dir kokoro==0.9.4 soundfile && python -m spacy download en_core_web_sm
WORKDIR /workspace
