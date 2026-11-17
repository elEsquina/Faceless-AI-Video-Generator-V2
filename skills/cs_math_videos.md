# CS & Math Videos: Production Animation Guide

Video type: `cs_math_educational`. This guide instructs external AI Directors on building mathematically rigorous, visually intuitive animations using **Manim (Community Edition)**.

---

## 1. Engine Selection Policy

- **Manim (Community Edition)**: Primary engine for computer science algorithms, mathematical derivations, calculus, linear algebra, graph theory, and coordinate geometry.
- **Three.js + Remotion**: Secondary engine when rich real-time UI/software mockups or web dashboard interactions are required.

---

## 2. Educational Pacing & Structural Arc

Structure mathematical explanations into a 4-part progression:
1. **Geometric/Intuitive Hook (0–20% duration)**: State the core objective with a compelling visual metaphor (e.g. finding the lowest valley in a fog-covered mountain).
2. **Mathematical Formulation (20–45% duration)**: Present clean LaTeX formulas, highlighting variables with distinct color accents (e.g. $w_{t+1} = w_t - \eta \nabla L(w_t)$).
3. **Dynamic Step-by-Step Visualization (45–80% duration)**: Step through iterations, showing tangent vectors, gradient descent arrows, and decreasing loss values.
4. **Intuition & Takeaway (80–100% duration)**: Summarize convergence behavior, showing how learning rate $\eta$ influences the path.

---

## 3. Manim Animation Standards & Tested Patterns

### A. 3D Surface & Gradient Descent Pattern
```python
from manim import *
import numpy as np

class GradientDescentScene(ThreeDScene):
    def construct(self):
        # Camera orientation
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        
        # 3D Axes
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[0, 8, 2],
            x_length=6,
            y_length=6,
            z_length=4,
        ).shift(DOWN * 0.5)
        
        # Loss surface L(w1, w2) = w1^2 + w2^2
        surface = Surface(
            lambda u, v: axes.c2p(u, v, u**2 + v**2),
            u_range=[-2.5, 2.5],
            v_range=[-2.5, 2.5],
            resolution=(24, 24),
            should_make_jagged=False,
        )
        surface.set_style(fill_opacity=0.6, fill_color=BLUE_E, stroke_color=BLUE_B, stroke_width=0.8)
        
        self.play(Create(axes), Create(surface), run_time=1.5)
        
        # Descent Steps
        w = np.array([2.0, 2.0])
        eta = 0.25
        dot = Sphere(radius=0.15, color=YELLOW).move_to(axes.c2p(w[0], w[1], w[0]**2 + w[1]**2))
        self.play(FadeIn(dot))
        
        for step in range(4):
            grad = 2 * w
            w_next = w - eta * grad
            next_pos = axes.c2p(w_next[0], w_next[1], w_next[0]**2 + w_next[1]**2)
            arrow = Arrow3D(
                start=axes.c2p(w[0], w[1], w[0]**2 + w[1]**2),
                end=next_pos,
                color=RED,
                thickness=0.03,
            )
            self.play(Create(arrow), dot.animate.move_to(next_pos), run_time=0.8)
            w = w_next
        self.wait(1.0)
```

### B. Safe Text Replacement & Lifecycle Management
- **Never morph across varying text strings**: Do not call `Transform(label_a, label_b)` when string contents or lengths differ. This produces jumbled spline vertices.
- **Always use explicit transitions**:
  ```python
  self.play(FadeOut(old_text), run_time=0.2)
  self.play(FadeIn(new_text), run_time=0.2)
  ```
- **Loop cleanup**: In loops updating counters or step numbers, ensure the previous mobject is removed or faded out before introducing the next.
- **Vertical Zoning**:
  - Keep main mathematical diagrams and formulas in $y \in [-1.6, 3.2]$.
  - Reserve $y \le -2.0$ strictly for captions.

---

## 4. Visual QA & Verification
1. Verify all LaTeX equations compile without parse errors.
2. Verify coordinate axes align with visual labels.
3. Check intermediate frames at 25%, 50%, and 75% for text collisions.
4. Verify scene output duration matches target duration within 0.05 seconds.

## Executable layout and lifecycle foundation

Read `.agents/skills/video-cs-math/SKILL.md` and staged `_production/math_stage.py`.
Use `replace_text` (disjoint text fades), `replace_object` (ReplacementTransform for shapes), or `replace_equation`
(TransformMatchingTex) and keep the returned identity. Related objects belong
in VGroups and `clear_group` handles FadeOut/removal. The library also provides
arrays, explicit-position graphs/trees, neural networks, fit/layout and camera-aware
projected bounds. Verify equations and numeric trajectories independently from
visual review; render and inspect transition midpoints, not just title cards.
