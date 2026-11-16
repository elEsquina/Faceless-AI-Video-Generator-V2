#!/usr/bin/env bash
# Execute exactly one selected rendering engine. No background services or scheduler.
set -euo pipefail
cd "$(dirname "$0")"
usage() { echo 'Usage: ./run_one.sh manim|blender|remotion|ffmpeg [--gpu]' >&2; exit 2; }
[[ $# -ge 1 && $# -le 2 ]] || usage
engine="$1"
[[ "$engine" =~ ^(manim|blender|remotion|ffmpeg)$ ]] || usage
flag="${2:-}"
[[ -z "$flag" || "$flag" == '--gpu' ]] || usage
mkdir -p workspace/output
DC=(docker compose -f compose.yaml)
if [[ "$flag" == '--gpu' ]]; then
  if [[ "$engine" != blender ]]; then
    echo 'GPU passthrough is configured for Blender; run this engine without --gpu.' >&2
    exit 2
  fi
  DC+=(-f compose.gpu.yaml)
  "${DC[@]}" run --rm gpu-check
fi
case "$engine" in
  manim) "${DC[@]}" run --rm manim -ql --disable_caching -o manim.mp4 scenes/manim_smoke.py ManimSmoke ;;
  blender) "${DC[@]}" run --rm --build blender blender -b -t 2 -P /workspace/scenes/blender_smoke.py ;;
  remotion) "${DC[@]}" run --rm --build remotion npm run smoke ;;
  ffmpeg) "${DC[@]}" run --rm --build ffmpeg -y -loop 1 -framerate 30 -i /workspace/output/blender.png -t 1 -pix_fmt yuv420p /workspace/output/ffmpeg.mp4 ;;
esac
printf '\nDone: %s\n' "$engine"
