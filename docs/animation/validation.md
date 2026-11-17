# Validation and limitations

The refactor adds a reusable foundation; it does not reproduce the full upstream engines.

- Character meshes are original stylized profiles with rigid armature vertex binding, clothing, cheek/muzzle silhouettes, pupils/highlights, blink/gaze, mouth and head controls, named body actions. They are not skinned cinematic models or a foot-IK locomotion solver. Walking foot slide, joint quality and physical interactions still need shot review. Hand binding/contact distance helpers are available; a gesture alone is not a handoff.
- Three.js utilities use installed packages only: world, lights/fog, physical material and circuit shader, edge outlines, camera easing, deterministic GSAP state, flow paths, annotation overlays, crossfade utility, configurable science object assemblies. They do not claim the upstream normal/depth ink, lens blur, grade or painted asset toolkit is installed.
- Manim utilities handle layout, mathematical replacement and identity cleanup; arrays, explicit-position graph/tree diagrams, networks and emphasis. An executable lifecycle example tests actual Manim operations, not just AST validity. Original gradient-descent acceptance content must be checked separately.
- Geometry checks use actual projected sample rectangles and declared identity/contact metadata. They cannot establish occlusion inside objects, artistic appeal, universal font readability or arbitrary 3D penetration. Missing metadata is recorded as unavailable. Actual image review is mandatory.
- Technical completion is separate from `visual_acceptance`. Approval requires current artifact hashes and identified scene/composed evidence frames; scene/audio/final edits invalidate it. Render caching for new jobs checks source/helper/preset signatures instead of blindly reusing stale MP4s. Old jobs remain compatible.

No paid AI API, model downloader, frontend, publishing or cloud service was added. No reference assets were copied. The external AI remains the director.

Installed Manim presets verified from `manim.constants.QUALITIES`: `m` is 1280×720/30 fps; `h` is 1920×1080/60 fps. Preview uses `l` (854×480/15 fps). These are distinct from final visual acceptance.

Runtime checks executed (logs under kids job `309995ec/logs/`):

- Installed TypeScript compiled the original solar scene plus cinematic/object helpers without errors.
- Installed GSAP evaluated repeated/out-of-order times `[2,0,1,.5,2,0]` with exact expected linear values.
- Actual Manim dry-run exercised ReplacementTransform, TransformMatchingTex, FadeOut, VGroup, array swap/index ordering, visitation, tree and network construction.
- Original descent scene dry-run passed its shared timeline, sampled bounds and independent finite-difference/closed-form/monotonic-loss assertions.
- Blender built both actual armatures, checked rigid vertex binding, sampled all eleven named actions deterministically, and checked hand contact. Twelve walking samples measured minimum boot z ≈ 0.00443 m at unit scale (not a foot-slide or universal penetration proof).

Actual rendered preview sheets, final MP4s, composed caption frames and old/new comparisons remain the visual evidence; dry-run checks alone never grant approval.

Preview CLI: `python scripts/preview_scene.py JOB_ID --frames 90 240 450 690 810` uses existing adapters sequentially. Blender scenes implement the documented `--still-frames` contract; Manim renders a low-resolution draft into the job; Remotion captures half-scale stills and collects optional actual DOM/projected bounds from production probes. Final rendering stays behind an explicit MCP execution after image review.

Composed story review exposed two additional systemic defects and their repairs:

- Existing bright-pixel stroke/lingering-pattern heuristics flagged forest foliage as overlapping text. Their output is now explicitly advisory; actual projected geometry and external image review determine collisions. Blank/frozen/format and explicit measured collisions still gate.
- Postproduction used one dictionary entry per scene and ignored narration segment intervals. The pipeline now preserves multiple authored windows (including silence gaps), applies word timestamps at each global start, validates overlap/bounds, and reuses the existing Kokoro/caption/FFmpeg stack. A regression checks out-of-order windows, shot timing and gaps. Shorten narration that exceeds a measured window; do not truncate speech or silently desynchronize shots.

Original procedural sine/harmonic score and chime assets are generated locally by `python -m ai_video_pipeline.media.score JOB_ID warm|bright|calm`; no music samples or third-party audio were imported.

Kids job `309995ec`: final MP4 is exactly 30.0 seconds with narration/captions. All required scene/composed evidence plus the six-shot preview and matched comparison were inspected; structured MCP visual review approved this stylized demonstration with explicit rigid-rig limitations. Story narration repair reused the finished animation and completed in 19.508 seconds (measured MCP elapsed time).

Solar job `0d37f95f`: original five-stage scene and a 12-frame crossfade were inspected in half-resolution stills. Actual DOM layout now waits for measurable render layout via Remotion barriers; projected geometry uses actual mesh vertices instead of oversized world AABBs. The six inspected stills include a crossfade midpoint, and sampled layout checks pass. A failed/empty measurement never counts as passed geometry.

Math preview repair: actual images revealed an axis crossing final close-up labels and whole-string equation glyph stacking. The final scene clears the y-axis before a meaningful 2× camera close-up, keeps the x label at consistent size, reverses the highlighted trace to follow the descent direction, and checks the final dot against axes.c2p. Text replacement now uses disjoint fades; explicit token equations use TransformMatchingTex; shapes have a separate ReplacementTransform helper. Draft and final scene beats use frame-compatible durations and quantized final holds. Measured draft timeline: 30.0 seconds; derivative finite-difference error ≈7.22e-11; final point coordinate error ≈6.66e-16. No pixel statistic establishes these claims.

Math job `e42f8010`: final MCP execution completed in 48.002 seconds, with 30.0-second narration/caption composition. All required scene/composed frames were inspected after preview repairs. The provided baseline `b81c622d` is **binary search**, not gradient descent. Its matched 16-second frame visibly stacks status labels. The comparison supports layout/collision-handling and composition observations; it is not a controlled same-topic comparison of educational content or artistic quality. No scores or parity claims are made.
