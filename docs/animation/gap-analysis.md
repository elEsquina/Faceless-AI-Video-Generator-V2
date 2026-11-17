# Production foundation gap analysis (before implementation)

Source inspection: repositories cloned into `/tmp/faceless-refs/` on 2026-11-17.

| Source implementation inspected | Technique | Current local gap / proposed change |
|---|---|---|
| claude-animated-shorts `templates/bridge/{Bridge,world,story}.tsx/ts` | One persistent world, absolute-frame posing, shot timeline, render barriers | Skills offer only `seek(frame/fps)`; add deterministic world/camera/material/timeline components and job-local staging |
| `templates/bridge/{lights,shade,ink,paint,lensblur,cast}.ts` | Coordinated daylight/golden palettes, custom shading, outlines before depth blur, pooled expressive cards, sight-line-aware environments | No production library; add original lighting/material/outline/atmosphere helpers using installed packages only; do not imply unsupported postprocessing packages are installed |
| `templates/audio/timeline.py`, `templates/scripts/{bridge-stills.mjs,short_qa.py,sbs_sheet.py}` | Frame-aligned audio, sampled stills, measured technical QA plus human comparisons | Keep existing Kokoro/mix/captions; add preview evidence and comparison workflow, never equate statistics with artistic quality |
| nocodehack-roblox-engine `engine/{rig,locomotion,anims,faces,acting}.py` | Reusable articulated hierarchy, action channels, facial states and listener/body reactions | Local guide explicitly prescribes UV-sphere animals; replace with original profiled meshes, reusable skeletal pivots and facial controls; no Roblox assets imported |
| `engine/{story,build,camera,staging,interact}.py`, `tools/story_lint.py`, example `stories/dragon_in_the_park/story.json` | Structured cast/beats/shots, character-relative framing, interaction constraints, lint before preview and repair | Add structured action and camera utilities; inspect projections before final rendering; keep one shared timeline |
| Local `quality/validator.py` and QA models | Technical report can say passed without any agent review; cached review has no artifact binding | Separate technical result from visual acceptance; bind evidence to content hashes, reject stale approval, require all scene evidence plus final composed frames |
| Local Manim guide | Text fades and fixed zones only; no layout/lifecycle/diagram code | Add fit/layout, safe replacements, equations, graph/tree/network/array/plot primitives; independently check descent math |

Both upstreams were inspected at source level. Claude Animated Shorts is MIT; Roblox Engine code is Apache-2.0 with NOTICE and separate asset restrictions. This implementation uses original code and procedural assets. No upstream assets, reference frames, Roblox meshes/decals, or implementations are redistributed. See source-specific licensing files in the temporary clones. No claim of parity with either reference is made.

Preserve MCP tool names, job schema compatibility, parsers, Compose, Kokoro, captions, FFmpeg and sequential jobs. The renderer class in `media/renderer.py` is a scaffold; actual execution is `parsers/omega.py`. Rendering must be demonstrated through MCP STDIO and actual Docker commands, not inferred from classes.

Pinned sources: Claude `e3b817b6afc6cd413466d43f11ba31209e034bbf`, Roblox Engine `ebbdbcf08cd761dad6db28662b3fced99b7dea14`. Additional inspection included `engine/space.py` exact triangle/BVH body gates and `build.py` penetration, visibility, jump-cut gates and tiered resume rendering. These sophisticated collision planners are not reproduced by simple projected AABBs; local geometry checks must state their sampled/projected scope.

Runtime evidence: cached Blender 4.0.2 renders Cycles CPU. An Eevee preview failed because `libEGL.so.1` was absent. User explicitly authorized installing EGL/Mesa libraries after measured Cycles cost (~7 seconds/final frame). User also requested GPU repair after the refactor/tests; WSL/Docker GPU diagnosis is tracked separately, preserving the no-Windows-change constraint.
