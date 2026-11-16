# Kids Stories: Agent Generation Guide

Video type: `kids_stories`. Optimize for clarity, age-appropriate plots, safe themes, visible character reactions and consistent character identities. Do not infer a mandatory engine from the type.

## Director decision
- Prefer Blender/Python for fully 3D acting when a **licensed, locally installed** rig/asset and renderer exist.
- Prefer Three.js + Remotion for illustrated 2.5D stories, camera glides, and stylized billboards.
- Roblox-specific characters, emotes, hairstyles and sets are NOT part of this skill. The upstream NoCodeHack engine requires its own assets and Roblox Studio MCP setup; do not claim they are available.
- Select an engine per scene based on available tools and asset budget; write the decision and fallback into `plan.json`.

## Story-to-animation contract
Plan a clear hook, goal, escalating obstacle, emotional turn and resolution. Generate structured scene beats with `scene_id`, `start_s`, `duration_s`, `setting`, `cast`, `action`, `reaction`, `camera`, `narration`, `sfx`, and `asset_refs`. Each speaking character should trigger a listener reaction when helpful. Every scene needs purposeful motion, but do not add rapid cuts merely to fill time. Maintain location, scale, costume, eye-line and lighting continuity.

## Blender-style structured route (adapted from nocodehack)
1. Write a versioned `story.json`/job plan; inspect the actual Blender adapter capabilities before emitting animation instructions.
2. Lint the story for missing props, undeclared cast, impossible/overlapping times, bad frame bounds and unknown action types.
3. Perform **geometry gates** on each constructed scene before video render: feet-ground contact, object-hand contact, object collision, camera framing, gaze/face visibility, and character path intersection. Require an explicit PASS/FAIL report; only call it PASS after running an implemented check.
4. Render low-cost draft frames/contact sheet; review entrance, prop visibility, reaction framing, emotional peak and shot variation.
5. Repair only failed scenes. Repeat validation after every repair. Render preview, then final only with user permission.
6. Mix voice/SFX/music after picture timing is locked; caption policy follows the user's settings, not the upstream default.

## Three.js/Remotion-style route (adapted from mromidev)
Use scene timeline / frame-indexed camera keys / separate world, characters and post layers. Keep characters original and reference visuals for style study only. For each major beat generate still frames, compare against a written style brief, fix occlusion/silhouettes, then render. Scale pixel-space effects with export resolution. Never hard-code source-specific bridge characters or lighting as global requirements.

## Failure checks
No missing limbs/rigs, no camera through walls, no speech without matching action, no floating feet or hand-prop gaps, no text beyond safe bounds, no disconnected cuts, and no unlicensed character assets. Record quality gates as requested/implemented/not-available rather than inventing results.
