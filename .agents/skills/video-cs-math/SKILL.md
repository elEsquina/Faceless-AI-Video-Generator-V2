---
name: video-cs-math
description: Generate mathematically rigorous, visually intuitive CS/math educational videos with Manim and frame QA.
---

# Video CS & Math Generation Skill

Generate educational animations using Manim Community Edition.

## Guidelines
1. Read `AGENTS.md` and `skills/cs_math_videos.md` before planning.
2. Structure animations into 4 progressive parts: Geometric Intuition -> Formal Mathematical Equation -> Dynamic Iterations / Descent -> Summary.
3. In Manim scripts:
   - Target 1280x720, 30 fps (`-ql` or `-qh`).
   - Use explicit `FadeOut` / `FadeIn` for text changes; never morph text with `Transform`.
   - Maintain vertical zoning: diagrams in $y \ge -1.6$, reserve $y \le -2.0$ for burned captions.
4. Execute via MCP tools:
   - `create_job` -> write `plan.json`, `audio_plan.json`, and `.py` scene files -> `validate_plan` -> `execute_job` -> `inspect_video`.
5. Verify mathematical precision, readable LaTeX typography, and synchronized voiceover.
