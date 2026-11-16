# Explanatory Videos: Agent Generation Guide

Video type: `explanatory_videos`. User supplies topic, format and audience; the director selects the engine automatically from installed toolchains. Default candidates: Three.js + GSAP + Remotion for camera-driven 3D explanations and kinetic typography; Manim for math-heavy segments; Blender for physical object animations.

## Story and scene plan
1. Research/verify factual claims when the task requires it; retain references in the job plan. Avoid invented statistics.
2. Use a hook -> visual mechanism -> worked example -> consequence -> recap arc. Narration should explain what the image cannot already communicate.
3. Write a scene/shot schedule with start/end time, word cue, specific visible change, camera parameters, captions and effect events. All modalities use one shared timeline.
4. Provide a simple original style brief: palette, composition, font hierarchy, depth, shadow, outline, transition and scene-to-scene continuity.

## Three.js+Remotion recipe (adapted from claude-animated-shorts)
- Separate: `story` (frame and shot timing), `world` (geometry/props), `cast` (illustrated billboard or true 3D entities), `camera` (position/look-at/FOV), `post` (outline/DOF/bloom/grade), `audio` (cues).
- Prefer deterministic frame-indexed animation. If using GSAP for previews, drive its timeline from a deterministic frame clock during rendering; do not allow uncontrolled wall-clock animation inside Remotion.
- Associate visual reactions/transitions with word-alignment markers; re-time after real TTS word durations are obtained.
- Create a first/center/last still for each shot and a contact sheet for the whole video. Inspect readability, clipping, depth, ink/outline behavior, and subject focus.
- Treat source repo's exact bridge look/color values as an optional reference style, not a hard requirement; do not copy its proprietary reference imagery.
- Keep post-processing in a known order, verify render at intended resolution; check temporary disk capacity before large Remotion bundles.

## Review loop
Static checks (TypeScript compile, asset paths, finite coordinates) -> low-res stills -> visual QA with concrete frame-numbered defects -> edit only failing scene -> rerun checks -> preview -> final video with FFmpeg A/V QA. Require evidence for PASS; provide a short missing-capability report if no toolchain exists.

## Cost controls
Reuse scene code and original local assets, batch stills, avoid rendering full video until story and camera are approved, regenerate only changed scenes, prefer offline sound synthesis/local TTS where installed. Video engine choice is determined by requirement, not hardcoded by category.
