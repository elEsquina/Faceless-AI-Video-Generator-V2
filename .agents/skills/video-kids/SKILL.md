---
name: video-kids
description: Rigged Blender stories with executable production utilities and evidence-based frame QA.
---

Activate for rigged blender stories. Read `prompt.md` and exactly the current job's `skills/kids_stories.md`. The external director chooses the engine and style; no paid AI API.

## Available executable tools

`scripts/kids_stage.py and motion.py` contains the implementation. `create_job` stages channel utilities under `jobs/ID/scenes/_production/` and records SHA-256 versions in `production_manifest.json`. Inspect these files before composing the storyboard. Do not claim an unsupported renderer works from a Python class alone.

`Character(name, kind="rabbit"|"turtle", scale=...)` builds profiled meshes bound to an eight-bone armature. `pose(action, seconds, at, yaw, emotion)` evaluates absolute poses. Actions: idle, walk, run, sit, jump (local 0..1 seconds), wave, look, talk, sad, joy, reach. `forest(seed)`, `lighting()`, `camera(...)`, `frame_camera(...)` provide layered woodland and wide/medium/close/tracking shots. `projected_bounds` returns actual evaluated camera bounds.

Example inside job scene:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _production.kids_stage import Character, forest, lighting, camera, frame_camera
forest(); lighting()
hero = Character("Clover", "rabbit")
hero.pose("wave", 0)
```
Build frame-change handlers driven by `(frame-1)/fps`; do not integrate velocity from the previous rendered frame. Pair expressions with body acting and listener reactions. Preserve the same cast identities and materials across shots. For prop interactions explicitly constrain hand/prop reach and contact; a reach pose alone does not prove contact.

Profiles, clothing, cheek contours, eye highlights and turtle scutes are original procedural assets. This is a rigid stylized armature, not a studio deformable rig: inspect elbow articulation, gait foot contact, silhouettes, eyes and mouth in every shot. Document defects; do not call this channel production-ready solely because meshes rendered. Never replace final cast with primitive spheres/cubes. Add custom profiles or legally licensed reviewed models when a style requires them.

Preview: scene code should accept `--still-frame=N --output=...png`. Run cached Blender with `blender -b -t 8 -P /workspace/jobs/ID/scenes/story.py -- --still-frame=70 --output=/workspace/jobs/ID/qa/preview.png`. The tested image now includes EGL/Mesa for headless Eevee. Check an actual still before choosing it; use Cycles CPU with denoising disabled as fallback. GPU access must be verified separately. Sample every shot, expression change and interaction. Inspect actual images; repair the affected mesh/action/camera, then repeat those frames.

## Workflow and approval

Plan one shared timeline for request, plan, storyboard design, code, narration and captions. Create jobs through actual MCP STDIO (`python scripts/pipeline_mcp.py create_job JSON`). Validate code and geometry before preview. Use cached Docker images, no parallel render jobs. Inspect actual preview frames, repair specific defects, then execute via MCP `execute_job`. Run `inspect_video`, inspect every evidence frame and final composed frames with captions, and submit a structured review using current `artifact_fingerprint` and `inspected_frames`. Technical passed/completed does not establish visual acceptance. Unresolved collisions, unreadable text, continuity errors, broken interactions or caption obstruction require needs_repair.

See `references/production.md` for the geometry/evidence contract and tested examples.

Shared executable preview command: `python scripts/preview_scene.py JOB_ID --frames 90 240 450 690 810`. It uses the same scene/helper staging as final Omega rendering and writes draft images/logs inside the job. Do not run it concurrently with a video render.

Call `configure_renderer(scene, samples=64)` before rendering new scenes. Compatible new jobs use `blender_device=auto`: the adapter enables the optional official GPU image only after an actual rendered-frame verification is recorded for that image ID; otherwise the tested CPU image remains available. Legacy jobs keep their existing image by default. `configure_renderer` probes/logs the selected CUDA/OptiX device, handles the Blender-version Eevee name change, and can require GPU explicitly. Do not assume CUDA passthrough alone proves rendering works. Set `blender_device=cpu` for the CPU image or `gpu` to require a verified profile.

Optional pinned upstream source examples and compatibility limits: read [references/upstream.md](references/upstream.md) when the scene needs techniques beyond the staged production helpers. These references preserve the current MCP/Docker job contract.
