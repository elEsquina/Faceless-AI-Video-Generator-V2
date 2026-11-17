# Explanatory Videos: Production Animation Guide

Video type: `explanatory_videos`. This guide instructs external AI Directors on building cinematic, 3D motion-graphic explanatory videos using **Three.js, GSAP, and Remotion**.

---

## 1. Engine Selection Policy

- **Three.js + GSAP + Remotion**: Primary engine for technological, scientific, and business explanations. Delivers smooth camera moves, dynamic 3D meshes, particle simulations, and synchronized typography.
- **Manim**: Use for dedicated mathematical derivations or algorithm steps embedded in the explainer.
- **Blender**: Use for complex physical simulations or realistic photorealistic renders.

---

## 2. Five-Stage Storytelling Arc

Every explanatory video should structure its narrative into 5 clear phases:
1. **The Hook (0–15% duration)**: The core mystery or real-world problem (e.g. "How does sunlight turn into electricity in your home?").
2. **The Microscopic / Core Mechanism (15–45% duration)**: Zooming into the functional unit (e.g. silicon wafers, photon impact, electron dislodgement).
3. **The Circuit / Process Flow (45–70% duration)**: Demonstrating macroscopic energy flow (e.g. P-N junction electric field, direct current to inverter).
4. **The Real-World System (70–85% duration)**: Integration into daily life (e.g. AC electricity powering homes and storing in batteries).
5. **The Summary & Takeaway (85–100% duration)**: A unified visual recapitulating the clean energy cycle.

---

## 3. Three.js + Remotion Production Architecture

### A. Frame-Deterministic GSAP Animation
Remotion relies on headless Chromium frame captures. Never allow wall-clock or free-running GSAP timelines. Always lock timelines to Remotion's frame clock:

```tsx
import {timelineAt} from './_production/cinematic';
const state = timelineAt(() => ({cameraZ: 6, flow: 0}), (tl, s) => {
  tl.to(s, {cameraZ: 4, flow: 1, duration: 2, ease: 'sine.inOut'}, 0);
}, frame / fps);
```

Read `.agents/skills/video-explainer/SKILL.md` and the staged `cinematic.tsx`
and `models.tsx` before scene authoring. The actual implementations provide
world/lighting/camera, material/shader, edge-outline, particle-path, annotation,
transition and detailed object-assembly helpers using installed dependencies.
Customize a meaningful process and composition; empty scenes with boxes and text
are placeholders unless the user explicitly requests that style.


### B. Composition & Camera Design
- Use cinematic lighting with warm primary lights (`#ffedd5`) and cool rim/ambient fills (`#1e293b`).
- Apply depth and smooth focal transitions with Three.js camera position interpolations.
- Always reserve the bottom 18% ($y \ge 590\text{px}$ in 720p) for subtitle overlay tracks.

---

## 4. Visual QA & Frame Review

1. **Resolution & Aspect**: Verify 1280x720 (16:9) framing.
2. **Text Readability**: Ensure high contrast against 3D backgrounds (use background scrims or dropshadows where necessary).
3. **Motion Smoothness**: Ensure rotation and camera velocities do not exceed 90 degrees/sec to avoid strobing.
4. **Keyframe Audit**: Inspect frames at $t = 0\%$, $25\%$, $50\%$, $75\%$, and $100\%$ of each scene.
