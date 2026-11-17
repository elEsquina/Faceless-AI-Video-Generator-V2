---
name: video-kids
description: Generate kid-friendly animated stories with structured beats, Blender/Remotion engine selection, and scene QA.
---

# Video Kids Generation Skill

Generate production-quality animated kids' stories using Blender or Three.js + Remotion.

## Guidelines
1. Read `AGENTS.md` and `skills/kids_stories.md` before planning.
2. Structure the story across 5 distinct beats (Hook, Goal, Journey, Climax, Resolution).
3. In Blender scripts:
   - Use `CYCLES` CPU engine with `scene.cycles.use_denoising = False`.
   - Set 1280x720, 30 fps, H.264 format.
   - Position characters with ground contact ($z \ge 0$) and safe caption margins.
4. Execute via MCP tools:
   - `create_job` -> write `plan.json`, `audio_plan.json`, and scenes -> `validate_plan` -> `execute_job` -> `inspect_video`.
5. Maximize emotional warmth, clear character actions, and supportive dialogue.
