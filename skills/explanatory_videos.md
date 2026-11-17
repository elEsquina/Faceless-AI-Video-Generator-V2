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
import React from 'react';
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { gsap } from 'gsap';

export const ExplainerScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Create paused timeline driven by exact frame time
  const timeline = gsap.timeline({ paused: true });
  const state = { cameraZ: 6, rotationY: 0, electronFlow: 0, textOpacity: 0 };

  timeline.to(state, { cameraZ: 3.5, textOpacity: 1, duration: 1.5, ease: 'power2.out' }, 0);
  timeline.to(state, { rotationY: Math.PI * 0.5, electronFlow: 1, duration: 2.5, ease: 'sine.inOut' }, 1.0);

  // Seek timeline to current timestamp
  timeline.seek(frame / fps);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0f1d' }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, state.cameraZ], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[4, 6, 5]} intensity={2.2} />
        <mesh rotation={[0.2, state.rotationY, 0]}>
          <boxGeometry args={[2, 1.2, 0.2]} />
          <meshStandardMaterial color="#2563eb" roughness={0.3} metalness={0.8} />
        </mesh>
      </ThreeCanvas>
      {/* 2D Overlay / Callout typography */}
      <div style={{
        position: 'absolute',
        top: 60,
        left: 80,
        opacity: state.textOpacity,
        color: '#f8fafc',
        fontFamily: 'sans-serif',
      }}>
        <h2 style={{ fontSize: 44, color: '#38bdf8', margin: 0 }}>Photovoltaic Cell</h2>
        <p style={{ fontSize: 22, color: '#94a3b8', maxWidth: 450 }}>Silicon P-N junction absorbing solar photons</p>
      </div>
    </AbsoluteFill>
  );
};
export default ExplainerScene;
```

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
