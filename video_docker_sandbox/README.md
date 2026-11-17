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
at a time, then compose the scene outputs with FFmpeg. The working MCP Omega adapter performs these calls sequentially for authored jobs.

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

The MCP runner calls these Compose services with prepared scene files inside `workspace/`; do **not** mount the entire repository or Docker socket. Treat generated Blender Python and Remotion TSX as arbitrary executable code. Pin image digests and dependency lockfiles before production use.

## Verification status

On 2026-11-17, actual MCP/Docker execution produced three original 30-second 1280×720/30-fps videos with Kokoro narration, captions and FFmpeg composition. Actual frames and matched comparisons were reviewed. See [implementation/evidence report](../docs/animation/report.md). Headless Eevee was verified after user-authorized EGL/Mesa installation. GPU passthrough and per-engine acceleration are separate checks; use the diagnostics below rather than inferring GPU support from a class or container flag.

For native Ubuntu WSL Docker runtime setup, review and run `sudo bash ../scripts/setup_gpu_wsl.sh` in your Ubuntu terminal. This configures the signed NVIDIA Container Toolkit and Docker, not Windows or Linux display drivers. The administrator authenticates locally. `scripts/gpu_kernel_probe.py` verifies actual CUDA kernel execution; `nvidia-smi` alone does not prove renderer acceleration.

## Verified Blender GPU path

On this installation, NVIDIA Container Toolkit 1.20.2 and the separate Blender 4.5.16 LTS image rendered real CUDA frames on the RTX 5050. OptiX is unavailable here; CUDA and GPU denoising are verified. The default older CPU image remains available.

From the repository root, the optional image and repeatable verification commands are:

```bash
docker compose -f video_docker_sandbox/compose.yaml -f video_docker_sandbox/compose.gpu.yaml build blender
python scripts/verify_blender_gpu.py e42f8010
```

The verification command replays the three actual character-frame probes stored in that job, writes its evidence there, and registers the exact successfully tested image ID in `workspace/.cache/blender_gpu.json`. A rebuilt image must be reverified. No image is registered merely from `nvidia-smi` or device enumeration.

New kids MCP jobs automatically receive `blender_device: auto`; the adapter selects the verified image and the staged `configure_renderer` helper selects CUDA. Existing legacy jobs default to CPU. Set `FACELESS_GPU=cpu` for CPU or job `render_settings.json` to `{"blender_device":"gpu"}` to require a verified GPU profile. Authored scripts must use the staged renderer helper and compatible Blender APIs. Actual MCP job `7c231c5a` exercised this automatic route successfully. Current Manim, Remotion and Kokoro configurations remain CPU workloads.
