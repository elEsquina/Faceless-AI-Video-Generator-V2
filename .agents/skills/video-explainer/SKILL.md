---
name: video-explainer
description: Generate visual explanatory videos with frame-based Three.js/Remotion and iterative frame QA.
---

# Video Explainer Generation Skill

Generate cinematic explanatory videos with Three.js, GSAP, and Remotion.

## Guidelines
1. Read `AGENTS.md` and `skills/explanatory_videos.md` before planning.
2. Structure content across 5 phases (Hook, Mechanism, Flow, System, Summary).
3. In Remotion / Three.js TSX:
   - Always drive GSAP timelines deterministically with `timeline.seek(frame / fps)`.
   - Export components as `MainScene` or `default`.
   - Target 1280x720, 30 fps.
   - Maintain clear typography and reserve the bottom 18% for burned captions.
4. Execute via MCP tools:
   - `create_job` -> write `plan.json`, `audio_plan.json`, and `.tsx` scene files -> `validate_plan` -> `execute_job` -> `inspect_video`.
5. Verify smooth camera motions, high-contrast labels, and audio synchronization.
