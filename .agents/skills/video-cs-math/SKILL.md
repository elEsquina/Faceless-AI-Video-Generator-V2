---
name: video-cs-math
description: Readable rigorous Manim with executable production utilities and evidence-based frame QA.
---

Activate for readable rigorous manim. Read `prompt.md` and exactly the current job's `skills/cs_math_videos.md`. The external director chooses the engine and style; no paid AI API.

## Available executable tools

`scripts/math_stage.py` contains the implementation. `create_job` stages channel utilities under `jobs/ID/scenes/_production/` and records SHA-256 versions in `production_manifest.json`. Inspect these files before composing the storyboard. Do not claim an unsupported renderer works from a Python class alone.

Import `fit`, `heading`, `replace_text`, `replace_object`, `replace_equation`, `clear_group`, `array`, `swap_cells`, `visit_indices`, `graph`, `network`, `emphasize`, `descent` and `bounds` from staged `_production.math_stage`. Write original Manim Scene/MovingCameraScene classes using these building blocks. Explicit graph positions support trees/DAGs; `array` supports active indices, `swap_cells` updates logical order and visual positions, and `visit_indices` animates an independently computed traversal; `network` provides grouped edges/nodes; ValueTracker + always_redraw drive dynamic plots.

```python
label = replace_text(self, label, Text("Iteration 2"), run_time=.3)
equation = replace_equation(self, equation, MathTex(r"x_{k+1}=(1-2\eta)x_k"))
clear_group(self, VGroup(diagram, label))
```
Text replacement uses disjoint fades; `replace_object` uses ReplacementTransform for shapes, the second TransformMatchingTex for explicit matching tokens (or disjoint FadeOut/FadeIn for whole strings), and cleanup FadeOut. Keep returned identities; group related labels/shapes with VGroup, remove old objects and clear updaters before disposal. Do not re-add old labels after replacement. Keep diagrams above y=-2, equation boxes within the current camera, text >=22 pixels at final output, and reserve bottom 18% for captions. Use large purposeful diagrams and a few motivated camera moves. No tiny graph in a mostly empty screen.

Verify mathematical claims independently: derive formulas, compute numerical iterations/residuals, check units and graph positions against the actual function. `descent` only models L(x)=x² with 0<eta<1; do not claim arbitrary losses are convex. For camera movement record `bounds(obj, self.camera.frame)` at layout checkpoints.

Preview through cached Manim `-ql --disable_caching --media_dir /manim/jobs/ID/qa/preview scenes/...py SceneClass`; inspect rendered video keyframes including transition midpoints. Final uses job `render_settings.json` with `{"manim_quality":"m"}` for 1280x720/30 fps (adapter validates presets). Repair label layout and lifecycle before another render.

## Workflow and approval

Plan one shared timeline for request, plan, storyboard design, code, narration and captions. Create jobs through actual MCP STDIO (`python scripts/pipeline_mcp.py create_job JSON`). Validate code and geometry before preview. Use cached Docker images, no parallel render jobs. Inspect actual preview frames, repair specific defects, then execute via MCP `execute_job`. Run `inspect_video`, inspect every evidence frame and final composed frames with captions, and submit a structured review using current `artifact_fingerprint` and `inspected_frames`. Technical passed/completed does not establish visual acceptance. Unresolved collisions, unreadable text, continuity errors, broken interactions or caption obstruction require needs_repair.

See `references/production.md` for the geometry/evidence contract and tested examples.

Executable example: `scripts/lifecycle_example.py` exercises replacements, grouped cleanup, an animated logical array swap, visitation, a tree and a network. Stage it beside `_production` and run Manim `LifecycleExample`; do not use it as acceptance video content.

Shared executable preview command: `python scripts/preview_scene.py JOB_ID --frames 90 240 450 690 810`. It uses the same scene/helper staging as final Omega rendering and writes draft images/logs inside the job. Do not run it concurrently with a video render.

Equation safety: tokenize corresponding MathTex terms when matching them. `replace_equation` falls back to disjoint fades for unmatched whole strings to avoid stacking old/new glyphs. For camera close-ups, clear axes that would run behind overlay text, retain the coordinate mapping, and measure the final point against axes.c2p independently.

Optional pinned upstream source examples and compatibility limits: read [references/upstream.md](references/upstream.md) when the scene needs techniques beyond the staged production helpers. These references preserve the current MCP/Docker job contract.
