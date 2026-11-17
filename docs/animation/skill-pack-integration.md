# Skill integration pack review

The user-provided `skill_integration_pack.zip` contained an installer and two instruction documents, not animation assets. The useful source references have been integrated into the existing three channel skills; the original installer was not executed. Its unpinned bulk-copy behavior and standalone renderer assumptions were unsuitable for the current working pipeline.

## What was retained

| Channel | Source collection | Local entrypoint | Integration |
|---|---|---|---|
| Kids | EL4CTEO/blender-skills, MIT | [Blender references](../../.agents/skills/video-kids/references/upstream.md) | Nine selected topics plus their asset-QA dependency; scripts, helper copies, docs and license |
| CS/math | awesome-skills/manim-skill, MIT | [Manim references](../../.agents/skills/video-cs-math/references/upstream.md) | Craft references, runnable examples and inspection utilities; gallery/media omitted |
| Explainer | Hmzbo/animation-skills OSS Three.js subtree, MIT | [Three.js references](../../.agents/skills/video-explainer/references/upstream.md) | Geometry/lighting examples, API/troubleshooting references and archived standalone tools |

Exact commits, source paths and the original ZIP checksum are recorded in [the manifest](skill-pack-manifest.json). Each collection has `SOURCE.json` containing SHA-256 hashes for every imported file and retains its MIT license. All **89 imported files** matched their recorded hashes; **52 Python files and 4 JavaScript modules** passed syntax checks.

Existing channel `SKILL.md` files now link to the appropriate optional catalog. Archived upstream instruction files are named `UPSTREAM_SKILL.md` so they do not become competing automatically discovered skills. The channel catalogs explain what to read, what actually ran, and how to adapt code to job-local paths. No production Python scaffold, MCP schema/tool, renderer, Docker image, dependency or GPU configuration was changed for this installation.

The pack's Claude Animated Shorts and Roblox Engine references were already inspected and adapted during the preceding production refactor, so duplicate repositories were not installed. No Roblox catalog assets, style-reference imagery, video galleries, or separately licensed GSAP/Remotion skill buckets were imported. The three original rendered deliveries remain unchanged.

## Actual validation and limits

Verification artifacts are in `video_docker_sandbox/workspace/jobs/7c231c5a/qa/skill_pack/`.

- **Blender 4.0.2 and 4.5.16:** upstream `env_report` and nonfix `rig_check` ran against the existing eight-bone original cast. The valid rig passed, and a deliberately removed vertex weight was rejected. The root-origin warning remains reported; this is not an export-readiness claim.
- **Blender 4.5.16:** `shapekeys` created 15 viseme keys and correctly reported every key as unsculpted. It does not manufacture finished facial poses or lip synchronization. The 4.0 CPU image lacks NumPy, so this tool is explicitly blocked there; no dependency was installed.
- **Blender 5.x:** the upstream collection targets 5.2+/5.3. Other operations, profiles and new APIs remain unverified. Catalogs require capability checks and adaptation rather than a silent image upgrade.
- **ManimCE 0.22.1:** the upstream `MotionTiming` example rendered successfully with the existing Docker adapter environment at 854×480/15 fps. [Actual sampled frames](../../video_docker_sandbox/workspace/jobs/7c231c5a/qa/skill_pack/manim_timing_frames.jpg) were viewed: two distinct speed curves and equal-time marks are readable at three intermediate points. This is an attributed upstream example used for compatibility checking, not a new original delivery video. Optional Typst and the separate inspection utility's dependencies are not established as installed.
- **Three.js r175:** both imported examples were evaluated with real Three.js geometry/cameras and a stub renderer. Repeated out-of-order times produced identical state hashes, and different times changed the state. No pixel-level, cross-machine or standalone Playwright-driver success is claimed. Production continues through the existing Remotion adapter.
- The three active skills passed the skill validator. The complete pipeline regression suite passed **56 tests** with the existing environment warning. Raw results are in the verification job.

The obsolete installer ZIP was removed after the useful sources, licenses, routes and provenance were retained. Future source updates require inspecting a new pinned revision and rerunning relevant compatibility checks; do not run an unreviewed bulk update over local skills.
