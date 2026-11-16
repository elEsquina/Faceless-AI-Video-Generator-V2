# Generation Skill: Kids' Animated Stories

This guide outlines rules, narrative patterns, and code generation standards for children's animated videos.

---

## 1. Domain Profile

- **Target Audience**: Ages 4–10.
- **Tone**: Playful, vibrant, warm, emotionally expressive, and clear.
- **Narrative Arc**:
  1. *Introduction* (15%): Introduce main character, world, and goal.
  2. *Adventure / Complication* (50%): A humorous challenge, obstacle, or journey.
  3. *Climax / Discovery* (20%): Solving the problem with kindness, creativity, or teamwork.
  4. *Resolution / Moral* (15%): Warm ending with a takeaway lesson.

---

## 2. Recommended Engine Selection

- **Primary**: **Blender Python API (`bpy`)** for stylized 3D low-poly or claymation-style character scenes.
- **Alternative**: **Three.js + Remotion** for 2D/2.5D storybook illustration scenes with paper cutout animations.

---

## 3. Script & Audio Pacing

- **Narration Speed**: Slow to moderate (approx. 110–130 words per minute).
- **Voice Style**: Friendly, warm, expressive, with distinct character inflections.
- **Sound Effects (SFX)**: Frequent and cartoonish (whoosh, boing, pop, magic chime, footstep pitter-patter).
- **Background Music (BGM)**: Gentle acoustic instruments (ukulele, xylophone, soft piano, light percussion), ducked by -14dB during voiceover.

---

## 4. Shared Timeline Guidelines

- Keep scenes short (4 to 8 seconds each) to maintain young viewers' engagement.
- Place visual action and key sound effects within the first 0.5s of a scene transition.
- Large, high-contrast, rounded subtitle text with playful bouncy animations.

---

## 5. Animation Code Scaffold (Blender Example)

When generating Blender code in `scenes/scene_XX/scene.py`:

```python
import bpy
import math

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 150  # 5 seconds at 30 fps

def build_environment():
    # Setup camera, light, and stylized colorful backdrop
    pass

def animate_character():
    # Stylized bouncy movement keyframed across frame_start to frame_end
    pass

if __name__ == "__main__":
    setup_scene()
    build_environment()
    animate_character()
```
