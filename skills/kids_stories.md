# Kids Stories: Production Animation Guide

Video type: `kids_stories`. This guide instructs external AI Directors on creating character-driven, animated children's stories with visual continuity, age-appropriate pacing, and high emotional engagement.

---

## 1. Engine Selection Policy

- **Blender (Cycles Engine, Headless)**: Primary choice for 3D stylized character acting, environmental depth, procedural nature, and physical character interactions.
- **Three.js + Remotion**: Alternative choice for 2.5D illustrated cutout aesthetics, kinetic picture books, and camera-guided motion graphics.
- **Selection Rule**: The director selects the engine per scene based on visual requirements. Write the engine choice into `storyboard.json` and `plan.json`.

---

## 2. Structured Narrative Arc

Every story must follow a clear 5-stage beat schedule:
1. **Hook & Setting (0–20% duration)**: Introduce the main character, their peaceful status quo, and distinct personality.
2. **The Inciting Incident / Goal (20–40% duration)**: Introduce a companion in need or a clear obstacle (e.g. lost turtle needing guidance).
3. **The Journey / Escalating Obstacle (40–70% duration)**: The characters navigate a challenge together; visible emotional reactions and mutual cooperation.
4. **The Climax & Breakthrough (70–85% duration)**: Overcoming the obstacle with teamwork and kindness.
5. **Warm Resolution & Moral (85–100% duration)**: A comforting concluding image, warm smiles, and positive reinforcement.

---

## 3. Blender Headless Production Standards

### A. Rendering Configuration
Headless Blender in Docker requires Cycles on CPU with denoising disabled to avoid missing GPU/OpenGL display dependencies:
```python
import bpy

# Set Render Engine
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.use_denoising = False  # Avoid OpenImageDenoise build errors in headless containers
scene.cycles.samples = 8            # Fast, crisp sample count for animated shorts

# Resolution & Frame Rate
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 30

# Output settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'REALTIME'
```

### B. Executable Character Foundation

Read `.agents/skills/video-kids/SKILL.md`. New MCP jobs contain
`scenes/_production/kids_stage.py` and `motion.py`: original profiled meshes,
actual armature binding, named action channels, facial controls and scale-aware
camera shots. Inspect `production_manifest.json`, then customize those utilities.
Do not substitute UV spheres or cubes for final characters. The procedural cast
is a stylized rigid rig; document any remaining gait, articulation or asset-quality
limitations rather than declaring studio readiness. Use the same identity across
shots, pair facial changes with body reactions, and inspect actual frames.

### C. Environment Generation
Build vibrant storybook environments:
- **Ground**: Displaced plane with soft green grass material.
- **Sky**: Warm blue/golden gradient background with soft sun lamp (`color=(1.0, 0.95, 0.85)`, `energy=3.0`).
- **Props**: Stylized low-poly trees (brown cylinder trunks, green coned foliage) and smooth river stones.

---

## 4. Geometry & Continuity Quality Gates

Before rendering final passes:
1. **Ground Contact Check**: All characters must maintain $z \ge 0$ (no sinking beneath the ground plane).
2. **Eye-line Consistency**: Characters facing each other must have matching gaze angles (look-at vectors aligned).
3. **No Mesh Intersection**: Check bounding spheres between rabbit and turtle ($dist(c_1, c_2) \ge r_1 + r_2$).
4. **Caption Clearance**: Avoid crucial character actions in the lower 18% of the viewport ($y \le -2.0$ in camera projection).

---

## 5. Review & Repair Instructions

1. If keyframe extraction shows character clipping, adjust `camera.location` or character translation keyframes.
2. If render logs report `OpenImageDenoiser` error, confirm `bpy.context.scene.cycles.use_denoising = False`.
3. If pacing feels rushed, increase transition holds on key character emotional reactions.
