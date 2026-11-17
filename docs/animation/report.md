# Animation production foundation — implementation and evidence

This refactor supplies executable production tools to future MCP jobs and demonstrates them in three original videos. The external coding agent remains the director; no paid LLM API was introduced. Improvements are demonstrated against local outputs, not asserted as parity with upstream productions.

## Architecture and executable tools

- `create_job` stages versioned channel utilities under `scenes/_production/`, with SHA-256 provenance in `production_manifest.json`. Updated routing guides require the director to inspect them before original storyboarding/code. New Manim jobs default to the verified 1280×720/30-fps preset; legacy jobs retain their defaults.
- Kids: `.agents/skills/video-kids/scripts/{kids_stage,motion}.py` builds original profiled character meshes bound to actual eight-bone armatures. Eleven deterministic action channels, eyes/blinks/gaze, mouth/head controls, expression/body poses, forest construction, lighting, scale-aware framing, measured hand/prop contact and projected bounds are available.
- Explainer: `.agents/skills/video-explainer/scripts/{cinematic,models}.tsx` provides world/lighting/fog, eased cameras, materials/shader, outlines, deterministic paused GSAP evaluation, charge-flow paths, labels, dissolves/crossfades, detailed panel/cell/inverter/home assemblies and actual DOM/mesh-vertex evidence probes. It uses installed packages only.
- CS/math: `.agents/skills/video-cs-math/scripts/math_stage.py` provides fit/layout, frame-quantized disjoint text fades, token-aware equation matching, ReplacementTransform for shapes, grouped cleanup, arrays/swaps/visitation, explicit-position graphs/trees, networks, emphasis and numerical descent. `lifecycle_example.py` verifies real Manim identity/lifecycle and logical array ordering.
- `scripts/preview_scene.py` uses the existing engine adapters; Remotion previews reuse a browser and capture real geometry. `scripts/pipeline_mcp.py` calls the actual local MCP STDIO transport. Final generation and review submissions used MCP calls.
- New jobs cache renders by scene/helper/preset signatures. Audio-only recovery reuses completed visuals. Parser Theta/postproduction now honor multiple narration windows, silence gaps and global caption offsets rather than collapsing them into one entry per scene.
- Quality reports distinguish technical status from evidence-bound visual acceptance. Approval requires current artifact hashes and all scene/composed evidence frames. Projected bounds gate collisions, framing, caption clearance, text size and occupancy; optional metadata covers identity, expressions, style, contacts and planned cuts. Pixel-density/lingering-pattern results are advisory, not artistic judgments. Frozen-motion exceptions require explicit static intent; aspect ratios are checked numerically.

The eleven registered MCP tools, job schema compatibility, Omega/Theta, Kokoro, captions, FFmpeg and Compose services remain. `core/skills.py` and `media/renderer.py` scaffolds were not presented as functioning renderers; actual execution is through Omega's Docker adapters. The user authorized EGL/Mesa libraries after a measured slow/noisy Cycles fallback; those libraries enable tested headless Eevee. Windows was not modified, and nothing was pushed.

## References and licenses

Both repositories were cloned and inspected at source level before production changes; see [gap analysis](gap-analysis.md).

| Reference | Pinned revision | License / use |
|---|---|---|
| [Claude Animated Shorts](https://github.com/mromidev/claude-animated-shorts) | `e3b817b6afc6cd413466d43f11ba31209e034bbf` | MIT; architecture/workflow inspected, no implementation/assets redistributed |
| [NoCodeHack Roblox Engine](https://github.com/nocodehack/nocodehack-roblox-engine) | `ebbdbcf08cd761dad6db28662b3fced99b7dea14` | Apache-2.0 plus NOTICE and separate asset restrictions; no Roblox meshes/decals/assets imported |

Character profiles, materials, environments, science models/shader and audio scores/chimes are original procedural project contributions. No separately licensed third-party character, animation, texture or music asset was imported. Existing renderer/TTS/font dependencies retain their own licenses; no new Python/npm dependency was installed.

## Videos and comparisons

Each final file contains narration, burned captions, original background score and a sound cue. Jobs are sequential. Every video has an authored 30-second shot/beat timeline; the single engine scene in each test contains multiple compositions or camera shots.

| Channel | New job / MP4 | Matched before/after sheet |
|---|---|---|
| Kids — rabbit helps a lost turtle | [309995ec final.mp4](../../video_docker_sandbox/workspace/jobs/309995ec/output/final.mp4) | [6c88d036 → 309995ec](../../video_docker_sandbox/workspace/jobs/309995ec/qa/comparison/before_after.jpg) |
| Solar-panel explainer | [0d37f95f final.mp4](../../video_docker_sandbox/workspace/jobs/0d37f95f/output/final.mp4) | [f474cb30 → 0d37f95f](../../video_docker_sandbox/workspace/jobs/0d37f95f/qa/comparison/before_after.jpg) |
| Gradient descent | [e42f8010 final.mp4](../../video_docker_sandbox/workspace/jobs/e42f8010/output/final.mp4) | [b81c622d → e42f8010](../../video_docker_sandbox/workspace/jobs/e42f8010/qa/comparison/before_after.jpg) |

Sampling is at matched 3/8/16/23/27-second timestamps, stated in each sheet's metadata. The supplied CS baseline is binary search, not gradient descent: compare layout, collisions, composition and camera use, not controlled same-topic educational quality.

## Visual review findings

- Kids: primitive sphere silhouettes became recognizable clothed, expressive cast with consistent identities, articulated actions, layered woodland and six camera shots. Actual previews exposed cropped ears/feet and an incorrectly scaled turtle close-up; repairs went into the shared camera utility. Composed caption frames were inspected after narration was retimed to the shots. The provided old output visibly clips primitive characters and lacks facial/environment detail.
- Solar: the prior dark slab/boxes/cylinder became a cell-grid panel, exploded semiconductor, charge separation/circuit flow, inverter waveform and lit home. Actual previews exposed photons over headings, a circuit entering the caption band, an edge-clipped annotation and a malformed roof; those were repaired. Conventional current is explicitly distinguished from electron motion. Crossfade midpoint and final composed captions were inspected.
- Math: the provided old 16-second frame visibly stacks status labels. New labels have explicit lifecycles; the quadratic, derivative, five iterations and loss values are readable, followed by a meaningful close-up. Preview review caught glyph stacking and a y-axis crossing close-up text; safe fades and axis cleanup fixed them. Numerical verification independently checks derivative finite differences, closed-form iterates, decreasing loss and final dot coordinates. The convergence condition is stated specifically for L(x)=x².

Review records and inspected frame paths live in each job's `qa/quality_report.json` and `qa/visual_review.json`. These are external-agent judgments of actual sampled images, not automatic artistic scores. See [validation details](validation.md).

## Measurements and limitations

- Kids: final 900-frame CPU Eevee render measured 953.47 seconds (~1.06 seconds/frame). The earlier discarded Cycles pass sampled ~7 seconds/frame. Audio-only repair took 19.508 seconds through MCP and reused the completed animation.
- Solar: the first MCP attempt took 90.296 seconds including a completed render and rejected overlong narration; audio-only recovery took 29.290 seconds. The final semantic scene repair, QA and cached-audio composition took 86.279 seconds.
- Math: final render/narration/caption composition completed in 48.002 seconds through MCP. Draft timeline measured 30.0 seconds; derivative error ~7.22e-11 and final dot coordinate error ~6.66e-16. Final numeric/media checks are in the job QA artifacts.

The character foundation is a usable stylized rigid rig, not a studio deformable asset library: elbow/knee deformation, foot IK and phoneme-level lip synchronization are not implemented. Sampled ground/contact checks are not universal penetration or foot-slide proofs. The full upstream depth/normal ink, lens blur, grading and painted-asset systems were not ported. Artistic parity and studio asset readiness remain unproven and are not claimed. Geometry is sampled/projected; meaningful external frame inspection remains necessary. The baseline comparison for CS is not topic-controlled.

Final regression, media verification, acceptance and GPU verification results follow.

## Acceptance and regression result

The complete suite passed: **56 tests, 1 existing environment deprecation warning, 7.72 seconds**. This includes the existing MCP STDIO/tool-discovery tests and new production staging, deterministic actions, geometry, continuity/contact, stale-review rejection, evidence/defect rejection, scene-cache isolation, narration-window/gap/offset and frozen/aspect checks. Real engine runtime checks supplement the unit suite; the three final jobs exercised actual Docker rendering, local Kokoro, captions and FFmpeg through MCP.

All three final artifacts passed technical QA and external sampled-frame review. MP4 stream verification is saved in `jobs/e42f8010/qa/final_media_verification.json`; per-job raw FFprobe data, visual review and quality reports remain alongside the MP4s.

| Requested criterion | Result |
|---|---|
| Both references inspected at source level; gaps documented before production edits | Complete |
| All three skills contain executable utilities and meaningful references | Complete |
| Blender has usable characters/actions/environment/cameras | Complete for the demonstrated rigid stylized rig; studio deformation/IK/asset parity remains incomplete |
| Three.js cinematic, deterministic animation and composition foundation | Complete for tested installed dependencies; full upstream postprocessing parity not claimed |
| Manim mathematical/lifecycle/layout utilities and working examples | Complete |
| New jobs automatically receive/version the production foundation; director workflow uses it | Complete; original test scenes import those staged libraries |
| Three original 30-second narrated/captioned composed videos rendered through MCP | Complete |
| Actual rendered previews/composed frames inspected and repaired | Complete |
| Old/new comparisons with concrete observations, no invented scores | Complete; CS baseline is a different topic |
| Existing regression suite passes; no paid AI API | Complete |

The GPU follow-up below is separate from these completed CPU-fallback video demonstrations.

## GPU follow-up: CUDA rendering verified and integrated

The RTX 5050 Laptop GPU was healthy in WSL. The initial sandbox NVML error did not establish a host GPU failure. Two actual blockers were found: Docker lacked NVIDIA Container Toolkit, and the cached Blender 4.0.2 build did not expose this GPU as a supported Cycles device.

After the user ran `scripts/setup_gpu_wsl.sh` with local sudo authentication, Docker registered NVIDIA Container Toolkit 1.20.2. The installer follows [NVIDIA's official installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), preserves configuration backups, and does not change Windows or install a Linux display driver. Actual PTX JIT CUDA kernels wrote 42 in both WSL and Docker; evidence is in `jobs/e42f8010/qa/{wsl,docker}_gpu_kernel_check.json`. The utility reports version 610.51; the queried running driver is 610.71.

The optional `docker/blender-gpu.Dockerfile` installs SHA-256-verified official Blender 4.5.16 LTS in a separate image, preserving the legacy CPU image. CUDA Cycles and GPU denoising rendered three original 1280×720, 32-sample character frames successfully. The initial measured run took 1.49–1.64 seconds/frame; replay through `scripts/verify_blender_gpu.py e42f8010` took 1.53–1.79 seconds/frame. This is not a controlled speed comparison with the older Eevee animation. [Rendered proof](../../video_docker_sandbox/workspace/jobs/e42f8010/qa/gpu_oidn/gpu_frame_72.png), [raw measurements](../../video_docker_sandbox/workspace/jobs/e42f8010/qa/gpu_oidn/result.json) and verification logs remain in the job. OptiX was tested and unavailable; CUDA is the verified backend.

New kids jobs receive `blender_device: auto`. Omega and preview rendering use the optional GPU Compose override only when the locally verified profile matches the exact installed image ID and Docker has NVIDIA runtime support. The staged renderer helper selects actual CUDA devices and GPU denoising. Legacy jobs retain CPU defaults. `FACELESS_GPU=cpu` explicitly selects CPU; `blender_device: gpu` requires a verified profile and fails clearly if unavailable. For future compatible scenes, call the staged `configure_renderer` helper rather than hardcoding an old Eevee API or CPU device.

Actual MCP diagnostic job **7c231c5a** used its automatically created settings and logged `CUDA`, `GPU`, and `NVIDIA GeForce RTX 5050 Laptop GPU`. Its 60-frame, 640×360, two-second animation completed through MCP in **22.805 seconds** including startup/composition. The scene required a GPU, so a CPU fallback would have failed. See [MCP diagnostic video](../../video_docker_sandbox/workspace/jobs/7c231c5a/output/final.mp4), its renderer log and `qa/media_verification.json`. This short silent diagnostic is additional to the three narrated delivery videos.

The GPU repair is complete for the verified Blender CUDA path. The three delivery videos above remain CPU-rendered artifacts; they were not relabeled as GPU renders. Manim/Cairo, the current software-WebGL Remotion configuration and the installed CPU PyTorch/Kokoro image remain CPU workloads. Docker passthrough alone does not accelerate those engines.

## Subsequent skill-pack integration

The optional upstream source collections from the user-provided integration pack were reviewed and incorporated into the existing skills with MIT notices, pinned commits, file hashes and compatibility gates. This subsequent installation vendors selected licensed source code; the original two reference engines and their assets remain unvendored. See [integration review and runtime checks](skill-pack-integration.md). Existing production code and the three delivery videos were preserved.
