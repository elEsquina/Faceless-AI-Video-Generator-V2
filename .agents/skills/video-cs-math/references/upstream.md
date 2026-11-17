# Optional Manim craft sources

For continuous representation changes, camera-led explanations, timing, algorithm item identity or richer mathematical choreography, consult the pinned MIT [Manim collection](upstream/manim/UPSTREAM_SKILL.md). Read only the relevant topic rather than loading every example. Preserve its [LICENSE](upstream/manim/LICENSE) with adapted code; commit and file hashes are in [SOURCE.json](upstream/manim/SOURCE.json).

Useful entrypoints:

- [Animation recipes](upstream/manim/references/animation-recipes.md): shared time, motion mappings, continuous state, item transfers and visual anchors.
- [Visual direction](upstream/manim/references/visual-direction.md) and [aesthetic refinement](upstream/manim/references/aesthetic-refinement.md): focal composition and preview repair.
- [Advanced techniques](upstream/manim/references/advanced.md): camera and updater patterns.
- `examples/motion_timing.py`, `local_linearity.py`, `merge_step.py`, `circle_to_wave.py` are concrete starting points. Adapt them to the requested subject; do not present an upstream example as original generated content.

Upstream targets ManimCE 0.22.x; the installed Docker image reports **0.22.1**. The imported `MotionTiming` example actually rendered at the installed low-quality 854×480/15-fps preset; three intermediate frames were inspected for readable labels and equal-time marks. This validates that example, not every example or optional backend. Typst is optional and not established as installed. The video-inspection utility requires PyAV/Pillow; verify those before choosing it, or use the existing pipeline frame extractor.

The archived upstream standalone CLI and setup notes are references. Keep the current Pydantic/MCP job contract, staged `math_stage.py`, shared narration timeline, caption clearance, Docker adapter and evidence-bound QA. Copy adapted code with attribution into `jobs/ID/scenes/`; write all preview/output files in that job. No npm/Python installation or renderer replacement is implied.

Evidence: `video_docker_sandbox/workspace/jobs/7c231c5a/qa/skill_pack/manim_render.log`, `manim_timing_frames.jpg`, and `manim_media/videos/motion_timing/480p15/MotionTiming.mp4`.
