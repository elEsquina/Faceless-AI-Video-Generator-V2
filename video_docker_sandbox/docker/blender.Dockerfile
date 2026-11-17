FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends blender ffmpeg ca-certificates libegl1 libgl1-mesa-dri libgl1 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
