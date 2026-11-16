# AI Video Docker sandbox

Standalone, local-only rendering sandbox for the V2 pipeline. No services expose ports and **no source/project directory is mounted**. Only `workspace/` is mounted as scene input and output. AI-generated code is untrusted: do not give it credentials, network access, Docker socket mounts, or unrestricted host directories.

## Services
- `manim`: official Manim Community stable Docker image, CPU renderer.
- `blender`: Ubuntu 24.04 Blender, Cycles CPU fallback; probes OptiX then CUDA when GPU visible.
- `remotion`: Node 22 + React + Three.js + GSAP + Remotion, renders test MP4.
- `ffmpeg`: FFmpeg encoder/compositor.
- `tts` (optional): Kokoro Python package with CPU PyTorch; import test only, **not** downloading voice weights or generating audio.
- `gpu-check` (GPU override): NVIDIA CUDA 12.8 diagnostic (`nvidia-smi`).

## On Ubuntu WSL2 with RTX 5050

Your Linux Docker daemon must have NVIDIA GPU support. Docker Desktop WSL2 backend or NVIDIA Container Toolkit on a native WSL2 Docker daemon are options; this project does not modify Windows or the host. Verify **in your Ubuntu terminal** before building:

```bash
docker info
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
```

WSL may expose `nvidia-smi` at `/usr/lib/wsl/lib/nvidia-smi`. Do not install Linux NVIDIA kernel drivers in WSL. If GPU passthrough fails, run the standard (CPU fallback) compose without override. RTX 5050 hardware acceleration depends on driver compatibility, the Blender build's supported backend, and successful Cycles device detection; GPU access alone does not prove Blender is using GPU.

## Single-video workflow (recommended)

Run **only the engine selected by the external AI agent**. Containers are ephemeral;
no engine runs until selected. Run in sequence, not simultaneously:

```bash
./run_one.sh manim
./run_one.sh blender --gpu   # requires GPU passthrough
./run_one.sh remotion
# ./run_one.sh ffmpeg    # requires blender.png from Blender test
```

For a single video containing multiple scene technologies, invoke one engine
at a time, then compose the scene outputs with FFmpeg. The MCP runner will
perform these calls in the future; it is not yet implemented.

## Smoke test: CPU fallback (all four render engines)

```bash
chmod +x smoke.sh
./smoke.sh
```

## Smoke test: RTX GPU requested

```bash
./smoke.sh --gpu
```

Look for `BLENDER_RENDER_DEVICE=OPTIX...` or `CUDA...` in Blender output. If it prints `CPU`, the GPU was passed through but not successfully selected by Cycles. Inspect package/driver capabilities before claiming GPU acceleration.

## One-off tests

```bash
docker compose run --rm manim --version
docker compose run --rm blender blender -b --version
docker compose run --rm remotion npm run list
docker compose run --rm ffmpeg -version
# Optional TTS image and import check (may download gigabytes of dependencies):
docker compose --profile tts build tts
docker compose --profile tts run --rm tts
```

Output goes into `workspace/output/` and for Manim to `workspace/media/` (default Manim layout). GPUs are **not required** to render the Manim/Remotion smoke tests. Headless Chrome/Three.js may use software WebGL rendering. For GPU-assisted local voice synthesis, create a separate CUDA-enabled PyTorch image; the default TTS image is CPU-only even with the GPU compose override.

## Integration

Your future MCP runner can call these Compose services with prepared scene files inside `workspace/`; do **not** mount the entire repository or Docker socket. Treat generated Blender Python and Remotion TSX as arbitrary executable code. Pin image digests and dependency lockfiles before production use.

## Verification status

The files and shell scripts can be statically checked outside Docker. This authoring environment has no Docker CLI or accessible NVIDIA GPU, so container image builds, CUDA passthrough, and render outputs have **not** been executed or verified here. Run `./smoke.sh --gpu` in Ubuntu to test real hardware.
