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

### B. Procedural Stylized Character Creation
When external rigs are not bundled, generate charming procedural geometric characters:
- **Rabbit Archetype**: Rounded body sphere, head sphere, long ears with forward tilt, pink nose, hopping translation with vertical sine-bounce and ear flop rotations.
- **Turtle Archetype**: Flattened olive-green shell hemisphere, round head with gentle bobbing, 4 stubby flippers/legs moving alternately.

```python
def create_rabbit(name="Rabbit", location=(0, 0, 0)):
    # Body
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(location[0], location[1], location[2] + 0.7))
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    
    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(location[0], location[1] + 0.3, location[2] + 1.5))
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    
    # Ears
    for side in (-0.2, 0.2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.7, location=(location[0] + side, location[1] + 0.3, location[2] + 2.0))
        ear = bpy.context.active_object
        ear.rotation_euler = (0.2, side * 0.4, 0)
        ear.name = f"{name}_Ear_{'L' if side < 0 else 'R'}"
```

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
