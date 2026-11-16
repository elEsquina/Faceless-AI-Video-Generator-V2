# Generation Skill: General Explanatory Videos

This guide outlines rules, design language, and code generation standards for general concept, science, business, and tech explanatory videos.

---

## 1. Domain Profile

- **Target Audience**: General public, professionals, students.
- **Tone**: Professional, engaging, articulate, informative, and crisp.
- **Narrative Arc**:
  1. *Hook* (10%): Surprising question, relatable dilemma, or compelling statistic.
  2. *Core Concept Definition* (25%): The foundational idea broken down simply.
  3. *Mechanism / Walkthrough* (45%): How it works step-by-step with visual metaphors.
  4. *Real-world Impact / Application* (15%): Why it matters today.
  5. *Call-to-Action / Conclusion* (5%): Concise memorable wrap-up.

---

## 2. Recommended Engine Selection

- **Primary**: **Three.js + GSAP + Remotion (React/TSX)** for modern web motion graphics, isometric 3D illustrations, UI concept animations, and kinetic typography.

---

## 3. Script & Audio Pacing

- **Narration Speed**: Moderate to brisk (approx. 140–165 words per minute).
- **Voice Style**: Confident, conversational, authoritative, and energetic.
- **Sound Effects (SFX)**: Subtle, modern UI sounds (digital clicks, smooth whooshes, soft pops, camera shutter clicks).
- **Background Music (BGM)**: Modern lo-fi, electronic ambient, or subtle corporate indie music ducked by -16dB during speech.

---

## 4. Shared Timeline Guidelines

- Synchronize motion graphics transitions with narration keywords.
- Text splash / captions should highlight 1–3 key terms per phrase rather than dense sentences.
- Maintain consistent visual pacing: one main concept or visual transformation per 5–10 second block.

---

## 5. Animation Code Scaffold (Remotion / TSX Example)

When generating Remotion components in `scenes/scene_XX/Scene.tsx`:

```tsx
import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export const ExplainerScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const cardY = interpolate(frame, [0, 20], [50, 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ flex: 1, backgroundColor: '#0f172a', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ opacity, transform: `translateY(${cardY}px)`, color: '#ffffff', fontSize: 48, fontWeight: 700 }}>
        Visual Concept Card
      </div>
    </div>
  );
};
```
