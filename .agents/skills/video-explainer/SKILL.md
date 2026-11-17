---
name: video-explainer
description: Cinematic deterministic explainers with executable production utilities and evidence-based frame QA.
---

Activate for cinematic deterministic explainers. Read `prompt.md` and exactly the current job's `skills/explanatory_videos.md`. The external director chooses the engine and style; no paid AI API.

## Available executable tools

`scripts/cinematic.tsx` and `scripts/models.tsx` contain the implementations. `create_job` stages channel utilities under `jobs/ID/scenes/_production/` and records SHA-256 versions in `production_manifest.json`. Inspect these files before composing the storyboard. Do not claim an unsupported renderer works from a Python class alone.

`models.tsx` supplies customizable panel assemblies, exploded cell layers, particle wires, converter enclosures and houses. Use `World`, `Lights`, `Camera`, `physical`, `Outline`, `Flow`, `Label`, `Chapter`, `Dissolve`, `circuitMaterial` and `timelineAt` from the staged `_production/cinematic` module. They use the installed Three.js/Fiber/Remotion/GSAP packages. No postprocessing dependency is assumed. Lighting, fog, keyed camera targets, emissive process particles and object-edge outlines establish hierarchy; customize them for the requested style.

```tsx
import {timelineAt, Camera} from './_production/cinematic';
const state=timelineAt(()=>({amount:0}), (tl,s)=>{
  tl.to(s,{amount:1,duration:2,ease:'power2.inOut'},0);
}, frame/fps);
```
Fresh state, a paused timeline, absolute seek and `kill()` prevent random-order Remotion rendering from depending on a browser ticker. Set every mutable property from the frame. No Date.now, unseeded randomness, useFrame delta integration, requestAnimationFrame or autoplay timelines. Export the scene as default. Build meaningful processes (paths, flow, layers, internal structure), not generic cubes under text. Fit label bounds in safe zones; decorative outline is not a text legibility fix.

Preview: stage the scene and its `_production` folder into the existing Remotion entry, then use `npx remotion still src/index.tsx MainScene /workspace/jobs/ID/qa/frame.png --frame=N --scale=.5 --browser-executable=/usr/bin/chromium`. Inspect all camera shots, annotation changes and transition midpoints. Compare repeated frame hashes when evaluating deterministic animation. Final rendering uses the existing Omega adapter with concurrency one. Repair paths, view targets, lighting or annotation placement individually.

## Workflow and approval

Plan one shared timeline for request, plan, storyboard design, code, narration and captions. Create jobs through actual MCP STDIO (`python scripts/pipeline_mcp.py create_job JSON`). Validate code and geometry before preview. Use cached Docker images, no parallel render jobs. Inspect actual preview frames, repair specific defects, then execute via MCP `execute_job`. Run `inspect_video`, inspect every evidence frame and final composed frames with captions, and submit a structured review using current `artifact_fingerprint` and `inspected_frames`. Technical passed/completed does not establish visual acceptance. Unresolved collisions, unreadable text, continuity errors, broken interactions or caption obstruction require needs_repair.

See `references/production.md` for the geometry/evidence contract and tested examples.

Shared executable preview command: `python scripts/preview_scene.py JOB_ID --frames 90 240 450 690 810`. It uses the same scene/helper staging as final Omega rendering and writes draft images/logs inside the job. Do not run it concurrently with a video render.

For measured layout evidence use `LayoutProbe` beneath an AbsoluteFill with `data-qa-root="true"`, and `ProjectionProbe` in World. Enable only via input props `collectLayout`; DOM labels and named `qa_subject*` objects emit normalized actual bounds into preview logs. The preview CLI collects these into `qa/layout_scene_001.json`.

Optional pinned upstream source examples and compatibility limits: read [references/upstream.md](references/upstream.md) when the scene needs techniques beyond the staged production helpers. These references preserve the current MCP/Docker job contract.
