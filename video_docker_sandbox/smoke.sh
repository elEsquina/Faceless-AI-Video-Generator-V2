#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p workspace/output
DC=(docker compose -f compose.yaml)
if [[ "${1:-}" == "--gpu" ]]; then
  DC+=( -f compose.gpu.yaml )
  "${DC[@]}" run --rm gpu-check
fi
"${DC[@]}" build blender remotion ffmpeg
"${DC[@]}" pull manim
"${DC[@]}" run --rm manim -ql --disable_caching -o manim.mp4 scenes/manim_smoke.py ManimSmoke
"${DC[@]}" run --rm blender blender -b -t 2 -P /workspace/scenes/blender_smoke.py
"${DC[@]}" run --rm remotion npm run smoke
"${DC[@]}" run --rm ffmpeg -y -i /workspace/output/blender.png -vf format=yuv420p -t 1 /workspace/output/ffmpeg.mp4
printf '\nRender outputs:\n'
find workspace -type f \( -name '*.mp4' -o -name '*.png' \) | sort
